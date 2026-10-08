#!/usr/bin/env python3
"""No-clobber publication, install manifest, and checksum-gated upgrade for install.sh.

Guarantees (see AGENTS.md): containment inside an explicit allowed root,
no-clobber publication, atomic publication through staged renames, restrictive
normalized modes, dry-run immutability (owned by install.sh), and
interrupted-run staging cleanup.
"""
from __future__ import annotations

import argparse
import contextlib
import difflib
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
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

STAGING_FILE_RE = re.compile(r"\.sdlc-file-[0-9a-f]{24}\Z")
STAGING_SKILL_RE = re.compile(
    r"\.sdlc-skill-[a-z0-9](?:[a-z0-9._-]{0,38}[a-z0-9])?-[0-9a-f]{24}\Z"
)
KIT_VERSION_MARKER = ".sdlc-kit-version"
KIT_MANIFEST_MARKER = ".sdlc-kit-manifest.json"
MANIFEST_VERSION = 3
KIT_BASE_DIR = ".sdlc-kit-base"
# Fill-once template instances: the kit publishes the shape once; once the
# adopter fills one in, it is their document and kit template drift must not
# be spliced into it. Everything else the kit publishes is living (mergeable)
# except pinned snapshots, which are decided by their kit source path.
INSTANCE_DOC_STEMS = {"architecture.md", "security.md"}
INSTANCE_DOC_DIRS = {"specs", "changes", "adr", "contracts"}
INSTALLED_DIRECTORY_MODE = 0o755
INSTALLED_REGULAR_MODE = 0o644
INSTALLED_EXECUTABLE_MODE = 0o755
NORMALIZED_TIMESTAMP_NS = 0


class InstallError(RuntimeError):
    """A publication or upgrade precondition failed."""


def staging_file_name() -> str:
    return ".sdlc-file-" + secrets.token_hex(12)


def skill_staging_name(name: str) -> str:
    label = re.sub(r"[^a-z0-9._-]", "-", name.lower())[:40].strip("._-") or "skill"
    return f".sdlc-skill-{label}-" + secrets.token_hex(12)


def fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    except OSError as error:
        raise InstallError(f"could not open directory: {path}") from error
    try:
        os.fsync(descriptor)
    except OSError as error:
        raise InstallError(f"could not flush directory: {path}") from error
    finally:
        os.close(descriptor)


def reject_linebreaks(*paths: str) -> None:
    for path in paths:
        if "\n" in path or "\r" in path:
            raise InstallError("paths must not contain line breaks")


def contained_parent(root: Path, destination: Path) -> Path:
    """Validate every component from root to destination's parent.

    Rejects symlinked or non-directory components so no write escapes the
    allowed root through an aliased path. Returns the validated parent.
    """
    reject_linebreaks(str(root), str(destination))
    root = root.absolute()
    destination = destination.absolute()
    if destination == root:
        raise InstallError(f"destination must be inside the allowed root: {destination}")
    if root != Path("/") and root not in destination.parents:
        raise InstallError(f"refusing write outside allowed root: {destination}")
    parent = destination.parent
    current = root
    try:
        parts = parent.relative_to(root).parts
    except ValueError as error:
        raise InstallError(f"refusing write outside allowed root: {destination}") from error
    for part in parts:
        current = current / part
        try:
            entry = current.lstat()
        except OSError as error:
            raise InstallError(f"could not inspect destination parent: {current}") from error
        if stat.S_ISLNK(entry.st_mode):
            raise InstallError(f"refusing write through symlinked directory: {current}")
        if not stat.S_ISDIR(entry.st_mode):
            raise InstallError(f"refusing write through non-directory path: {current}")
    return parent


def make_directories(root: Path, destination: Path) -> Path:
    """Create destination's parent chain inside root, no-clobber on files."""
    root = root.absolute()
    parent = destination.absolute().parent
    try:
        parts = parent.relative_to(root).parts
    except ValueError as error:
        raise InstallError(f"refusing write outside allowed root: {parent}") from error
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise InstallError(f"refusing write through symlinked directory: {current}")
        if current.exists():
            if not current.is_dir():
                raise InstallError(f"refusing write through non-directory path: {current}")
            continue
        try:
            current.mkdir(mode=INSTALLED_DIRECTORY_MODE)
        except FileExistsError:
            if not current.is_dir():
                raise InstallError(
                    f"refusing write through non-directory path: {current}"
                ) from None
            continue
        except OSError as error:
            raise InstallError(f"could not create directory: {current}") from error
        os.chmod(current, INSTALLED_DIRECTORY_MODE)
        os.utime(current, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
        fsync_directory(current.parent)
    return parent


def normalized_file_mode(source_mode: int) -> int:
    if source_mode & 0o111:
        return INSTALLED_EXECUTABLE_MODE
    return INSTALLED_REGULAR_MODE


def validate_source_file(source: Path) -> int:
    try:
        entry = source.lstat()
    except OSError as error:
        raise InstallError(f"could not inspect installation source: {source}") from error
    if stat.S_ISLNK(entry.st_mode) or not stat.S_ISREG(entry.st_mode):
        raise InstallError(f"installation source must be a regular file: {source}")
    return stat.S_IMODE(entry.st_mode)


def validate_source_directory(source: Path) -> None:
    try:
        entry = source.lstat()
    except OSError as error:
        raise InstallError(f"could not inspect installation source: {source}") from error
    if stat.S_ISLNK(entry.st_mode) or not stat.S_ISDIR(entry.st_mode):
        raise InstallError(f"installation source must be a real directory: {source}")


def copy_file_bytes(source: Path, destination: Path, mode: int) -> None:
    """Copy source content to a fresh destination path with normalized metadata."""
    try:
        with open(source, "rb") as reader, open(destination, "xb") as writer:
            shutil.copyfileobj(reader, writer)
            writer.flush()
            os.fsync(writer.fileno())
        os.chmod(destination, mode)
        os.utime(destination, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
    except OSError as error:
        with contextlib.suppress(OSError):
            destination.unlink()
        raise InstallError(f"could not copy {source} to {destination}: {error}") from error


def clean_stale_staging(parent: Path) -> None:
    """Remove only entries matching the installer's generated staging shapes.

    Names with a partial or ambiguous shape and entries of the wrong type are
    left untouched; the caller holds the parent lock, excluding live publishers.
    """
    changed = False
    try:
        entries = sorted(parent.iterdir())
    except OSError as error:
        raise InstallError(f"could not enumerate {parent}") from error
    for entry in entries:
        name = entry.name
        try:
            if STAGING_FILE_RE.fullmatch(name):
                if not entry.is_file():
                    continue
                entry.unlink()
                changed = True
            elif STAGING_SKILL_RE.fullmatch(name):
                if not entry.is_dir():
                    continue
                shutil.rmtree(entry)
                changed = True
        except OSError as error:
            raise InstallError(f"could not clean staging entry {entry}: {error}") from error
    if changed:
        fsync_directory(parent)


def copy_tree_staged(source: Path, staging: Path) -> None:
    """Populate a staged directory with normalized modes and timestamps."""
    validate_source_directory(source)
    for current, directories, files in os.walk(source):
        relative = Path(current).relative_to(source)
        target = staging / relative
        for name in directories:
            entry = Path(current) / name
            if entry.is_symlink() or not entry.is_dir():
                raise InstallError(f"unsupported source entry: {entry}")
            try:
                (target / name).mkdir()
                os.chmod(target / name, INSTALLED_DIRECTORY_MODE)
            except OSError as error:
                raise InstallError(f"could not stage directory {entry}: {error}") from error
        for name in files:
            entry = Path(current) / name
            if entry.is_symlink() or not entry.is_file():
                raise InstallError(f"unsupported source entry: {entry}")
            copy_file_bytes(entry, target / name, normalized_file_mode(entry.lstat().st_mode))
    for current, _directories, _files in os.walk(staging, topdown=False):
        os.utime(current, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS),
                 follow_symlinks=False)
        fsync_directory(Path(current))


def publish_file(root: Path, source: Path, destination: Path) -> str:
    """No-clobber file publication; returns "added" or "exists"."""
    make_directories(root, destination)
    parent = contained_parent(root, destination)
    if os.path.lexists(destination):
        return "exists"
    mode = normalized_file_mode(validate_source_file(source))
    try:
        lock = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    except OSError as error:
        raise InstallError(f"could not open publication parent: {parent}") from error
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        clean_stale_staging(parent)
        if os.path.lexists(destination):
            return "exists"
        temporary = parent / staging_file_name()
        published = False
        try:
            copy_file_bytes(source, temporary, mode)
            try:
                os.link(temporary, destination)
                published = True
            except OSError as error:
                if error.errno == errno.EEXIST:
                    return "exists"
                if error.errno not in (errno.ENOTSUP, errno.EPERM, errno.EXDEV):
                    raise InstallError(f"could not publish {destination}: {error}") from error
                # Filesystems without hard links: exclusive create is still atomic no-clobber.
                try:
                    with open(destination, "xb"):
                        pass
                    copy_file_bytes(source, destination, mode)
                    published = True
                except FileExistsError:
                    return "exists"
        finally:
            with contextlib.suppress(OSError):
                temporary.unlink()
        if published:
            fsync_directory(parent)
        return "added"
    finally:
        os.close(lock)


def replace_file(source: Path, destination: Path) -> None:
    """Ownership-proven replacement: atomic, mode- and time-normalized."""
    mode = normalized_file_mode(validate_source_file(source))
    parent = destination.parent
    temporary = parent / staging_file_name()
    try:
        copy_file_bytes(source, temporary, mode)
        os.replace(temporary, destination)
    finally:
        with contextlib.suppress(OSError):
            temporary.unlink()
    fsync_directory(parent)


def publish_tree(root: Path, source: Path, destination: Path) -> str:
    """No-clobber atomic directory publication; returns "added" or "exists"."""
    make_directories(root, destination)
    parent = contained_parent(root, destination)
    if os.path.lexists(destination):
        return "exists"
    validate_source_directory(source)
    try:
        lock = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    except OSError as error:
        raise InstallError(f"could not open publication parent: {parent}") from error
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        clean_stale_staging(parent)
        if os.path.lexists(destination):
            return "exists"
        staging = parent / skill_staging_name(destination.name)
        try:
            staging.mkdir(mode=INSTALLED_DIRECTORY_MODE)
            os.chmod(staging, INSTALLED_DIRECTORY_MODE)
        except OSError as error:
            raise InstallError(f"could not stage {destination}: {error}") from error
        try:
            copy_tree_staged(source, staging)
            try:
                os.rename(staging, destination)
            except OSError as error:
                if error.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                    raise InstallError(f"could not publish {destination}: {error}") from error
                shutil.rmtree(staging, ignore_errors=True)
                return "exists"
        except BaseException:
            shutil.rmtree(staging, ignore_errors=True)
            raise
        fsync_directory(parent)
        return "added"
    finally:
        os.close(lock)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as reader:
            for block in iter(lambda: reader.read(1 << 20), b""):
                digest.update(block)
    except OSError as error:
        raise InstallError(f"could not hash {path}: {error}") from error
    return digest.hexdigest()


def read_text_guarded(path: Path) -> str:
    try:
        return path.read_text()
    except OSError as error:
        raise InstallError(f"could not read {path}: {error}") from error


def kit_version_of(kit: Path) -> str:
    lines = read_text_guarded(kit / "CHANGELOG.md").splitlines()
    in_unreleased = False
    for line in lines:
        if line == "## [Unreleased]":
            in_unreleased = True
            continue
        if in_unreleased and line.startswith("## ["):
            break
        if in_unreleased and line.strip() and not line.startswith("### "):
            return "unreleased"
    for line in lines:
        if line.startswith("## [") and "] - " in line:
            return line[4 : line.index("]")]
    raise InstallError("CHANGELOG.md has no released version section")


def payload_entries(kit: Path) -> list[tuple[str, str, Path]]:
    """The installer's full destination mapping as (kind, relative, source)."""
    entries: list[tuple[str, str, Path]] = []
    for name, source in (
        ("AGENTS.md", kit / "templates/AGENTS.md"),
        ("CLAUDE.md", kit / "templates/CLAUDE.md"),
        ("required-skills.yml", kit / "required-skills.yml"),
    ):
        entries.append(("target", name, source))
    for tree_source, tree_destination in (
        (kit / "templates/docs", "docs"),
        (kit / "templates/github", ".github"),
    ):
        if tree_source.is_dir():
            for path in sorted(tree_source.rglob("*")):
                if path.is_file() and not path.is_symlink():
                    entries.append(
                        ("target", f"{tree_destination}/{path.relative_to(tree_source).as_posix()}", path)
                    )
    for group in (kit / "skills", kit / "vendor/skills"):
        if not group.is_dir():
            continue
        for directory in sorted(group.iterdir()):
            if not directory.is_dir() or directory.is_symlink():
                continue
            for path in sorted(directory.rglob("*")):
                if path.is_file() and not path.is_symlink():
                    entries.append(
                        ("skills", f"{directory.name}/{path.relative_to(directory).as_posix()}", path)
                    )
    return entries


def file_class(kind: str, rel: str, source: Path, kit: Path) -> str:
    """Upgrade routing class for one published file: living, instance, pinned.

    living — the kit keeps a voice in this file across versions and the file
    carries rules agents read, so an adopter-modified copy is merged with the
    kit's new version. instance — a fill-once template the adopter owns once
    filled; kept. pinned — a snapshot that must stay byte-identical; adopter
    edits there are reported divergence, never merge input. seed — a file that
    runs as installed (CI workflows): even an unedited copy is live, so it is
    never replaced, merged, or deleted after install; template changes are
    reported.
    """
    if kind == "target" and rel.startswith(".github/workflows/"):
        return "seed"
    if kind == "skills":
        try:
            source.relative_to(kit / "vendor/skills")
        except ValueError:
            return "living"
        return "pinned"
    parts = rel.split("/")
    if len(parts) >= 2 and parts[0] == "docs" and (
        parts[1] in INSTANCE_DOC_STEMS or parts[1] in INSTANCE_DOC_DIRS
    ):
        return "instance"
    return "living"


def base_file_path(target: Path, kind: str, rel: str) -> Path:
    """Location of the installed-base snapshot for one published file."""
    return target / KIT_BASE_DIR / kind / rel


def write_installed_bytes(root: Path, destination: Path, content: bytes) -> None:
    """Atomically publish content with the installer's normalized file mode."""
    if not destination.parent.is_dir():
        make_directories(root, destination)
    else:
        contained_parent(root, destination)
    temporary = root / staging_file_name()
    try:
        temporary.write_bytes(content)
        os.chmod(temporary, INSTALLED_REGULAR_MODE)
        os.utime(temporary, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
        os.replace(temporary, destination)
    except OSError as error:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise InstallError(f"could not write {destination}: {error}") from error
    fsync_directory(destination.parent)


PLACEHOLDER = re.compile(r"\{[A-Za-z][^}]*\}")


def is_placeholder_line(line: str) -> bool:
    """A line that holds only placeholders and markup, no rule text."""
    if not PLACEHOLDER.search(line):
        return False
    return not any(character.isalnum() for character in PLACEHOLDER.sub("", line))


def without_placeholder_rewording(base: Path, other: Path) -> bytes:
    """The kit's new version with placeholder-only rewordings reverted to base."""
    base_lines = base.read_text(encoding="utf-8").splitlines(keepends=True)
    other_lines = other.read_text(encoding="utf-8").splitlines(keepends=True)
    result: list[str] = []
    matcher = difflib.SequenceMatcher(None, base_lines, other_lines, autojunk=False)
    for tag, base_start, base_end, other_start, other_end in matcher.get_opcodes():
        old, new = base_lines[base_start:base_end], other_lines[other_start:other_end]
        if tag == "replace" and all(map(is_placeholder_line, old + new)):
            result.extend(old)
        else:
            result.extend(new)
    return "".join(result).encode("utf-8")


def three_way_merge(current: Path, base: Path, other: Path) -> tuple[bytes | None, bool]:
    """Merge the kit's new version with adopter edits via git merge-file.

    current is the adopter's file (never modified), base the installed-base
    snapshot, other the new kit version. Returns (merged bytes, conflicts?)
    or (None, False) when the merge cannot be attempted — the caller then
    keeps the adopter file and reports a hand-merge, exactly as before this
    mechanism existed.

    A kit change that only rewords placeholder lines is dropped first: the
    adopter has usually filled those lines, so the rewording would conflict
    and hold back every other kit change in the file.
    """
    staged_other = base.parent / staging_file_name()
    try:
        staged_other.write_bytes(without_placeholder_rewording(base, other))
        result = subprocess.run(
            ["git", "merge-file", "-p", "-L", "your copy", "-L", "installed base",
             "-L", "new kit version", str(current), str(base), str(staged_other)],
            capture_output=True, check=False,
        )
    except (OSError, UnicodeDecodeError):
        return None, False
    finally:
        with contextlib.suppress(OSError):
            staged_other.unlink()
    if result.returncode < 0 or result.returncode > 127:
        return None, False
    return result.stdout, result.returncode != 0


def remove_empty_parents(root: Path, directory: Path) -> None:
    """Remove directories left empty by a deletion, stopping below root."""
    root = root.absolute()
    directory = directory.absolute()
    while directory != root and root in directory.parents:
        try:
            directory.rmdir()
        except OSError:
            break
        directory = directory.parent
    fsync_directory(directory)


def load_manifest(manifest_path: Path) -> dict:
    try:
        manifest = json.loads(read_text_guarded(manifest_path))
    except json.JSONDecodeError as error:
        raise InstallError(f"invalid install manifest {manifest_path}: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("version") not in (1, 2, MANIFEST_VERSION):
        raise InstallError(f"unsupported install manifest: {manifest_path}")
    return manifest


def write_json_atomic(target: Path, name: str, document: dict) -> None:
    temporary = target / staging_file_name()
    try:
        temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n")
        os.chmod(temporary, INSTALLED_REGULAR_MODE)
        os.utime(temporary, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
        os.replace(temporary, target / name)
    except OSError as error:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise InstallError(f"could not write {target / name}: {error}") from error
    finally:
        with contextlib.suppress(OSError):
            temporary.unlink()
    fsync_directory(target)


def write_manifest(target: Path, skills_dir: Path, kit_version: str,
                   added_target: list[str], added_skills: list[str], kit: Path | None = None,
                   unchanged_target: list[str] | None = None) -> None:
    """Merge the just-added file identities into the install manifest.

    The manifest records only files the installer published; anything already
    on the target before installation stays absent and is never touched by an
    upgrade. Each recorded file carries its routing class and the base
    content the kit laid down, so a later upgrade can three-way merge the
    kit's new version with adopter edits instead of forcing a whole-file
    hand-merge. The base lives inside the manifest: one self-contained file
    in the adopter's tree, no snapshot directory.
    """
    manifest_path = target / KIT_MANIFEST_MARKER
    manifest: dict = {"version": MANIFEST_VERSION, "kit": kit_version, "target": {}, "skills": {}}
    if manifest_path.exists():
        try:
            existing = json.loads(read_text_guarded(manifest_path))
            if isinstance(existing, dict) and existing.get("version") == MANIFEST_VERSION:
                manifest["target"] = dict(existing.get("target", {}))
                previous_skills = existing.get("skills", {})
                if same_skills_root(previous_skills.get("root"), target, skills_dir):
                    manifest["skills"] = dict(previous_skills.get("files", {}))
        except json.JSONDecodeError:
            pass
    for rel in added_target:
        manifest["target"][rel] = {
            "class": file_class("target", rel, target / rel, kit or target),
            "base": (target / rel).read_text(encoding="utf-8"),
        }
    # An existing file identical to the kit's content is adopted into the
    # manifest with the same anchor, so later upgrades manage it — a
    # re-establishment install must not leave untouched kit files untracked.
    for rel in unchanged_target or []:
        if rel in manifest["target"]:
            continue
        manifest["target"][rel] = {
            "class": file_class("target", rel, target / rel, kit or target),
            "base": (target / rel).read_text(encoding="utf-8"),
        }
    skill_files: dict = manifest["skills"]
    for rel in added_skills:
        source = kit_skill_source(kit, rel) if kit else skills_dir / rel
        skill_files[rel] = {
            "class": file_class("skills", rel, source, kit or target),
            "base": (skills_dir / rel).read_text(encoding="utf-8"),
        }
    write_json_atomic(target, KIT_MANIFEST_MARKER, {
        "version": MANIFEST_VERSION,
        "kit": kit_version,
        "target": manifest["target"],
        "skills": {"root": skills_root_record(target, skills_dir), "files": skill_files},
    })


def skills_root_record(target: Path, skills_dir: Path) -> str:
    """The skills root as the manifest records it: relative when inside the target."""
    try:
        return skills_dir.absolute().relative_to(target.absolute()).as_posix()
    except ValueError:
        return str(skills_dir)


def same_skills_root(recorded: object, target: Path, skills_dir: Path) -> bool:
    """Whether a recorded skills root names this skills directory.

    Older manifests stored an absolute path, which a clone or moved checkout
    no longer matches; the same in-repository suffix still identifies it.
    """
    if not isinstance(recorded, str):
        return False
    current = skills_root_record(target, skills_dir)
    if recorded in (current, str(skills_dir)):
        return True
    return (not Path(current).is_absolute() and Path(recorded).is_absolute()
            and recorded.endswith("/" + current))


def kit_skill_source(kit: Path, rel: str) -> Path:
    """Locate a published skill file's kit source (skills/ or vendor/skills/)."""
    head, _, rest = rel.partition("/")
    for group in ("skills", "vendor/skills"):
        candidate = kit / group / head / rest
        if candidate.is_file():
            return candidate
    return kit / "skills" / rel


def run_upgrade(kit: Path, target: Path, skills_dir: Path, kit_version: str,
                dry_run: bool, stream: TextIO, adopt: Sequence[str] = (),
                resolved: Sequence[str] = ()) -> int:
    """Content-anchored upgrade against the recorded install manifest.

    Each manifest entry carries the base content the kit last laid down. A
    file still matching its base is an untouched kit copy and is replaced,
    or deleted when the kit no longer ships it;
    a diverged living file is three-way merged with the kit's new version;
    filled template instances and pinned snapshots are never merged. Merged
    files re-anchor on the new kit version so the next upgrade merges again
    instead of replacing. Legacy manifest versions degrade conservatively:
    nothing adopter-modified is written without an anchor.

    Adopted paths (--adopt) transfer ownership to the adopter: the kit never
    writes, merges, or re-adds them. A present adopted file is reported only
    when the kit template changed upstream; an absent one is silent.

    Resolved paths (--resolved) were merged by hand against this kit version:
    the file is kept as it is, its base re-anchors on the new kit version, any
    adoption ends, and its conflict file is removed, so the next upgrade merges
    from here instead of conflicting again.
    """
    manifest_path = target / KIT_MANIFEST_MARKER
    if not manifest_path.exists():
        print(
            "No .sdlc-kit-manifest.json found: this install predates manifest-based upgrades.\n"
            "Nothing was changed. Follow INSTALL.md 'Upgrade an existing installation' for the\n"
            "one-time manual path; later upgrades will then run automatically.",
            file=stream,
        )
        return 0
    manifest = load_manifest(manifest_path)
    manifest_version = manifest.get("version")
    old_by_kind = {"target": dict(manifest.get("target", {})), "skills": {}}
    if same_skills_root(manifest.get("skills", {}).get("root"), target, skills_dir):
        old_by_kind["skills"] = dict(manifest.get("skills", {}).get("files", {}))

    actions: dict[str, list[str]] = {"add": [], "update": [], "current": [], "merged": [],
                                     "conflict": [], "modified": [], "removed": [],
                                     "deleted": [], "adopted": [], "resolved": [], "legacy": []}
    adopt_set = {item.strip() for item in adopt if item.strip()}
    resolved_set = {item.strip() for item in resolved if item.strip()}
    resolved_paths: list[Path] = []
    if adopt_set & resolved_set:
        raise InstallError("a path cannot be both --adopt and --resolved: "
                           + ", ".join(sorted(adopt_set & resolved_set)))
    kept_detail: dict[str, str] = {}
    conflict_regions: dict[str, int] = {}
    plan: list[tuple[str, Path, Path]] = []
    merge_writes: list[tuple[str, Path, bytes]] = []
    deletions: list[tuple[str, Path]] = []
    conflict_writes: list[tuple[str, Path, bytes]] = []
    new_entries: dict[str, dict[str, object]] = {"target": {}, "skills": {}}
    seen: dict[str, set[str]] = {"target": set(), "skills": set()}

    def conflict_sibling(destination: Path) -> Path:
        return destination.parent / (destination.name + ".sdlc-conflict")

    for kind, rel, source in payload_entries(kit):
        seen[kind].add(rel)
        destination = (target if kind == "target" else skills_dir) / rel
        new_text = source.read_text(encoding="utf-8")
        new_bytes = new_text.encode("utf-8")
        klass = file_class(kind, rel, source, kit)
        entry = old_by_kind[kind].get(rel)
        installed_bytes: bytes | None = None
        if destination.is_file() and not destination.is_symlink():
            installed_bytes = destination.read_bytes()
        if rel in resolved_set:
            if installed_bytes is None:
                raise InstallError(f"--resolved file does not exist: {rel}")
            if b"<<<<<<< your copy" in installed_bytes or b">>>>>>> new kit version" in installed_bytes:
                raise InstallError(f"--resolved file still has conflict markers: {rel}")
            actions["resolved"].append(rel)
            resolved_paths.append(destination)
            new_entries[kind][rel] = {"class": klass, "base": new_text}
            continue
        if rel in adopt_set or (isinstance(entry, dict) and entry.get("adopted")):
            newly_adopted = rel in adopt_set
            if installed_bytes is None:
                new_entries[kind][rel] = {"class": klass, "base": None, "adopted": True}
            else:
                old_base = entry.get("base") if isinstance(entry, dict) else None
                new_entries[kind][rel] = {"class": klass, "base": new_text, "adopted": True}
                if not newly_adopted and old_base != new_text:
                    kept_detail[rel] = " (adopted; kit template changed upstream)"
                    actions["adopted"].append(rel)
            if newly_adopted:
                actions["adopted"].append(rel)
            continue
        if installed_bytes is None:
            actions["add"].append(rel)
            plan.append((kind, destination, source))
            new_entries[kind][rel] = {"class": klass, "base": new_text}
            continue
        if installed_bytes == new_bytes:
            actions["current"].append(rel)
            new_entries[kind][rel] = {"class": klass, "base": new_text}
            continue
        if klass == "seed":
            kept_detail[rel] = " (CI workflow, never replaced: compare with the new template by hand)"
            actions["modified"].append(rel)
            new_entries[kind][rel] = {"class": klass, "base": new_text}
            continue
        # v3 entries carry the base anchor; legacy records (plain hashes — and
        # v2 records, which could conflate adopter content with kit content)
        # get no merge and no wholesale write.
        base_text: str | None = None
        if isinstance(entry, dict) and isinstance(entry.get("base"), str):
            base_text = entry["base"]
        if base_text is not None:
            entry_dict = entry if isinstance(entry, dict) else {}
            base_bytes = base_text.encode("utf-8")
            if installed_bytes == base_bytes:
                actions["update"].append(rel)
                plan.append((kind, destination, source))
                new_entries[kind][rel] = {"class": klass, "base": new_text}
                continue
            if klass != "living" or base_bytes == new_bytes:
                if klass == "instance" and base_bytes != new_bytes:
                    kept_detail[rel] = " (instance: kit template changed upstream)"
                elif klass == "pinned":
                    kept_detail[rel] = " (pinned snapshot diverges from its pin)"
                elif base_bytes == new_bytes:
                    kept_detail[rel] = " (adopter edit; kit unchanged)"
                actions["modified"].append(rel)
                new_entries[kind][rel] = entry_dict
                continue
            staged_base = target / staging_file_name()
            try:
                staged_base.write_bytes(base_bytes)
                merged, conflicts = three_way_merge(destination, staged_base, source)
            finally:
                with contextlib.suppress(OSError):
                    staged_base.unlink()
            if merged is not None and not conflicts:
                actions["merged"].append(rel)
                merge_writes.append((kind, destination, merged))
                new_entries[kind][rel] = {"class": klass, "base": new_text}
                continue
            if merged is not None:
                actions["conflict"].append(rel)
                conflict_regions[rel] = merged.count(b"<<<<<<< your copy")
                conflict_writes.append((kind, destination, merged))
                new_entries[kind][rel] = entry_dict
                continue
            kept_detail[rel] = " (no usable merge; hand-merge advised)"
            actions["modified"].append(rel)
            new_entries[kind][rel] = entry_dict
            continue
        if (isinstance(entry, str) and manifest_version == 1
                and hashlib.sha256(installed_bytes).hexdigest() == entry):
            # v1 recorded install-time kit content and has never been rewritten
            # by a keep, so hash equality still means an untouched kit copy.
            actions["update"].append(rel)
            plan.append((kind, destination, source))
            new_entries[kind][rel] = {"class": klass, "base": new_text}
            continue
        if entry is None:
            kept_detail[rel] = " (not tracked by the install manifest; re-establish with the\n    " \
                "one-time manual path to manage it)"
        else:
            kept_detail[rel] = (
                " (manifest version 2 records are unreliable; verify against the new kit version by hand)"
                if manifest_version == 2 else " (manifest predates installed-base anchors)"
            )
        actions["modified"].append(rel)
        new_entries[kind][rel] = {"class": klass, "base": None}
    # A file the kit no longer ships is deleted only when it still matches the
    # base the kit laid down; edited, adopted, or unanchored files stay.
    for kind in ("target", "skills"):
        root = target if kind == "target" else skills_dir
        for rel in sorted(set(old_by_kind[kind]) - seen[kind]):
            destination = root / rel
            if not os.path.lexists(destination):
                continue
            entry = old_by_kind[kind][rel]
            label = rel + (" (skills)" if kind == "skills" else "")
            base = entry.get("base") if isinstance(entry, dict) else None
            if isinstance(entry, dict) and entry.get("adopted"):
                kept_detail[label] = " (adopted)"
            elif kind == "target" and file_class(kind, rel, destination, kit) == "seed":
                kept_detail[label] = " (CI workflow, never deleted)"
            elif (isinstance(base, str) and destination.is_file() and not destination.is_symlink()
                  and destination.read_bytes() == base.encode("utf-8")):
                actions["deleted"].append(label)
                deletions.append((kind, destination))
                continue
            else:
                kept_detail[label] = (" (adopter-modified)" if isinstance(base, str)
                                      else " (no installed-base anchor)")
            actions["removed"].append(label)

    unknown = sorted((adopt_set | resolved_set) - (seen["target"] | seen["skills"]))
    if unknown:
        raise InstallError(
            "--adopt or --resolved target is not part of the kit payload: " + ", ".join(unknown))

    # Older installers wrote .sdlc-vendor/ metadata into skill directories
    # without recording it in the manifest. The name is the kit's own, so any
    # copy under the skills root is legacy kit output.
    legacy_vendor: list[Path] = []
    if skills_dir.is_dir():
        for skill in sorted(skills_dir.iterdir()):
            metadata = skill / ".sdlc-vendor"
            if (not skill.is_symlink() and skill.is_dir() and metadata.is_dir()
                    and not metadata.is_symlink()):
                legacy_vendor.append(metadata)
                actions["legacy"].append(f"{skill.name}/.sdlc-vendor/")

    label = "DRY RUN — no files will be written" if dry_run else "Upgrade"
    print(f"{label}: {len(actions['update'])} updated, {len(actions['add'])} added, "
          f"{len(actions['current'])} current, {len(actions['merged'])} merged, "
          f"{len(actions['conflict'])} conflicts, {len(actions['modified'])} kept "
          f"(adopter-modified), {len(actions['adopted'])} adopted, "
          f"{len(actions['resolved'])} resolved, "
          f"{len(actions['deleted'])} deleted and {len(actions['removed'])} kept of those "
          f"removed upstream", file=stream)
    for rel in actions["adopted"]:
        print(f"  A {rel}{kept_detail.get(rel, ' (adopted — kit will not write this path)')}",
              file=stream)
    for rel in actions["resolved"]:
        print(f"  R {rel} (resolved — kit manages it again from this version)", file=stream)
    for rel in actions["add"]:
        print(f"  + {rel}", file=stream)
    for rel in actions["update"]:
        print(f"  ~ {rel}", file=stream)
    for rel in actions["merged"]:
        print(f"  M {rel} (merged — review the hunks)", file=stream)
    for rel in actions["conflict"]:
        print(f"  C {rel} (conflict — your copy kept; {rel}.sdlc-conflict has every kit change "
              f"merged, with {conflict_regions.get(rel, 0)} region(s) marked to resolve)", file=stream)
    for rel in actions["modified"]:
        print(f"  ! kept, adopter-modified{kept_detail.get(rel, '')}: {rel}", file=stream)
    for rel in actions["deleted"]:
        print(f"  - {rel} (removed upstream, untouched)", file=stream)
    for rel in actions["removed"]:
        print(f"  ! left in place, removed upstream{kept_detail.get(rel, '')}: {rel}", file=stream)
    for rel in actions["legacy"]:
        print(f"  - {rel} (legacy kit metadata)", file=stream)
    if dry_run:
        return 0

    for kind, destination, source in plan:
        root = target if kind == "target" else skills_dir
        if not destination.parent.exists():
            make_directories(root, destination)
        else:
            contained_parent(root, destination)
        if os.path.lexists(destination):
            replace_file(source, destination)
        else:
            result = publish_file(root, source, destination)
            if result != "added":
                raise InstallError(f"unexpected publication result for {destination}: {result}")
        with contextlib.suppress(OSError):
            conflict_sibling(destination).unlink()
    for kind, destination, content in merge_writes:
        write_installed_bytes(target if kind == "target" else skills_dir, destination, content)
        with contextlib.suppress(OSError):
            conflict_sibling(destination).unlink()
    for kind, destination, content in conflict_writes:
        write_installed_bytes(target if kind == "target" else skills_dir,
                              conflict_sibling(destination), content)
    for destination in resolved_paths:
        with contextlib.suppress(OSError):
            conflict_sibling(destination).unlink()
    for metadata in legacy_vendor:
        try:
            shutil.rmtree(metadata)
        except OSError as error:
            raise InstallError(f"could not remove legacy metadata {metadata}: {error}") from error
        remove_empty_parents(skills_dir, metadata.parent)
    for kind, destination in deletions:
        root = target if kind == "target" else skills_dir
        contained_parent(root, destination)
        try:
            destination.unlink()
        except FileNotFoundError:
            pass
        except OSError as error:
            raise InstallError(f"could not delete {destination}: {error}") from error
        remove_empty_parents(root, destination.parent)
    # The v2 snapshot directory is obsolete; its content now lives in the manifest.
    legacy_dir = target / KIT_BASE_DIR
    if legacy_dir.is_dir() and not legacy_dir.is_symlink():
        try:
            shutil.rmtree(legacy_dir)
        except OSError as error:
            raise InstallError(f"could not remove the obsolete {KIT_BASE_DIR}/ directory: {error}") from error

    write_json_atomic(target, KIT_MANIFEST_MARKER, {
        "version": MANIFEST_VERSION,
        "kit": kit_version,
        "target": new_entries["target"],
        "skills": {"root": skills_root_record(target, skills_dir), "files": new_entries["skills"]},
    })

    marker = target / KIT_VERSION_MARKER
    temporary = target / staging_file_name()
    try:
        temporary.write_text(kit_version + "\n")
        os.chmod(temporary, INSTALLED_REGULAR_MODE)
        os.utime(temporary, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
        os.replace(temporary, marker)
    except OSError as error:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise InstallError(f"could not update the version marker: {error}") from error
    finally:
        with contextlib.suppress(OSError):
            temporary.unlink()
    fsync_directory(target)
    return 0


def open_verified_root(path: Path, create: bool) -> Path:
    reject_linebreaks(str(path))
    if path == Path(path.anchor) or path.absolute() == Path(path.absolute().anchor):
        raise InstallError("installation root must not be the filesystem root")
    if path.is_symlink():
        raise InstallError(f"root must not be a symlink: {path}")
    if create and not path.exists():
        try:
            path.mkdir(parents=True)
            os.chmod(path, INSTALLED_DIRECTORY_MODE)
        except OSError as error:
            raise InstallError(f"could not create root: {path}") from error
    if path.exists():
        try:
            entry = path.lstat()
        except OSError as error:
            raise InstallError(f"could not inspect root: {path}") from error
        if stat.S_ISLNK(entry.st_mode) or not stat.S_ISDIR(entry.st_mode):
            raise InstallError(f"root must be a real directory: {path}")
    elif not create:
        # Tolerated for dry-run prediction; creation is the caller's explicit choice.
        return path
    return path


def probe_writable(root: Path) -> None:
    probe = root / staging_file_name()
    try:
        probe.write_text("")
        probe.unlink()
    except OSError as error:
        raise InstallError(f"root is not writable: {root} ({error})") from error


def command_source(arguments: argparse.Namespace) -> None:
    path = Path(arguments.path)
    try:
        entry = path.lstat()
    except OSError as error:
        raise InstallError(f"could not inspect source: {path}") from error
    if stat.S_ISLNK(entry.st_mode):
        raise InstallError(f"source must not be a symlink: {path}")
    if not (stat.S_ISREG(entry.st_mode) or stat.S_ISDIR(entry.st_mode)):
        raise InstallError(f"source must be a regular file or directory: {path}")


def command_root(arguments: argparse.Namespace) -> None:
    open_verified_root(Path(arguments.path), arguments.create)


def command_check(arguments: argparse.Namespace) -> None:
    root = open_verified_root(Path(arguments.path), create=False)
    if arguments.write_probe:
        probe_writable(root)


def command_file(arguments: argparse.Namespace) -> None:
    print(publish_file(Path(arguments.root), Path(arguments.source), Path(arguments.destination)))


def command_same(arguments: argparse.Namespace) -> None:
    """Report whether source and destination file contents are identical."""
    source = Path(arguments.source)
    destination = Path(arguments.destination)
    try:
        identical = (
            destination.is_file()
            and not destination.is_symlink()
            and source.read_bytes() == destination.read_bytes()
        )
    except OSError as error:
        raise InstallError(f"could not compare {source} with {destination}: {error}") from error
    print("identical" if identical else "differs")


def command_tree(arguments: argparse.Namespace) -> None:
    print(publish_tree(Path(arguments.root), Path(arguments.source), Path(arguments.destination)))


def command_clean(arguments: argparse.Namespace) -> None:
    root = Path(arguments.root)
    directory = Path(arguments.directory)
    # Matches the original semantics: clean runs before the copies, so missing
    # publication parents are created (validated, no symlinks) and then swept.
    parent = make_directories(root, directory / ".sdlc-clean-staging")
    lock = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        clean_stale_staging(parent)
    finally:
        os.close(lock)


def command_version(arguments: argparse.Namespace) -> None:
    target = open_verified_root(Path(arguments.root), create=False)
    marker = target / KIT_VERSION_MARKER
    existing = "replaced" if marker.exists() else "created"
    if arguments.dry_run:
        print(existing + " (dry run)")
        return
    lock = os.open(target, os.O_RDONLY | os.O_DIRECTORY)
    try:
        fcntl.flock(lock, fcntl.LOCK_EX)
        clean_stale_staging(target)
        temporary = target / staging_file_name()
        try:
            temporary.write_text(arguments.value + "\n")
            os.chmod(temporary, INSTALLED_REGULAR_MODE)
            os.utime(temporary, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
            os.replace(temporary, marker)
        except OSError as error:
            with contextlib.suppress(OSError):
                temporary.unlink()
            raise InstallError(f"could not write the version marker: {error}") from error
        finally:
            with contextlib.suppress(OSError):
                temporary.unlink()
        fsync_directory(target)
    finally:
        os.close(lock)
    print(existing)


def command_manifest(arguments: argparse.Namespace) -> None:
    target = open_verified_root(Path(arguments.target), create=False)
    skills_dir = Path(arguments.skills_root)
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as error:
        raise InstallError(f"invalid manifest payload: {error}") from error
    if not isinstance(payload, dict):
        raise InstallError("manifest payload must be a JSON object")
    write_manifest(
        target,
        skills_dir,
        arguments.kit_version,
        [str(item) for item in payload.get("target", [])],
        [str(item) for item in payload.get("skills", [])],
        kit=Path(payload["kit"]) if payload.get("kit") else None,
        unchanged_target=[str(item) for item in payload.get("target_unchanged", [])],
    )
    print("manifest written")


def command_upgrade(arguments: argparse.Namespace) -> None:
    kit = Path(arguments.kit)
    target = open_verified_root(Path(arguments.target), create=False)
    skills_dir = open_verified_root(Path(arguments.skills_dir), create=True)
    version = arguments.kit_version or kit_version_of(kit)
    adopt = tuple(arguments.adopt or ())
    resolved = tuple(arguments.resolved or ())
    raise SystemExit(run_upgrade(kit, target, skills_dir, version, arguments.dry_run,
                                 sys.stdout, adopt=adopt, resolved=resolved))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    source_parser = subparsers.add_parser("source")
    source_parser.add_argument("path")
    source_parser.set_defaults(handler=command_source)
    file_parser = subparsers.add_parser("file")
    file_parser.add_argument("root")
    file_parser.add_argument("source")
    file_parser.add_argument("destination")
    file_parser.set_defaults(handler=command_file)
    root_parser = subparsers.add_parser("root")
    root_parser.add_argument("path")
    root_parser.add_argument("--create", action="store_true")
    root_parser.set_defaults(handler=command_root)
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("path")
    check_parser.add_argument("--write-probe", action="store_true")
    check_parser.set_defaults(handler=command_check)
    version_parser = subparsers.add_parser("version")
    version_parser.add_argument("root")
    version_parser.add_argument("value")
    version_parser.add_argument("--dry-run", action="store_true")
    version_parser.set_defaults(handler=command_version)
    clean_parser = subparsers.add_parser("clean")
    clean_parser.add_argument("root")
    clean_parser.add_argument("directory")
    clean_parser.set_defaults(handler=command_clean)
    tree_parser = subparsers.add_parser("tree")
    tree_parser.add_argument("root")
    tree_parser.add_argument("source")
    tree_parser.add_argument("destination")
    tree_parser.set_defaults(handler=command_tree)
    manifest_parser = subparsers.add_parser("manifest")
    manifest_parser.add_argument("--target", required=True)
    manifest_parser.add_argument("--skills-root", required=True)
    manifest_parser.add_argument("--kit-version", required=True)
    manifest_parser.set_defaults(handler=command_manifest)
    same_parser = subparsers.add_parser("same")
    same_parser.add_argument("source")
    same_parser.add_argument("destination")
    same_parser.set_defaults(handler=command_same)
    upgrade_parser = subparsers.add_parser("upgrade")
    upgrade_parser.add_argument("--kit", required=True)
    upgrade_parser.add_argument("--target", required=True)
    upgrade_parser.add_argument("--skills-dir", required=True)
    upgrade_parser.add_argument("--kit-version", default=None)
    upgrade_parser.add_argument("--dry-run", action="store_true")
    upgrade_parser.add_argument("--adopt", action="append", default=[],
                                metavar="FILE",
                                help="mark a kit payload path adopter-owned: never "
                                     "written, merged, or re-added by later upgrades")
    upgrade_parser.add_argument("--resolved", action="append", default=[],
                                metavar="FILE",
                                help="FILE was merged by hand against this kit version: keep "
                                     "it, re-anchor its base, end any adoption, and remove "
                                     "its conflict file")
    upgrade_parser.set_defaults(handler=command_upgrade)
    return parser


def main() -> None:
    arguments = build_parser().parse_args()
    try:
        arguments.handler(arguments)
    except (InstallError, OSError, ValueError) as error:
        print(f"install-safe: {error}", file=sys.stderr)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()
