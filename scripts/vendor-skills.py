#!/usr/bin/env python3
"""Verify, restore, refresh, or approved-remove pinned skill snapshots and metadata.

Vendor operations hold one advisory `flock` on the repository root, stage a full
copy of `vendor/`, and publish it with atomic no-replace renames. A crashed run
leaves at most one staging directory (cleaned by the next operation) or a
`.vendor-old` tree that the next operation restores or discards.
"""

from __future__ import annotations

import argparse
import ctypes
import errno
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import unicodedata
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, NoReturn

ROOT = Path(__file__).resolve().parent.parent
VENDOR_DIR = ROOT / "vendor"
LOCK_PATH = VENDOR_DIR / "skills.lock.json"
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
TRACK_RE = re.compile(r"^(?:[0-9a-f]{40}|refs/[A-Za-z0-9._*/-]+)$")
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
GITHUB_OWNER = r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
GITHUB_REPOSITORY = r"[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?"
SOURCE_RE = re.compile(rf"^https://github\.com/{GITHUB_OWNER}/{GITHUB_REPOSITORY}\.git$")
LOCK_VERSION = 2
SNAPSHOT_HASH_FORMAT = "sha256-framed-v3"
STAGING_PREFIX = ".vendor-staging-"
VENDOR_STAGING_NAME_RE = re.compile(r"^\.vendor-staging-[0-9a-f]{24}$")
VENDOR_STAGING_MARKER = ".sdlc-vendor-staging"
VENDOR_STAGING_MARKER_CONTENT = b"sdlc-vendor-staging-v1\n"
VENDOR_OLD_NAME = ".vendor-old"
INSTALLED_METADATA_NAME = ".sdlc-vendor"
DIRECTORY_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def read_utf8_text(path: Path, label: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        fail(f"invalid {label}: {error}")


def run(*args: str, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=cwd,
            check=False,
            text=True,
            capture_output=True,
        )
    except OSError as error:
        fail(f"could not run {args[0]}: {error}")
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        fail(f"command failed: {' '.join(args)}\n{detail}")
    return result.stdout.strip()


def rename_noreplace_primitive() -> tuple[Any, int]:
    libc = ctypes.CDLL(None, use_errno=True)
    if hasattr(libc, "renameat2"):
        rename = libc.renameat2
        flag = 1  # RENAME_NOREPLACE
    elif hasattr(libc, "renameatx_np"):
        rename = libc.renameatx_np
        flag = 0x00000004  # macOS RENAME_EXCLUSIVE
    else:
        fail("vendor publication requires renameat2 or renameatx_np")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    return rename, flag


def atomic_rename_noreplace(
    source_parent_fd: int,
    source: str,
    destination_parent_fd: int,
    destination: str,
) -> bool:
    """Atomically rename source to destination; False when the destination exists."""
    rename, flag = rename_noreplace_primitive()
    result = rename(
        source_parent_fd,
        os.fsencode(source),
        destination_parent_fd,
        os.fsencode(destination),
        flag,
    )
    if result == 0:
        return True
    error_number = ctypes.get_errno()
    if error_number == errno.EEXIST:
        return False
    raise OSError(error_number, os.strerror(error_number), destination)


def parse_json_unique(text: str, label: str) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                fail(f"{label} contains duplicate key: {key}")
            result[key] = value
        return result

    try:
        return json.loads(text, object_pairs_hook=reject_duplicates)
    except json.JSONDecodeError as error:
        fail(f"invalid {label}: {error}")


def validate_track(name: str, track: str) -> None:
    if (
        not TRACK_RE.fullmatch(track)
        or ".." in track
        or "//" in track
        or "@{" in track
        or track.endswith((".", "/"))
    ):
        fail(f"{name}: track must be a safe full commit or refs/ pattern")


def validate_lock_data(data: Any, allow_unpinned: bool = False) -> dict[str, Any]:
    allowed_top_level = {"version", "snapshotHash", "skills"}
    if not isinstance(data, dict):
        fail("provenance lock must be an object")
    unknown_top_level = sorted(set(data) - allowed_top_level)
    if unknown_top_level:
        fail(f"provenance lock has unknown fields: {', '.join(unknown_top_level)}")
    if (
        set(data) != allowed_top_level
        or type(data.get("version")) is not int
        or data.get("version") != LOCK_VERSION
        or data.get("snapshotHash") != SNAPSHOT_HASH_FORMAT
        or not isinstance(data.get("skills"), dict)
    ):
        fail(f"provenance lock must use version {LOCK_VERSION}, {SNAPSHOT_HASH_FORMAT}, and a skills object")
    required = {
        "source",
        "track",
        "commit",
        "upstreamPath",
        "contentSha256",
        "licenseSource",
        "licenseSha256",
    }
    for name, entry in data["skills"].items():
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            fail(f"invalid skill name in provenance lock: {name}")
        if not isinstance(entry, dict):
            fail(f"invalid provenance entry: {name}")
        missing = sorted(required - entry.keys())
        if missing:
            fail(f"{name}: missing provenance fields: {', '.join(missing)}")
        unknown = sorted(entry.keys() - required)
        if unknown:
            fail(f"{name}: unknown provenance fields: {', '.join(unknown)}")
        for field in required:
            if not isinstance(entry[field], str):
                fail(f"{name}: {field} must be a string")
            if any(unicodedata.category(character) == "Cc" for character in entry[field]):
                fail(f"{name}: {field} must not contain control characters")
        if not SOURCE_RE.fullmatch(entry["source"]):
            fail(f"{name}: source must be an HTTPS GitHub .git URL")
        validate_track(name, entry["track"])
        for field in ("upstreamPath", "licenseSource"):
            value = Path(entry[field])
            raw_parts = entry[field].split("/")
            if value.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
                fail(f"{name}: {field} must be a safe repository-relative path")
        if allow_unpinned:
            if entry["commit"] and not COMMIT_RE.fullmatch(entry["commit"]):
                fail(f"{name}: commit must be empty or a full SHA")
        elif not COMMIT_RE.fullmatch(entry["commit"]):
            fail(f"{name}: commit must be a full SHA")
        for field in ("contentSha256", "licenseSha256"):
            if allow_unpinned:
                if entry[field] and not HASH_RE.fullmatch(entry[field]):
                    fail(f"{name}: {field} must be empty or a SHA-256 digest")
            elif not HASH_RE.fullmatch(entry[field]):
                fail(f"{name}: {field} must be a SHA-256 digest")
    return data


def load_lock_path(path: Path, label: str, allow_unpinned: bool = False) -> dict[str, Any]:
    require_regular_file(path, label)
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        fail(f"invalid {label}: {error}")
    return validate_lock_data(parse_json_unique(text, label), allow_unpinned=allow_unpinned)


def load_lock(allow_unpinned: bool = False) -> dict[str, Any]:
    return load_lock_path(LOCK_PATH, "provenance lock", allow_unpinned=allow_unpinned)


def validate_snapshot_entries(directory: Path, allow_installed_metadata: bool = False) -> None:
    if directory.is_symlink():
        fail(f"snapshot root must be a real directory: {directory}")
    root = directory.resolve()
    for path in directory.rglob("*"):
        relative = path.relative_to(directory)
        if relative.parts[0] == INSTALLED_METADATA_NAME and not allow_installed_metadata:
            fail(f"snapshot uses reserved installed metadata namespace: {path}")
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raw_target = os.readlink(path)
            if Path(raw_target).is_absolute():
                fail(f"snapshot symlink must be relative: {path} -> {raw_target}")
            target = (path.parent / raw_target).resolve(strict=False)
            try:
                relative_target = target.relative_to(root)
            except ValueError:
                fail(f"snapshot symlink escapes its skill root: {path} -> {raw_target}")
            if relative_target.parts and relative_target.parts[0] == INSTALLED_METADATA_NAME:
                fail(f"snapshot symlink targets reserved installed metadata: {path} -> {raw_target}")
        elif not stat.S_ISDIR(mode) and not stat.S_ISREG(mode):
            fail(f"snapshot contains unsupported file type: {path}")


def hash_field(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def hash_file_field(digest: Any, path: Path) -> None:
    size = path.stat().st_size
    digest.update(size.to_bytes(8, "big"))
    remaining = size
    with path.open("rb") as source:
        while remaining:
            chunk = source.read(min(1024 * 1024, remaining))
            if not chunk:
                fail(f"file changed while hashing: {path}")
            digest.update(chunk)
            remaining -= len(chunk)
        if source.read(1):
            fail(f"file changed while hashing: {path}")


def snapshot_hash(directory: Path, exclude_installed_metadata: bool = False) -> str:
    digest = hashlib.sha256(b"sdlc-snapshot-v3\0")
    if not directory.is_dir():
        fail(f"missing skill snapshot: {directory}")
    validate_snapshot_entries(directory, allow_installed_metadata=exclude_installed_metadata)
    for path in sorted(directory.rglob("*"), key=lambda item: item.relative_to(directory).as_posix()):
        relative_path = path.relative_to(directory)
        if exclude_installed_metadata and relative_path.parts[0] == INSTALLED_METADATA_NAME:
            continue
        if path.is_symlink():
            hash_field(digest, b"link")
            hash_field(digest, relative_path.as_posix().encode())
            hash_field(digest, os.readlink(path).encode())
            continue
        if path.is_dir():
            hash_field(digest, b"dir")
            hash_field(digest, relative_path.as_posix().encode())
            continue
        hash_field(digest, b"file")
        hash_field(digest, relative_path.as_posix().encode())
        executable = b"1" if stat.S_IMODE(path.stat().st_mode) & 0o111 else b"0"
        hash_field(digest, executable)
        hash_file_field(digest, path)
    return digest.hexdigest()


def require_real_directory(path: Path, label: str) -> None:
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        fail(f"missing or unreadable {label}: {path} ({error})")
    if path.is_symlink() or not stat.S_ISDIR(mode):
        fail(f"{label} must be a real directory: {path}")


def require_regular_file(path: Path, label: str) -> None:
    try:
        mode = path.lstat().st_mode
    except OSError as error:
        fail(f"missing or unreadable {label}: {path} ({error})")
    if path.is_symlink() or not stat.S_ISREG(mode):
        fail(f"{label} must be a regular file: {path}")


def validate_vendor_container(vendor_dir: Path) -> None:
    for path, label in (
        (vendor_dir, "vendor root"),
        (vendor_dir / "skills", "skills directory"),
        (vendor_dir / "licenses", "licenses directory"),
        (vendor_dir / "provenance", "provenance directory"),
    ):
        require_real_directory(path, label)
    for path in (vendor_dir / "skills").iterdir():
        require_real_directory(path, "skill snapshot")
    for path in (vendor_dir / "licenses").iterdir():
        require_regular_file(path, "vendored license")
    for path in (vendor_dir / "provenance").iterdir():
        require_regular_file(path, "vendored provenance")


def file_hash(path: Path) -> str:
    require_regular_file(path, "license")
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def lock_text(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2) + "\n"


def provenance_text(name: str, entry: dict[str, Any]) -> str:
    provenance = {
        "version": 1,
        "skill": name,
        "source": entry["source"],
        "commit": entry["commit"],
        "upstreamPath": entry["upstreamPath"],
        "snapshotHash": SNAPSHOT_HASH_FORMAT,
        "contentSha256": entry["contentSha256"],
        "licenseSource": entry["licenseSource"],
        "licenseSha256": entry["licenseSha256"],
    }
    return json.dumps(provenance, indent=2) + "\n"


def verify(data: dict[str, Any], vendor_dir: Path = VENDOR_DIR) -> None:
    validate_lock_data(data)
    validate_vendor_container(vendor_dir)
    skills_dir = vendor_dir / "skills"
    licenses_dir = vendor_dir / "licenses"
    provenance_dir = vendor_dir / "provenance"
    expected = set(data["skills"])
    actual = {path.name for path in skills_dir.iterdir()}
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        parts = []
        if missing:
            parts.append(f"missing: {', '.join(missing)}")
        if extra:
            parts.append(f"unexpected: {', '.join(extra)}")
        fail("vendored skill directory mismatch (" + "; ".join(parts) + ")")

    expected_licenses = {f"{name}.txt" for name in expected}
    expected_provenance = {f"{name}.json" for name in expected}
    if {path.name for path in licenses_dir.iterdir()} != expected_licenses:
        fail("vendored license inventory differs from the skill lock")
    if {path.name for path in provenance_dir.iterdir()} != expected_provenance:
        fail("vendored provenance inventory differs from the skill lock")

    for name, entry in data["skills"].items():
        if snapshot_hash(skills_dir / name) != entry["contentSha256"]:
            fail(f"{name}: snapshot hash differs from provenance lock")
        if file_hash(licenses_dir / f"{name}.txt") != entry["licenseSha256"]:
            fail(f"{name}: license hash differs from provenance lock")
        provenance_file = provenance_dir / f"{name}.json"
        require_regular_file(provenance_file, "vendored provenance")
        if read_utf8_text(provenance_file, "vendored provenance") != provenance_text(name, entry):
            fail(f"{name}: generated provenance differs from the skill lock")


def verify_installed_modes(skill_dir: Path) -> None:
    for path in (skill_dir, *skill_dir.rglob("*")):
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            continue
        if stat.S_ISDIR(mode):
            expected = 0o755
        elif stat.S_ISREG(mode):
            expected = 0o755 if stat.S_IMODE(mode) & 0o111 else 0o644
        else:
            fail(f"installed skill contains unsupported file type: {path}")
        actual = stat.S_IMODE(mode)
        if actual != expected:
            fail(f"installed skill mode is {oct(actual)}, expected {oct(expected)}: {path}")


def verify_installed(data: dict[str, Any], skills_dir: Path) -> None:
    require_real_directory(skills_dir, "installed skills directory")
    for name, entry in data["skills"].items():
        skill_dir = skills_dir / name
        metadata_dir = skill_dir / INSTALLED_METADATA_NAME
        provenance_file = metadata_dir / "provenance.json"
        license_file = metadata_dir / "LICENSE.txt"
        require_real_directory(skill_dir, "installed skill")
        require_real_directory(metadata_dir, "installed metadata directory")
        verify_installed_modes(skill_dir)
        if {path.name for path in metadata_dir.iterdir()} != {"provenance.json", "LICENSE.txt"}:
            fail(f"{name}: installed metadata inventory is invalid")
        require_regular_file(provenance_file, "installed provenance")
        require_regular_file(license_file, "installed license")
        if read_utf8_text(provenance_file, "installed provenance") != provenance_text(name, entry):
            fail(f"{name}: installed provenance differs from the skill lock")
        if snapshot_hash(skill_dir, exclude_installed_metadata=True) != entry["contentSha256"]:
            fail(f"{name}: installed content differs from the skill lock")
        if file_hash(license_file) != entry["licenseSha256"]:
            fail(f"{name}: installed license differs from the skill lock")


def resolve_commit(source: str, track: str) -> str:
    if COMMIT_RE.fullmatch(track):
        return track

    def query(pattern: str) -> list[tuple[str, str]]:
        output = run("git", "ls-remote", source, pattern)
        return [
            (fields[1], fields[0])
            for line in output.splitlines()
            if len(fields := line.split()) == 2
        ]

    direct = [sha for ref, sha in query(track) if ref == track]
    # Annotated tags expose the tag object on the ref itself; the peeled ref carries the commit.
    peeled = [sha for ref, sha in query(f"{track}^{{}}") if ref == f"{track}^{{}}"]
    if len(peeled) == 1 and COMMIT_RE.fullmatch(peeled[0]):
        return peeled[0]
    if len(direct) == 1 and COMMIT_RE.fullmatch(direct[0]):
        return direct[0]
    fail(f"could not resolve one commit for {source} {track}")


def reject_gitlinks(repository: Path) -> None:
    gitlinks = []
    for line in run("git", "ls-files", "--stage", cwd=repository).splitlines():
        fields = line.split(maxsplit=3)
        if fields and fields[0] == "160000":
            gitlinks.append(fields[3].split("\t", 1)[-1] if len(fields) == 4 else "unknown")
    if gitlinks:
        fail(f"Git submodules are unsupported: {', '.join(gitlinks)}")


def checkout(source: str, commit: str, destination: Path) -> None:
    destination.mkdir(parents=True)
    run("git", "init", "--quiet", cwd=destination)
    run("git", "config", "core.autocrlf", "false", cwd=destination)
    run("git", "config", "core.eol", "lf", cwd=destination)
    run("git", "remote", "add", "origin", source, cwd=destination)
    run("git", "fetch", "--quiet", "--depth=1", "origin", commit, cwd=destination)
    run("git", "checkout", "--quiet", "--detach", "FETCH_HEAD", cwd=destination)
    actual = run("git", "rev-parse", "HEAD", cwd=destination)
    if actual != commit:
        fail(f"fetched {actual}, expected {commit}")
    reject_gitlinks(destination)


def safe_repo_path(repository: Path, value: str, field: str) -> Path:
    relative = Path(value)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        fail(f"unsafe {field} in provenance lock: {value}")
    resolved = (repository / relative).resolve()
    try:
        resolved.relative_to(repository.resolve())
    except ValueError:
        fail(f"unsafe {field} in provenance lock: {value}")
    return resolved


def path_lexists(path: Path) -> bool:
    return path.exists() or path.is_symlink()


def fsync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError as error:
        fail(f"could not open directory for durability sync: {directory} ({error})")
    try:
        os.fsync(descriptor)
    except OSError as error:
        fail(f"could not sync directory: {directory} ({error})")
    finally:
        os.close(descriptor)


def fsync_regular_file(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        fail(f"could not open file for durability sync: {path} ({error})")
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            fail(f"durability sync requires a regular file: {path}")
        os.fsync(descriptor)
    except OSError as error:
        fail(f"could not sync file: {path} ({error})")
    finally:
        os.close(descriptor)


def fsync_tree(directory: Path) -> None:
    require_real_directory(directory, "tree to sync")
    directories = [directory]
    for path in directory.rglob("*"):
        mode = path.lstat().st_mode
        if stat.S_ISREG(mode):
            fsync_regular_file(path)
        elif stat.S_ISDIR(mode):
            directories.append(path)
        elif not stat.S_ISLNK(mode):
            fail(f"tree to sync contains unsupported file type: {path}")
    for path in sorted(directories, key=lambda item: len(item.parts), reverse=True):
        fsync_directory(path)


def rename_durable(source: Path, destination: Path) -> None:
    source_parent = source.parent
    destination_parent = destination.parent
    source.rename(destination)
    fsync_directory(source_parent)
    if destination_parent != source_parent:
        fsync_directory(destination_parent)


def unlink_durable(path: Path, missing_ok: bool = False) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        if missing_ok:
            return
        raise
    fsync_directory(path.parent)


def remove_path(path: Path, missing_ok: bool = False) -> None:
    try:
        if not path_lexists(path):
            if missing_ok:
                return
            fail(f"could not remove missing path: {path}")
        if path.is_symlink():
            path.unlink()
        else:
            shutil.rmtree(path)
        fsync_directory(path.parent)
    except OSError as error:
        fail(f"could not remove {path}: {error}")


@contextmanager
def vendor_operation_lock(root: Path = ROOT) -> Iterator[int]:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(root, flags)
    except OSError as error:
        fail(f"could not open repository directory for vendor operation lock: {error}")
    acquired = False
    try:
        if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
            fail(f"vendor operation lock requires a real repository directory: {root}")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fail("another vendor operation is running")
        acquired = True
        yield descriptor
    finally:
        if acquired:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def write_marker_file(marker: Path, content: bytes) -> None:
    descriptor = os.open(
        marker,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        remaining = memoryview(content)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                fail("write returned no bytes")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    fsync_directory(marker.parent)


def mark_vendor_staging(staging: Path) -> None:
    write_marker_file(staging / VENDOR_STAGING_MARKER, VENDOR_STAGING_MARKER_CONTENT)


def cleanup_stale_vendor_state(root: Path = ROOT) -> None:
    """Next-run cleanup: restore or discard crashed publication and staging state."""
    old = root / VENDOR_OLD_NAME
    vendor = root / "vendor"
    if path_lexists(old):
        require_real_directory(old, "interrupted vendor publication backup")
        if not path_lexists(vendor):
            rename_durable(old, vendor)
            print("restored interrupted vendor publication", file=sys.stderr)
        else:
            data = load_lock_path(vendor / "skills.lock.json", "published provenance lock")
            verify(data, vendor)
            remove_path(old)
    for entry in sorted(root.glob(f"{STAGING_PREFIX}*")):
        marker = entry / VENDOR_STAGING_MARKER
        if not path_lexists(marker) or not marker.is_file():
            try:
                entry.rmdir()
            except OSError:
                print(
                    f"warning: leaving unmarked directory {entry.name} alone; inspect and remove it manually",
                    file=sys.stderr,
                )
            else:
                fsync_directory(root)
            continue
        try:
            content = marker.read_bytes()
        except OSError:
            content = b""
        if content != VENDOR_STAGING_MARKER_CONTENT:
            try:
                entry.rmdir()
            except OSError:
                print(f"warning: unrecognized staging marker in {entry.name}; leaving it alone", file=sys.stderr)
            else:
                fsync_directory(root)
            continue
        remove_path(entry)


def publish_vendor_tree(next_vendor: Path, data: dict[str, Any], serialized_lock: str) -> None:
    """Swap the staged vendor tree into place, atomically and durably.

    Crash windows are recovered by `cleanup_stale_vendor_state`: between the two
    renames the old tree sits at `.vendor-old` and `vendor/` is absent, so the
    next operation restores it; after the second rename the published tree is
    already the verified new one and only the discard of `.vendor-old` remains.
    """
    fsync_tree(next_vendor)
    old = ROOT / VENDOR_OLD_NAME
    if path_lexists(old):
        fail("cannot publish while a previous vendor publication is mid-swap")
    root_fd = os.open(ROOT, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0))
    try:
        if not atomic_rename_noreplace(root_fd, VENDOR_DIR.name, root_fd, VENDOR_OLD_NAME):
            fail("cannot publish: unexpected existing .vendor-old directory")
        try:
            staging_fd = os.open(
                next_vendor.parent,
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
            )
            try:
                if not atomic_rename_noreplace(staging_fd, "vendor", root_fd, "vendor"):
                    fail("vendor publication raced with an unexpected destination")
            finally:
                os.close(staging_fd)
        except OSError:
            if not path_lexists(VENDOR_DIR):
                rename_durable(old, VENDOR_DIR)
            raise
    finally:
        os.close(root_fd)
    fsync_directory(ROOT)
    published_text = read_utf8_text(VENDOR_DIR / "skills.lock.json", "published vendor lock")
    if published_text != serialized_lock:
        fail("published vendor lock differs from the verified staged lock")
    remove_path(old)


def stage_vendor_tree(
    data: dict[str, Any],
    names: list[str],
    update: bool,
    track: str | None = None,
    remove: bool = False,
) -> None:
    """Stage a full vendor copy, apply the operation, verify, publish atomically."""
    validate_vendor_container(VENDOR_DIR)
    unknown = sorted(set(names) - set(data["skills"]))
    if unknown:
        fail(f"unknown skills: {', '.join(unknown)}")
    if not names:
        fail("select at least one skill")
    names = list(dict.fromkeys(names))

    if track is not None:
        for name in names:
            validate_track(name, track)
            data["skills"][name]["track"] = track
    if update:
        for name in names:
            entry = data["skills"][name]
            entry["commit"] = resolve_commit(entry["source"], entry["track"])

    staging = ROOT / f"{STAGING_PREFIX}{secrets.token_hex(12)}"
    staging.mkdir(mode=0o700)
    fsync_directory(ROOT)
    mark_vendor_staging(staging)
    try:
        next_vendor = staging / "vendor"
        shutil.copytree(VENDOR_DIR, next_vendor, symlinks=True, copy_function=shutil.copy2)
        checkouts: dict[tuple[str, str], Path] = {}
        for name in names:
            if remove:
                continue
            entry = data["skills"][name]
            commit = entry["commit"]
            if not COMMIT_RE.fullmatch(commit):
                fail(f"{name}: lock has no pinned commit")
            key = (entry["source"], commit)
            if key not in checkouts:
                repo_dir = staging / "repos" / str(len(checkouts))
                checkout(entry["source"], commit, repo_dir)
                checkouts[key] = repo_dir
            repo_dir = checkouts[key]
            upstream_skill = safe_repo_path(repo_dir, entry["upstreamPath"], "upstreamPath")
            upstream_license = safe_repo_path(repo_dir, entry["licenseSource"], "licenseSource")
            if not upstream_skill.is_dir():
                fail(f"{name}: upstream skill path is missing at {commit}")
            if not upstream_license.is_file():
                fail(f"{name}: upstream license is missing at {commit}")

            staged_skill = next_vendor / "skills" / name
            if path_lexists(staged_skill):
                remove_path(staged_skill)
            shutil.copytree(upstream_skill, staged_skill, symlinks=True, copy_function=shutil.copy2)
            staged_license = next_vendor / "licenses" / f"{name}.txt"
            shutil.copy2(upstream_license, staged_license)

            content_sha = snapshot_hash(staged_skill)
            license_sha = file_hash(staged_license)
            if update:
                entry["contentSha256"] = content_sha
                entry["licenseSha256"] = license_sha
                (next_vendor / "provenance" / f"{name}.json").write_text(provenance_text(name, entry))
            else:
                if content_sha != entry["contentSha256"]:
                    fail(f"{name}: fetched snapshot differs from provenance lock")
                if license_sha != entry["licenseSha256"]:
                    fail(f"{name}: fetched license differs from provenance lock")

        if remove:
            remaining = {n: e for n, e in data["skills"].items() if n not in names}
            if not remaining:
                fail("cannot remove the final vendored snapshot")
            data = {**data, "skills": remaining}
            for name in names:
                staged_skill = next_vendor / "skills" / name
                if path_lexists(staged_skill):
                    remove_path(staged_skill)
                unlink_durable(next_vendor / "licenses" / f"{name}.txt", missing_ok=True)
                unlink_durable(next_vendor / "provenance" / f"{name}.json", missing_ok=True)
        serialized_lock = lock_text(data)
        (next_vendor / "skills.lock.json").write_text(serialized_lock)
        verify(data, next_vendor)
        publish_vendor_tree(next_vendor, data, serialized_lock)
    finally:
        remove_path(staging, missing_ok=True)

    verify(data)


def remove_snapshots(data: dict[str, Any], names: list[str]) -> None:
    """Approved removal: drop selected snapshots and regenerate vendor metadata."""
    validate_vendor_container(VENDOR_DIR)
    if not names:
        fail("select at least one skill")
    names = list(dict.fromkeys(names))
    unknown = sorted(set(names) - set(data["skills"]))
    if unknown:
        fail(f"unknown skills: {', '.join(unknown)}")
    if set(data["skills"]) - set(names) == set():
        fail("cannot remove the final vendored snapshot")
    verify(data)
    stage_vendor_tree(data, names, update=False, remove=True)


def install_hash_environment(data: dict[str, Any]) -> dict[str, str]:
    """Expected hashes for the installer's copy-time re-verification of vendored skills."""
    return {
        "SDLC_VENDOR_CONTENT_HASHES": json.dumps(
            {name: entry["contentSha256"] for name, entry in data["skills"].items()},
            sort_keys=True,
            separators=(",", ":"),
        ),
        "SDLC_VENDOR_PROVENANCE_HASHES": json.dumps(
            {
                name: hashlib.sha256(provenance_text(name, entry).encode()).hexdigest()
                for name, entry in data["skills"].items()
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        "SDLC_VENDOR_LICENSE_HASHES": json.dumps(
            {name: entry["licenseSha256"] for name, entry in data["skills"].items()},
            sort_keys=True,
            separators=(",", ":"),
        ),
    }


def run_locked_installer(command: list[str]) -> NoReturn:
    if not command:
        fail("install-locked requires an installer command")
    with vendor_operation_lock():
        cleanup_stale_vendor_state()
        data = load_lock()
        verify(data)
        environment = os.environ.copy()
        environment["SDLC_VENDOR_LOCKED"] = "1"
        environment.update(install_hash_environment(data))
        try:
            result = subprocess.run(command, check=False, env=environment)
        except OSError as error:
            fail(f"could not run installer: {error}")
    raise SystemExit(result.returncode)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("verify", help="verify snapshots against the provenance lock")
    installed = subparsers.add_parser("verify-installed", help="verify a fresh installed skills directory")
    installed.add_argument("skills_dir", type=Path, help="installed project-local skills directory")
    sync = subparsers.add_parser("sync", help="restore snapshots at their locked commits")
    sync.add_argument("skills", nargs="*", help="skills to restore; defaults to all")
    update = subparsers.add_parser("update", help="refresh selected skills from their tracked refs")
    update.add_argument("skills", nargs="+", help="skills to refresh")
    update.add_argument(
        "--track",
        help="set the tracked ref for the selected skills before resolving commits (e.g. refs/tags/v1.2.0)",
    )
    remove = subparsers.add_parser(
        "remove", help="remove selected snapshots (never the final snapshot) and regenerate vendor metadata"
    )
    remove.add_argument("skills", nargs="+", help="skills to remove")
    subparsers.add_parser("install-hashes", help=argparse.SUPPRESS)
    install = subparsers.add_parser("install-locked", help=argparse.SUPPRESS)
    install.add_argument("installer_command", nargs=argparse.REMAINDER)
    preview = subparsers.add_parser("preview-locked", help=argparse.SUPPRESS)
    preview.add_argument("installer_command", nargs=argparse.REMAINDER)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command in {"install-locked", "preview-locked"}:
        run_locked_installer(args.installer_command)
        return
    if args.command == "install-hashes":
        data = load_lock()
        verify(data)
        print(json.dumps(install_hash_environment(data), separators=(",", ":")))
        return
    with vendor_operation_lock():
        cleanup_stale_vendor_state()
        data = load_lock(allow_unpinned=args.command == "update")
        if args.command == "verify":
            verify(data)
        elif args.command == "verify-installed":
            verify_installed(data, args.skills_dir)
        elif args.command == "sync":
            stage_vendor_tree(data, args.skills or list(data["skills"]), update=False)
        elif args.command == "remove":
            remove_snapshots(data, args.skills)
        else:
            stage_vendor_tree(data, args.skills, update=True, track=args.track)


if __name__ == "__main__":
    main()
