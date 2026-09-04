#!/usr/bin/env python3
"""Verify, restore, refresh, or approved-remove pinned skill snapshots and metadata."""

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
import tempfile
import unicodedata
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, NoReturn

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
VENDOR_BACKUP_NAME = ".vendor-backup"
VENDOR_TRANSACTION_NAME = ".vendor-transaction.json"
VENDOR_STAGING_MARKER = ".sdlc-vendor-staging"
VENDOR_STAGING_MARKER_CONTENT = b"sdlc-vendor-staging-v1\n"
VENDOR_STAGING_INTENT_NAME = ".vendor-staging-intent.json"
VENDOR_STAGING_NAME_RE = re.compile(r"^\.vendor-staging-[0-9a-f]{24}$")
INSTALLED_METADATA_NAME = ".sdlc-vendor"
DIRECTORY_OPEN_FLAGS = (
    os.O_RDONLY
    | getattr(os, "O_DIRECTORY", 0)
    | getattr(os, "O_CLOEXEC", 0)
    | getattr(os, "O_NOFOLLOW", 0)
)


def fail(message: str) -> NoReturn:
    raise SystemExit(message)


def write_all(descriptor: int, content: bytes | memoryview) -> None:
    remaining = memoryview(content)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            fail("write returned no bytes")
        remaining = remaining[written:]


def read_bounded(descriptor: int, limit: int) -> bytes:
    content = bytearray()
    while len(content) < limit:
        chunk = os.read(descriptor, limit - len(content))
        if not chunk:
            break
        content.extend(chunk)
    return bytes(content)


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
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
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
        flag = 1
    elif hasattr(libc, "renameatx_np"):
        rename = libc.renameatx_np
        flag = 0x00000004
    else:
        fail("vendor recovery requires renameat2 or renameatx_np")
    rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
    rename.restype = ctypes.c_int
    return rename, flag


def atomic_rename_noreplace(
    source_parent_fd: int,
    source: str,
    destination_parent_fd: int,
    destination: str,
) -> bool:
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
        track = entry["track"]
        if (
            not TRACK_RE.fullmatch(track)
            or ".." in track
            or "//" in track
            or "@{" in track
            or track.endswith((".", "/"))
        ):
            fail(f"{name}: track must be a safe full commit or refs/ pattern")
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
    return validate_lock_data(
        parse_json_unique(text, label),
        allow_unpinned=allow_unpinned,
    )


def load_lock(allow_unpinned: bool = False) -> dict[str, Any]:
    return load_lock_path(
        LOCK_PATH,
        "provenance lock",
        allow_unpinned=allow_unpinned,
    )


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


def validate_snapshot_links(directory: Path, allow_installed_metadata: bool = False) -> None:
    validate_snapshot_entries(directory, allow_installed_metadata)


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
    validate_snapshot_links(directory, allow_installed_metadata=exclude_installed_metadata)
    for path in sorted(directory.rglob("*"), key=lambda item: item.relative_to(directory).as_posix()):
        relative_path = path.relative_to(directory)
        if exclude_installed_metadata and relative_path.parts[0] == ".sdlc-vendor":
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
    skills_dir = vendor_dir / "skills"
    licenses_dir = vendor_dir / "licenses"
    provenance_dir = vendor_dir / "provenance"
    for path, label in (
        (vendor_dir, "vendor root"),
        (skills_dir, "skills directory"),
        (licenses_dir, "licenses directory"),
        (provenance_dir, "provenance directory"),
    ):
        require_real_directory(path, label)
    for path in skills_dir.iterdir():
        require_real_directory(path, "skill snapshot")
    for path in licenses_dir.iterdir():
        require_regular_file(path, "vendored license")
    for path in provenance_dir.iterdir():
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


def open_published_lock(
    path: Path,
    expected_sha256: str,
) -> tuple[int, dict[str, Any], tuple[int, int]]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        fail(f"could not open published vendor lock: {error}")
    try:
        descriptor_stat = os.fstat(descriptor)
        if not stat.S_ISREG(descriptor_stat.st_mode):
            fail("published vendor lock must be a regular file")
        digest = hashlib.sha256()
        content = bytearray()
        while chunk := os.read(descriptor, 64 * 1024):
            content.extend(chunk)
            if len(content) > 1024 * 1024:
                fail("published vendor lock exceeds 1 MiB")
            digest.update(chunk)
        if digest.hexdigest() != expected_sha256:
            fail("published vendor lock differs from the verified staged lock")
        try:
            text = bytes(content).decode("utf-8")
        except UnicodeError as error:
            fail(f"invalid published vendor lock: {error}")
        data = validate_lock_data(parse_json_unique(text, "published vendor lock"))
        return descriptor, data, (descriptor_stat.st_dev, descriptor_stat.st_ino)
    except BaseException:
        os.close(descriptor)
        raise


def revalidate_published_lock(
    path: Path,
    descriptor: int,
    identity: tuple[int, int],
    expected_sha256: str,
) -> None:
    try:
        current = path.lstat()
    except OSError as error:
        fail(f"published vendor lock disappeared during verification: {error}")
    if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != identity:
        fail("published vendor lock changed during verification")
    os.lseek(descriptor, 0, os.SEEK_SET)
    digest = hashlib.sha256()
    while chunk := os.read(descriptor, 64 * 1024):
        digest.update(chunk)
    if digest.hexdigest() != expected_sha256:
        fail("published vendor lock content changed during verification")


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
    actual_licenses = {path.name for path in licenses_dir.iterdir()}
    actual_provenance = {path.name for path in provenance_dir.iterdir()}
    if actual_licenses != expected_licenses or actual_provenance != expected_provenance:
        fail("vendored license or provenance inventory differs from the skill lock")

    for name, entry in data["skills"].items():
        actual_content = snapshot_hash(skills_dir / name)
        if actual_content != entry["contentSha256"]:
            fail(f"{name}: snapshot hash differs from provenance lock")
        actual_license = file_hash(licenses_dir / f"{name}.txt")
        if actual_license != entry["licenseSha256"]:
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
        metadata_dir = skill_dir / ".sdlc-vendor"
        provenance_file = metadata_dir / "provenance.json"
        license_file = metadata_dir / "LICENSE.txt"
        require_real_directory(skill_dir, "installed skill")
        require_real_directory(metadata_dir, "installed metadata directory")
        verify_installed_modes(skill_dir)
        if {path.name for path in metadata_dir.iterdir()} != {"provenance.json", "LICENSE.txt"}:
            fail(f"{name}: installed metadata inventory is invalid")
        require_regular_file(provenance_file, "installed provenance")
        require_regular_file(license_file, "installed license")
        if stat.S_IMODE(provenance_file.stat().st_mode) != 0o644:
            fail(f"{name}: installed provenance mode is not 0644")
        if stat.S_IMODE(license_file.stat().st_mode) != 0o644:
            fail(f"{name}: installed license mode is not 0644")
        if read_utf8_text(provenance_file, "installed provenance") != provenance_text(name, entry):
            fail(f"{name}: installed provenance differs from the skill lock")
        if snapshot_hash(skill_dir, exclude_installed_metadata=True) != entry["contentSha256"]:
            fail(f"{name}: installed content differs from the skill lock")
        if file_hash(license_file) != entry["licenseSha256"]:
            fail(f"{name}: installed license differs from the skill lock")


def resolve_commit(source: str, track: str) -> str:
    if COMMIT_RE.fullmatch(track):
        return track
    output = run("git", "ls-remote", source, track)
    matches = [line.split()[0] for line in output.splitlines() if line.strip()]
    if len(matches) != 1 or not COMMIT_RE.fullmatch(matches[0]):
        fail(f"could not resolve one commit for {source} {track}")
    return matches[0]


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


def remove_path(path: Path) -> None:
    try:
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


def validate_inherited_lock(descriptor: int, root: Path = ROOT) -> None:
    try:
        inherited = os.fstat(descriptor)
        expected = root.stat()
    except OSError as error:
        fail(f"invalid inherited vendor operation lock: {error}")
    if not stat.S_ISDIR(inherited.st_mode) or (inherited.st_dev, inherited.st_ino) != (
        expected.st_dev,
        expected.st_ino,
    ):
        fail("inherited vendor operation lock does not reference the repository directory")

    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        probe = os.open(root, flags)
    except OSError as error:
        fail(f"could not verify inherited vendor operation lock: {error}")
    try:
        try:
            fcntl.flock(probe, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            pass
        else:
            fcntl.flock(probe, fcntl.LOCK_UN)
            fail("inherited vendor operation lock was not already locked")
    finally:
        os.close(probe)

    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        fail("inherited vendor operation lock is not held by this installer")


def install_hash_environment(data: dict[str, Any]) -> dict[str, str]:
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


def validate_install_hash_environment(data: dict[str, Any]) -> None:
    for name, expected in install_hash_environment(data).items():
        if os.environ.get(name) != expected:
            fail(f"invalid inherited vendor hash environment: {name}")


def continue_locked_install(descriptor: int, recover: bool) -> None:
    validate_inherited_lock(descriptor)
    if recover:
        recover_vendor_transaction()
        recover_vendor_staging()
    data = load_lock()
    verify(data)
    validate_install_hash_environment(data)


def remove_verified_directory_entry(parent_fd: int, name: str, opened_fd: int) -> None:
    expected = os.fstat(opened_fd)
    try:
        actual = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as error:
        fail(f"vendor staging entry disappeared during recovery: {name} ({error})")
    if not stat.S_ISDIR(actual.st_mode) or (actual.st_dev, actual.st_ino) != (
        expected.st_dev,
        expected.st_ino,
    ):
        fail(f"vendor staging entry changed during recovery: {name}")
    try:
        os.rmdir(name, dir_fd=parent_fd)
    except OSError as error:
        fail(f"could not remove vendor staging directory: {name} ({error})")


def preserve_stale_staging(root_fd: int, name: str, staging_fd: int) -> str:
    expected = os.fstat(staging_fd)
    for _attempt in range(8):
        preserved = f".vendor-preserved-{secrets.token_hex(12)}"
        if atomic_rename_noreplace(root_fd, name, root_fd, preserved):
            break
    else:
        fail(f"could not quarantine stale vendor staging directory: {name}")
    try:
        moved = os.stat(preserved, dir_fd=root_fd, follow_symlinks=False)
    except OSError as error:
        fail(f"could not inspect quarantined vendor staging: {preserved} ({error})")
    if not stat.S_ISDIR(moved.st_mode) or (moved.st_dev, moved.st_ino) != (
        expected.st_dev,
        expected.st_ino,
    ):
        fail(f"vendor staging changed while quarantining: {name}; preserved as {preserved}")
    os.fsync(root_fd)
    print(
        f"warning: preserved interrupted vendor staging as {preserved}; inspect and remove it manually",
        file=sys.stderr,
    )
    return preserved


def remove_vendor_staging_contents(directory_fd: int) -> None:
    try:
        names = os.listdir(directory_fd)
    except OSError as error:
        fail(f"could not list vendor staging directory: {error}")
    for name in names:
        try:
            entry = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
        except OSError as error:
            fail(f"could not inspect vendor staging entry: {name} ({error})")
        if stat.S_ISDIR(entry.st_mode):
            try:
                child_fd = os.open(name, DIRECTORY_OPEN_FLAGS, dir_fd=directory_fd)
            except OSError as error:
                fail(f"could not open vendor staging directory: {name} ({error})")
            try:
                remove_vendor_staging_contents(child_fd)
                remove_verified_directory_entry(directory_fd, name, child_fd)
            finally:
                os.close(child_fd)
        else:
            try:
                os.unlink(name, dir_fd=directory_fd)
            except OSError as error:
                fail(f"could not remove vendor staging entry: {name} ({error})")


def remove_verified_vendor_staging(root_fd: int, name: str, staging_fd: int) -> None:
    remove_vendor_staging_contents(staging_fd)
    remove_verified_directory_entry(root_fd, name, staging_fd)
    os.fsync(root_fd)


def vendor_staging_intent_path(root: Path = ROOT) -> Path:
    return root / VENDOR_STAGING_INTENT_NAME


def write_vendor_staging_intent(staging_name: str, root: Path = ROOT) -> None:
    if not VENDOR_STAGING_NAME_RE.fullmatch(staging_name):
        fail(f"invalid vendor staging name: {staging_name}")
    temporary_name = f"{VENDOR_STAGING_INTENT_NAME}.tmp-{secrets.token_hex(12)}"
    root_fd = os.open(root, DIRECTORY_OPEN_FLAGS)
    try:
        descriptor = os.open(
            temporary_name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=root_fd,
        )
        try:
            try:
                payload = json.dumps({"version": 1, "staging": staging_name}, sort_keys=True) + "\n"
                write_all(descriptor, payload.encode())
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            if not atomic_rename_noreplace(
                root_fd,
                temporary_name,
                root_fd,
                VENDOR_STAGING_INTENT_NAME,
            ):
                fail("vendor staging intent already exists")
            os.fsync(root_fd)
        except BaseException:
            try:
                os.unlink(temporary_name, dir_fd=root_fd)
                os.fsync(root_fd)
            except FileNotFoundError:
                pass
            raise
    finally:
        os.close(root_fd)


def clear_vendor_staging_intent(root: Path = ROOT, missing_ok: bool = False) -> None:
    unlink_durable(vendor_staging_intent_path(root), missing_ok=missing_ok)


def validate_vendor_intent_recovery_state(staging_fd: int) -> tuple[int, int] | None:
    try:
        names = os.listdir(staging_fd)
    except OSError as error:
        fail(f"could not list vendor staging intent target: {error}")
    if not names:
        return None
    if names != [VENDOR_STAGING_MARKER]:
        fail("vendor staging intent target contains unexpected entries")
    try:
        marker_fd = os.open(
            VENDOR_STAGING_MARKER,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=staging_fd,
        )
    except OSError as error:
        fail(f"vendor staging intent marker is unreadable: {error}")
    try:
        marker_stat = os.fstat(marker_fd)
        marker_content = read_bounded(marker_fd, len(VENDOR_STAGING_MARKER_CONTENT) + 1)
    finally:
        os.close(marker_fd)
    if not stat.S_ISREG(marker_stat.st_mode) or marker_content != VENDOR_STAGING_MARKER_CONTENT:
        fail("vendor staging intent marker is invalid")
    return marker_stat.st_dev, marker_stat.st_ino


def quarantine_intended_vendor_staging(
    root_fd: int,
    staging_name: str,
    staging_fd: int,
) -> None:
    preserve_stale_staging(root_fd, staging_name, staging_fd)


def recover_vendor_staging_intent(root_fd: int, root: Path) -> None:
    intent = vendor_staging_intent_path(root)
    if not path_lexists(intent):
        return
    require_regular_file(intent, "vendor staging intent")
    intent_data = parse_json_unique(read_utf8_text(intent, "vendor staging intent"), "vendor staging intent")
    if (
        not isinstance(intent_data, dict)
        or set(intent_data) != {"version", "staging"}
        or type(intent_data["version"]) is not int
        or intent_data["version"] != 1
        or not isinstance(intent_data["staging"], str)
        or not VENDOR_STAGING_NAME_RE.fullmatch(intent_data["staging"])
    ):
        fail(f"invalid vendor staging intent: {intent}")
    staging_name = intent_data["staging"]
    try:
        staging_fd = os.open(staging_name, DIRECTORY_OPEN_FLAGS, dir_fd=root_fd)
    except FileNotFoundError:
        clear_vendor_staging_intent(root)
        return
    except OSError as error:
        fail(f"vendor staging intent target must be a real directory: {staging_name} ({error})")
    try:
        validate_vendor_intent_recovery_state(staging_fd)
        quarantine_intended_vendor_staging(root_fd, staging_name, staging_fd)
    finally:
        os.close(staging_fd)
    clear_vendor_staging_intent(root)


def recover_vendor_staging(root: Path = ROOT) -> None:
    try:
        root_fd = os.open(root, DIRECTORY_OPEN_FLAGS)
    except OSError as error:
        fail(f"could not open repository directory for staging recovery: {error}")
    try:
        recover_vendor_staging_intent(root_fd, root)
        try:
            names = os.listdir(root_fd)
        except OSError as error:
            fail(f"could not list repository directory for staging recovery: {error}")
        for name in sorted(name for name in names if name.startswith(".vendor-staging-")):
            try:
                staging_fd = os.open(name, DIRECTORY_OPEN_FLAGS, dir_fd=root_fd)
            except OSError as error:
                fail(f"vendor staging directory must be a real directory: {name} ({error})")
            try:
                try:
                    marker_fd = os.open(
                        VENDOR_STAGING_MARKER,
                        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
                        dir_fd=staging_fd,
                    )
                except OSError as error:
                    fail(f"missing or unreadable vendor staging marker: {name} ({error})")
                try:
                    marker_stat = os.fstat(marker_fd)
                    if not stat.S_ISREG(marker_stat.st_mode):
                        fail(f"vendor staging marker must be a regular file: {name}")
                    marker_content = read_bounded(
                        marker_fd,
                        len(VENDOR_STAGING_MARKER_CONTENT) + 1,
                    )
                finally:
                    os.close(marker_fd)
                if marker_content != VENDOR_STAGING_MARKER_CONTENT:
                    fail(f"invalid vendor staging marker: {name}")
                preserve_stale_staging(root_fd, name, staging_fd)
            finally:
                os.close(staging_fd)
    finally:
        os.close(root_fd)


def mark_vendor_staging(staging: Path) -> None:
    marker = staging / VENDOR_STAGING_MARKER
    descriptor = os.open(
        marker,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        write_all(descriptor, VENDOR_STAGING_MARKER_CONTENT)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    fsync_directory(staging)
    fsync_directory(staging.parent)


def transaction_marker_path(root: Path = ROOT) -> Path:
    return root / VENDOR_TRANSACTION_NAME


def write_transaction_marker(
    phase: str,
    expected_lock_sha256: str,
    root: Path = ROOT,
) -> None:
    if not HASH_RE.fullmatch(expected_lock_sha256):
        fail("vendor transaction marker requires an expected lock SHA-256")
    marker = transaction_marker_path(root)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f"{VENDOR_TRANSACTION_NAME}.tmp-", dir=root)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as marker_file:
            marker_file.write(
                json.dumps(
                    {
                        "version": 1,
                        "phase": phase,
                        "expectedLockSha256": expected_lock_sha256,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            marker_file.flush()
            os.fsync(marker_file.fileno())
        os.replace(temporary, marker)
        fsync_directory(root)
    finally:
        temporary.unlink(missing_ok=True)


def recover_vendor_transaction(root: Path = ROOT) -> None:
    vendor = root / "vendor"
    backup = root / VENDOR_BACKUP_NAME
    marker = transaction_marker_path(root)
    if not path_lexists(marker):
        if path_lexists(backup):
            fail(f"vendor backup exists without a transaction marker: {backup}")
        return

    require_regular_file(marker, "vendor transaction marker")
    marker_data = parse_json_unique(
        read_utf8_text(marker, "vendor transaction marker"),
        "vendor transaction marker",
    )
    if (
        not isinstance(marker_data, dict)
        or set(marker_data) != {"version", "phase", "expectedLockSha256"}
        or type(marker_data["version"]) is not int
        or marker_data["version"] != 1
        or not isinstance(marker_data["phase"], str)
        or marker_data["phase"] not in {"prepared", "old-renamed", "new-published", "rolling-back"}
        or not isinstance(marker_data["expectedLockSha256"], str)
        or not HASH_RE.fullmatch(marker_data["expectedLockSha256"])
    ):
        fail(f"invalid vendor transaction marker: {marker}")

    expected_lock_sha256 = marker_data["expectedLockSha256"]
    phase = marker_data["phase"]
    if not path_lexists(vendor) and path_lexists(backup):
        require_real_directory(backup, "vendor transaction backup")
        backup_data = load_lock_path(backup / "skills.lock.json", "vendor backup provenance lock")
        verify(backup_data, backup)
        rename_durable(backup, vendor)
    elif path_lexists(vendor) and path_lexists(backup):
        require_real_directory(backup, "vendor transaction backup")
        verify_vendor_against_expected_lock(vendor, expected_lock_sha256)
        remove_path(backup)
    elif path_lexists(vendor) and not path_lexists(backup):
        if phase in {"prepared", "rolling-back"}:
            candidate_data = load_lock_path(vendor / "skills.lock.json", "vendor current provenance lock")
            verify(candidate_data, vendor)
        else:
            verify_vendor_against_expected_lock(vendor, expected_lock_sha256)
    else:
        fail("vendor transaction lost both the current tree and its backup")
    unlink_durable(marker)


def verify_vendor_against_expected_lock(vendor_dir: Path, expected_lock_sha256: str) -> None:
    published_lock = vendor_dir / "skills.lock.json"
    lock_fd, candidate_data, lock_identity = open_published_lock(
        published_lock,
        expected_lock_sha256,
    )
    try:
        verify(candidate_data, vendor_dir)
        revalidate_published_lock(
            published_lock,
            lock_fd,
            lock_identity,
            expected_lock_sha256,
        )
    finally:
        os.close(lock_fd)


def replace_vendor_tree(source: Path, expected_lock_sha256: str) -> None:
    backup = ROOT / VENDOR_BACKUP_NAME
    marker = transaction_marker_path()
    if path_lexists(backup) or path_lexists(marker):
        fail("cannot publish while a prior vendor transaction needs recovery")
    if not HASH_RE.fullmatch(expected_lock_sha256):
        fail("published vendor lock expectation must be a SHA-256 digest")

    write_transaction_marker("prepared", expected_lock_sha256)
    rename_durable(VENDOR_DIR, backup)
    write_transaction_marker("old-renamed", expected_lock_sha256)
    try:
        rename_durable(source, VENDOR_DIR)
    except OSError as error:
        if not path_lexists(VENDOR_DIR):
            write_transaction_marker("rolling-back", expected_lock_sha256)
            rename_durable(backup, VENDOR_DIR)
            unlink_durable(marker, missing_ok=True)
        raise error
    write_transaction_marker("new-published", expected_lock_sha256)
    verify_vendor_against_expected_lock(VENDOR_DIR, expected_lock_sha256)
    remove_path(backup)
    unlink_durable(marker)


def cleanup_vendor_staging(staging: Path) -> None:
    if not path_lexists(staging):
        return
    root_fd = os.open(staging.parent, DIRECTORY_OPEN_FLAGS)
    try:
        staging_fd = os.open(staging.name, DIRECTORY_OPEN_FLAGS, dir_fd=root_fd)
        try:
            remove_verified_vendor_staging(root_fd, staging.name, staging_fd)
        finally:
            os.close(staging_fd)
    finally:
        os.close(root_fd)


def cleanup_failed_vendor_staging(staging: Path) -> None:
    try:
        cleanup_vendor_staging(staging)
    except BaseException as cleanup_error:
        print(
            f"warning: vendor staging cleanup failed; recovery intent retained: {cleanup_error}",
            file=sys.stderr,
        )
    else:
        clear_vendor_staging_intent(missing_ok=True)


def materialize(data: dict[str, Any], names: list[str], update: bool) -> None:
    validate_vendor_container(VENDOR_DIR)
    unknown = sorted(set(names) - set(data["skills"]))
    if unknown:
        fail(f"unknown skills: {', '.join(unknown)}")
    if not names:
        fail("select at least one skill")

    if update:
        for name in names:
            entry = data["skills"][name]
            entry["commit"] = resolve_commit(entry["source"], entry["track"])

    staging_name = f".vendor-staging-{secrets.token_hex(12)}"
    staging = ROOT / staging_name
    write_vendor_staging_intent(staging_name)
    try:
        staging.mkdir(mode=0o700)
    except FileExistsError:
        clear_vendor_staging_intent(missing_ok=True)
        raise
    except BaseException:
        cleanup_failed_vendor_staging(staging)
        raise
    try:
        fsync_directory(ROOT)
        mark_vendor_staging(staging)
        clear_vendor_staging_intent()
    except BaseException:
        cleanup_failed_vendor_staging(staging)
        raise
    try:
        next_vendor = staging / "vendor"
        shutil.copytree(VENDOR_DIR, next_vendor, symlinks=True, copy_function=shutil.copy2)
        validate_vendor_container(next_vendor)
        checkouts: dict[tuple[str, str], Path] = {}
        for name in names:
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
            else:
                if content_sha != entry["contentSha256"]:
                    fail(f"{name}: fetched snapshot differs from provenance lock")
                if license_sha != entry["licenseSha256"]:
                    fail(f"{name}: fetched license differs from provenance lock")

        serialized_lock = lock_text(data)
        (next_vendor / "skills.lock.json").write_text(serialized_lock)
        provenance_dir = next_vendor / "provenance"
        if path_lexists(provenance_dir):
            remove_path(provenance_dir)
        provenance_dir.mkdir()
        for name, entry in data["skills"].items():
            (provenance_dir / f"{name}.json").write_text(provenance_text(name, entry))

        verify(data, next_vendor)
        fsync_tree(next_vendor)
        expected_lock_sha256 = hashlib.sha256(serialized_lock.encode()).hexdigest()
        replace_vendor_tree(next_vendor, expected_lock_sha256)
    finally:
        cleanup_vendor_staging(staging)

    verify(data)


def remove_snapshots(data: dict[str, Any], names: list[str]) -> None:
    """Transactionally remove selected snapshots and regenerate vendor metadata."""
    validate_vendor_container(VENDOR_DIR)
    if not names:
        fail("select at least one skill")
    names = list(dict.fromkeys(names))
    unknown = sorted(set(names) - set(data["skills"]))
    if unknown:
        fail(f"unknown skills: {', '.join(unknown)}")
    verify(data)
    remaining = {name: entry for name, entry in data["skills"].items() if name not in names}
    if not remaining:
        fail("cannot remove the final vendored snapshot")
    next_data = {**data, "skills": remaining}
    staging_name = f".vendor-staging-{secrets.token_hex(12)}"
    staging = ROOT / staging_name
    write_vendor_staging_intent(staging_name)
    try:
        staging.mkdir(mode=0o700)
    except FileExistsError:
        clear_vendor_staging_intent(missing_ok=True)
        raise
    except BaseException:
        cleanup_failed_vendor_staging(staging)
        raise
    try:
        fsync_directory(ROOT)
        mark_vendor_staging(staging)
        clear_vendor_staging_intent()
    except BaseException:
        cleanup_failed_vendor_staging(staging)
        raise
    try:
        next_vendor = staging / "vendor"
        shutil.copytree(VENDOR_DIR, next_vendor, symlinks=True, copy_function=shutil.copy2)
        for name in names:
            remove_path(next_vendor / "skills" / name)
            unlink_durable(next_vendor / "licenses" / f"{name}.txt")
            unlink_durable(next_vendor / "provenance" / f"{name}.json")
        serialized_lock = lock_text(next_data)
        (next_vendor / "skills.lock.json").write_text(serialized_lock)
        verify(next_data, next_vendor)
        fsync_tree(next_vendor)
        expected_lock_sha256 = hashlib.sha256(serialized_lock.encode()).hexdigest()
        replace_vendor_tree(next_vendor, expected_lock_sha256)
    finally:
        cleanup_vendor_staging(staging)
    verify(next_data)


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
    remove = subparsers.add_parser("remove", help="remove selected snapshots (never the final snapshot) and regenerate vendor metadata")
    remove.add_argument("skills", nargs="+", help="skills to remove")
    install = subparsers.add_parser("install-locked", help=argparse.SUPPRESS)
    install.add_argument("installer_command", nargs=argparse.REMAINDER)
    preview = subparsers.add_parser("preview-locked", help=argparse.SUPPRESS)
    preview.add_argument("installer_command", nargs=argparse.REMAINDER)
    inherited = subparsers.add_parser("continue-locked", help=argparse.SUPPRESS)
    inherited.add_argument("descriptor", type=int)
    inherited_preview = subparsers.add_parser("continue-preview-locked", help=argparse.SUPPRESS)
    inherited_preview.add_argument("descriptor", type=int)
    return parser.parse_args()


def run_locked_installer(command: list[str], recover: bool = True) -> NoReturn:
    if not command:
        fail("install-locked requires an installer command")
    with vendor_operation_lock() as lock_descriptor:
        if recover:
            recover_vendor_transaction()
            recover_vendor_staging()
        data = load_lock()
        verify(data)
        environment = os.environ.copy()
        environment.pop("SDLC_VENDOR_LOCK_HELD", None)
        environment["SDLC_VENDOR_LOCK_FD"] = str(lock_descriptor)
        environment.update(install_hash_environment(data))
        try:
            result = subprocess.run(
                command,
                check=False,
                env=environment,
                pass_fds=(lock_descriptor,),
            )
        except OSError as error:
            fail(f"could not run installer: {error}")
    raise SystemExit(result.returncode)


def main() -> None:
    args = parse_args()
    if args.command == "install-locked":
        run_locked_installer(args.installer_command)
    if args.command == "preview-locked":
        run_locked_installer(args.installer_command, recover=False)
    if args.command == "continue-locked":
        continue_locked_install(args.descriptor, recover=True)
        return
    if args.command == "continue-preview-locked":
        continue_locked_install(args.descriptor, recover=False)
        return
    with vendor_operation_lock():
        recover_vendor_transaction()
        recover_vendor_staging()
        data = load_lock(allow_unpinned=args.command == "update")
        if args.command == "verify":
            verify(data)
        elif args.command == "verify-installed":
            verify_installed(data, args.skills_dir)
        elif args.command == "sync":
            materialize(data, args.skills or list(data["skills"]), update=False)
        elif args.command == "remove":
            remove_snapshots(data, args.skills)
        else:
            materialize(data, args.skills, update=True)


if __name__ == "__main__":
    main()
