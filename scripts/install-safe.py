#!/usr/bin/env python3
"""Descriptor-relative, no-clobber publication for install.sh."""

from __future__ import annotations

import argparse
import ctypes
import errno
import fcntl
import hashlib
import os
import re
import secrets
import stat
import sys
from pathlib import Path
from typing import Any, BinaryIO

if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
    raise RuntimeError("safe installation requires O_DIRECTORY and O_NOFOLLOW support")
OPEN_DIRECTORY = os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
OPEN_NOFOLLOW = os.O_NOFOLLOW
INSTALLING_MARKER = ".sdlc-installing"
INSTALLING_MARKER_CONTENT = b"sdlc-install-v1\n"
INSTALLING_INTENT = ".sdlc-staging-intent"
INSTALLED_DIRECTORY_MODE = 0o755
INSTALLED_REGULAR_MODE = 0o644
INSTALLED_EXECUTABLE_MODE = 0o755
NORMALIZED_TIMESTAMP_NS = 0
STAGING_NAME_RE = re.compile(
    r"^(?:\.sdlc-file-[0-9a-f]{24}|\.sdlc-skill-[a-z0-9](?:[a-z0-9._-]{0,38}[a-z0-9])?-[0-9a-f]{24})$"
)


def contained_parts(allowed_root: Path, destination: Path) -> tuple[list[str], str]:
    root = os.path.abspath(os.fspath(allowed_root))
    target = os.path.abspath(os.fspath(destination))
    try:
        common = os.path.commonpath((root, target))
    except ValueError as error:
        raise ValueError(f"destination is outside allowed root: {destination}") from error
    if common != root or target == root:
        raise ValueError(f"destination is outside allowed root: {destination}")
    relative = os.path.relpath(target, root)
    parts = relative.split(os.sep)
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsafe destination: {destination}")
    return parts[:-1], parts[-1]


def open_child_directory(parent_fd: int, name: str, create: bool) -> int:
    flags = OPEN_DIRECTORY | OPEN_NOFOLLOW
    try:
        return os.open(name, flags, dir_fd=parent_fd)
    except FileNotFoundError:
        if not create:
            raise
    try:
        os.mkdir(name, mode=0o755, dir_fd=parent_fd)
    except FileExistsError:
        return os.open(name, flags, dir_fd=parent_fd)
    return os.open(name, flags, dir_fd=parent_fd)


def open_directory_path(path: Path, create: bool) -> tuple[int, bool]:
    """Open a path one component at a time without following ancestor symlinks."""
    absolute = Path(os.path.abspath(os.fspath(path)))
    current_fd = os.open(absolute.anchor, OPEN_DIRECTORY | OPEN_NOFOLLOW)
    try:
        for part in absolute.parts[1:]:
            sync_parent = False
            try:
                next_fd = open_child_directory(current_fd, part, create=False)
            except FileNotFoundError:
                if not create:
                    return current_fd, False
                next_fd = open_child_directory(current_fd, part, create=True)
                sync_parent = True
            if sync_parent:
                try:
                    os.fsync(current_fd)
                except BaseException:
                    os.close(next_fd)
                    raise
            os.close(current_fd)
            current_fd = next_fd
        return current_fd, True
    except BaseException:
        os.close(current_fd)
        raise


def prepare_directory_root(root: Path, create: bool) -> None:
    absolute_root = Path(os.path.abspath(os.fspath(root)))
    if absolute_root == Path(absolute_root.anchor):
        raise ValueError("installation root must not be the filesystem root")
    directory_fd, _ = open_directory_path(absolute_root, create)
    os.close(directory_fd)


def open_parent_directory(allowed_root: Path, destination: Path) -> tuple[int, str]:
    parents, name = contained_parts(allowed_root, destination)
    current_fd, complete = open_directory_path(allowed_root, create=False)
    if not complete:
        os.close(current_fd)
        raise FileNotFoundError(f"allowed root does not exist: {allowed_root}")
    try:
        for part in parents:
            sync_parent = False
            try:
                next_fd = open_child_directory(current_fd, part, create=False)
            except FileNotFoundError:
                next_fd = open_child_directory(current_fd, part, create=True)
                sync_parent = True
            if sync_parent:
                try:
                    os.fsync(current_fd)
                except BaseException:
                    os.close(next_fd)
                    raise
            os.close(current_fd)
            current_fd = next_fd
        return current_fd, name
    except BaseException:
        os.close(current_fd)
        raise


def write_all(descriptor: int, content: bytes | memoryview) -> None:
    remaining = memoryview(content)
    while remaining:
        written = os.write(descriptor, remaining)
        if written <= 0:
            raise OSError("write returned no bytes")
        remaining = remaining[written:]


def read_bounded(descriptor: int, limit: int) -> bytes:
    content = bytearray()
    while len(content) < limit:
        chunk = os.read(descriptor, limit - len(content))
        if not chunk:
            break
        content.extend(chunk)
    return bytes(content)


def copy_stream(source: BinaryIO, destination_fd: int) -> None:
    while True:
        chunk = source.read(1024 * 1024)
        if not chunk:
            return
        write_all(destination_fd, chunk)


def normalized_file_mode(source_stat: os.stat_result) -> int:
    if stat.S_IMODE(source_stat.st_mode) & 0o111:
        return INSTALLED_EXECUTABLE_MODE
    return INSTALLED_REGULAR_MODE


def validate_source_file(source: Path) -> None:
    descriptor = os.open(
        source,
        os.O_RDONLY
        | OPEN_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0),
    )
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(f"installation source must be a regular file: {source}")
    finally:
        os.close(descriptor)


def copy_source_to_new_file(
    source: Path,
    parent_fd: int,
    name: str,
    fixed_mode: int | None = None,
) -> None:
    source_fd = os.open(
        source,
        os.O_RDONLY
        | OPEN_NOFOLLOW
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0),
    )
    try:
        source_stat = os.fstat(source_fd)
        if not stat.S_ISREG(source_stat.st_mode):
            raise ValueError(f"installation source must be a regular file: {source}")
        mode = fixed_mode if fixed_mode is not None else normalized_file_mode(source_stat)
        destination_fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | OPEN_NOFOLLOW,
            mode,
            dir_fd=parent_fd,
        )
        try:
            with os.fdopen(os.dup(source_fd), "rb") as source_file:
                copy_stream(source_file, destination_fd)
            os.fchmod(destination_fd, mode)
            os.utime(destination_fd, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
            os.fsync(destination_fd)
        finally:
            os.close(destination_fd)
    finally:
        os.close(source_fd)


def valid_staging_name(name: str) -> bool:
    return STAGING_NAME_RE.fullmatch(name) is not None


def skill_staging_prefix(name: str) -> str:
    label = re.sub(r"[^a-z0-9._-]", "-", name.lower())[:40].strip("._-")
    if not label:
        label = "skill"
    return f".sdlc-skill-{label}-"


def write_staging_intent(parent_fd: int, staging_name: str) -> None:
    if not valid_staging_name(staging_name):
        raise ValueError(f"invalid staging name for intent: {staging_name}")
    temporary_name = f"{INSTALLING_INTENT}.tmp-{secrets.token_hex(12)}"
    descriptor = os.open(
        temporary_name,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | OPEN_NOFOLLOW,
        0o600,
        dir_fd=parent_fd,
    )
    try:
        try:
            write_all(descriptor, staging_name.encode() + b"\n")
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        if not atomic_rename_noreplace(
            parent_fd,
            temporary_name,
            parent_fd,
            INSTALLING_INTENT,
        ):
            raise RuntimeError("staging intent already exists")
        os.fsync(parent_fd)
    except BaseException:
        try:
            os.unlink(temporary_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
        except FileNotFoundError:
            pass
        raise


def clear_staging_intent(parent_fd: int, missing_ok: bool = False) -> None:
    try:
        os.unlink(INSTALLING_INTENT, dir_fd=parent_fd)
    except FileNotFoundError:
        if missing_ok:
            return
        raise RuntimeError("staging intent disappeared")
    except OSError as error:
        raise RuntimeError("could not remove staging intent") from error
    os.fsync(parent_fd)


def validate_intent_recovery_state(staging_fd: int) -> tuple[int, int] | None:
    names = list_entries(staging_fd)
    if not names:
        return None
    if names != [INSTALLING_MARKER]:
        raise RuntimeError("staging intent target contains unexpected entries")
    try:
        marker_fd = os.open(INSTALLING_MARKER, os.O_RDONLY | OPEN_NOFOLLOW, dir_fd=staging_fd)
    except OSError as error:
        raise RuntimeError("staging intent marker is unreadable") from error
    try:
        marker_stat = os.fstat(marker_fd)
        marker_content = read_bounded(marker_fd, len(INSTALLING_MARKER_CONTENT) + 1)
    finally:
        os.close(marker_fd)
    if not stat.S_ISREG(marker_stat.st_mode) or marker_content != INSTALLING_MARKER_CONTENT:
        raise RuntimeError("staging intent marker is invalid")
    return marker_stat.st_dev, marker_stat.st_ino


def quarantine_intended_staging(
    parent_fd: int,
    staging_name: str,
    staging_fd: int,
) -> None:
    preserve_stale_staging(parent_fd, staging_name, staging_fd)


def recover_staging_intent(parent_fd: int) -> None:
    try:
        descriptor = os.open(INSTALLING_INTENT, os.O_RDONLY | OPEN_NOFOLLOW, dir_fd=parent_fd)
    except FileNotFoundError:
        return
    try:
        marker_stat = os.fstat(descriptor)
        content = read_bounded(descriptor, 256)
    finally:
        os.close(descriptor)
    try:
        staging_name = content.decode("ascii").removesuffix("\n")
    except UnicodeError as error:
        raise RuntimeError("invalid staging intent encoding") from error
    if not stat.S_ISREG(marker_stat.st_mode) or content != staging_name.encode() + b"\n" or not valid_staging_name(staging_name):
        raise RuntimeError("invalid staging intent")
    try:
        staging_fd = open_child_directory(parent_fd, staging_name, create=False)
    except FileNotFoundError:
        clear_staging_intent(parent_fd)
        return
    try:
        validate_intent_recovery_state(staging_fd)
        quarantine_intended_staging(parent_fd, staging_name, staging_fd)
    finally:
        os.close(staging_fd)
    clear_staging_intent(parent_fd)


def create_staging_wrapper(parent_fd: int, prefix: str) -> tuple[str, int]:
    staging_name = f"{prefix}{secrets.token_hex(12)}"
    write_staging_intent(parent_fd, staging_name)
    try:
        os.mkdir(staging_name, mode=0o700, dir_fd=parent_fd)
    except OSError as error:
        clear_staging_intent(parent_fd)
        raise RuntimeError(f"could not create private staging directory: {staging_name}") from error
    try:
        staging_fd = open_child_directory(parent_fd, staging_name, create=False)
    except BaseException:
        cleanup_succeeded = False
        try:
            os.rmdir(staging_name, dir_fd=parent_fd)
            os.fsync(parent_fd)
            cleanup_succeeded = True
        except BaseException:
            pass
        finally:
            if cleanup_succeeded:
                clear_staging_intent(parent_fd, missing_ok=True)
        raise
    try:
        marker_fd = os.open(
            INSTALLING_MARKER,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | OPEN_NOFOLLOW,
            0o600,
            dir_fd=staging_fd,
        )
        try:
            write_all(marker_fd, INSTALLING_MARKER_CONTENT)
            os.fsync(marker_fd)
        finally:
            os.close(marker_fd)
        os.fsync(staging_fd)
        os.fsync(parent_fd)
        clear_staging_intent(parent_fd)
        return staging_name, staging_fd
    except BaseException:
        cleanup_succeeded = False
        try:
            remove_staging_directory(parent_fd, staging_name, staging_fd)
            os.fsync(parent_fd)
            cleanup_succeeded = True
        except BaseException:
            pass
        finally:
            os.close(staging_fd)
            if cleanup_succeeded:
                clear_staging_intent(parent_fd, missing_ok=True)
        raise


def recover_stale_staging(parent_fd: int) -> None:
    recover_staging_intent(parent_fd)
    for name in list_entries(parent_fd):
        if not name.startswith((".sdlc-file-", ".sdlc-skill-")):
            continue
        try:
            staging_fd = open_child_directory(parent_fd, name, create=False)
        except (FileNotFoundError, NotADirectoryError, OSError):
            continue
        owned = False
        try:
            try:
                marker_fd = os.open(INSTALLING_MARKER, os.O_RDONLY | OPEN_NOFOLLOW, dir_fd=staging_fd)
            except (FileNotFoundError, OSError):
                continue
            try:
                marker_stat = os.fstat(marker_fd)
                owned = (
                    stat.S_ISREG(marker_stat.st_mode)
                    and read_bounded(marker_fd, len(INSTALLING_MARKER_CONTENT) + 1)
                    == INSTALLING_MARKER_CONTENT
                )
            finally:
                os.close(marker_fd)
            if owned:
                preserve_stale_staging(parent_fd, name, staging_fd)
        finally:
            os.close(staging_fd)


def lock_and_recover_parent(parent_fd: int) -> None:
    fcntl.flock(parent_fd, fcntl.LOCK_EX)
    recover_stale_staging(parent_fd)


def publish_file(allowed_root: Path, source: Path, destination: Path) -> bool:
    parent_fd, name = open_parent_directory(allowed_root, destination)
    try:
        lock_and_recover_parent(parent_fd)
        staging_name, staging_fd = create_staging_wrapper(parent_fd, ".sdlc-file-")
    except BaseException:
        os.close(parent_fd)
        raise
    try:
        copy_source_to_new_file(source, staging_fd, "payload")
        try:
            os.link(
                "payload",
                name,
                src_dir_fd=staging_fd,
                dst_dir_fd=parent_fd,
                follow_symlinks=False,
            )
        except FileExistsError:
            return False
        os.fsync(parent_fd)
        return True
    finally:
        try:
            remove_staging_directory(parent_fd, staging_name, staging_fd)
            os.fsync(parent_fd)
        finally:
            os.close(staging_fd)
            os.close(parent_fd)


def copy_regular_entry(source_fd: int, destination_fd: int, name: str) -> None:
    opened_source = os.open(name, os.O_RDONLY | os.O_NONBLOCK | OPEN_NOFOLLOW, dir_fd=source_fd)
    try:
        source_stat = os.fstat(opened_source)
        if not stat.S_ISREG(source_stat.st_mode):
            raise ValueError(f"source entry changed type during copy: {name}")
        mode = normalized_file_mode(source_stat)
        copied_fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | OPEN_NOFOLLOW,
            mode,
            dir_fd=destination_fd,
        )
        try:
            with os.fdopen(os.dup(opened_source), "rb") as source_file:
                copy_stream(source_file, copied_fd)
            os.fchmod(copied_fd, mode)
            os.utime(copied_fd, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
            os.fsync(copied_fd)
        finally:
            os.close(copied_fd)
    finally:
        os.close(opened_source)


def validate_symlink_target(target: str, relative_parent: tuple[str, ...], display: Path) -> None:
    if os.path.isabs(target):
        raise ValueError(f"skill symlink must be relative: {display} -> {target}")
    resolved = list(relative_parent)
    for part in target.split(os.sep):
        if part in {"", "."}:
            continue
        if part == "..":
            if not resolved:
                raise ValueError(f"skill symlink escapes its root: {display} -> {target}")
            resolved.pop()
        else:
            resolved.append(part)


def copy_tree_entries_from_fd(
    source_fd: int,
    destination_fd: int,
    display: Path,
    relative_parent: tuple[str, ...] = (),
) -> None:
    for entry in os.scandir(source_fd):
        source_entry = display / entry.name
        entry_stat = entry.stat(follow_symlinks=False)
        if stat.S_ISLNK(entry_stat.st_mode):
            target = os.readlink(entry.name, dir_fd=source_fd)
            validate_symlink_target(target, relative_parent, source_entry)
            os.symlink(target, entry.name, dir_fd=destination_fd)
            os.utime(
                entry.name,
                ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS),
                dir_fd=destination_fd,
                follow_symlinks=False,
            )
        elif stat.S_ISDIR(entry_stat.st_mode):
            try:
                os.mkdir(entry.name, mode=INSTALLED_DIRECTORY_MODE, dir_fd=destination_fd)
            except OSError as error:
                raise RuntimeError(f"could not create installed skill directory: {source_entry}") from error
            source_child_fd = open_child_directory(source_fd, entry.name, create=False)
            destination_child_fd = open_child_directory(destination_fd, entry.name, create=False)
            try:
                copy_tree_entries_from_fd(
                    source_child_fd,
                    destination_child_fd,
                    source_entry,
                    (*relative_parent, entry.name),
                )
                os.fchmod(destination_child_fd, INSTALLED_DIRECTORY_MODE)
                os.utime(
                    destination_child_fd,
                    ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS),
                )
                os.fsync(destination_child_fd)
            finally:
                os.close(destination_child_fd)
                os.close(source_child_fd)
        elif stat.S_ISREG(entry_stat.st_mode):
            copy_regular_entry(source_fd, destination_fd, entry.name)
        else:
            raise ValueError(f"unsupported file type in skill: {source_entry}")


def copy_tree_entries(source: Path, destination_fd: int) -> None:
    source_fd, complete = open_directory_path(source, create=False)
    if not complete:
        os.close(source_fd)
        raise FileNotFoundError(f"skill source does not exist: {source}")
    try:
        copy_tree_entries_from_fd(source_fd, destination_fd, source)
    finally:
        os.close(source_fd)


def reject_staged_symlinks(directory_fd: int, relative_prefix: str = "") -> None:
    for entry in os.scandir(directory_fd):
        relative = f"{relative_prefix}/{entry.name}" if relative_prefix else entry.name
        entry_stat = entry.stat(follow_symlinks=False)
        if stat.S_ISLNK(entry_stat.st_mode):
            raise ValueError(f"maintained skill trees must not contain symlinks: {relative}")
        if stat.S_ISDIR(entry_stat.st_mode):
            child_fd = open_child_directory(directory_fd, entry.name, create=False)
            try:
                reject_staged_symlinks(child_fd, relative)
            finally:
                os.close(child_fd)


def staged_symlink_targets(
    directory_fd: int,
    relative_parent: tuple[str, ...] = (),
) -> dict[tuple[str, ...], str]:
    targets: dict[tuple[str, ...], str] = {}
    for entry in os.scandir(directory_fd):
        entry_path = (*relative_parent, entry.name)
        entry_stat = entry.stat(follow_symlinks=False)
        if stat.S_ISLNK(entry_stat.st_mode):
            targets[entry_path] = os.readlink(entry.name, dir_fd=directory_fd)
        elif stat.S_ISDIR(entry_stat.st_mode):
            child_fd = open_child_directory(directory_fd, entry.name, create=False)
            try:
                targets.update(staged_symlink_targets(child_fd, entry_path))
            finally:
                os.close(child_fd)
    return targets


def validate_staged_symlink_graph(directory_fd: int) -> None:
    targets = staged_symlink_targets(directory_fd)
    for symlink_path, target in targets.items():
        if os.path.isabs(target):
            raise ValueError(f"skill symlink must be relative: {'/'.join(symlink_path)} -> {target}")
        pending = [*symlink_path[:-1], *target.split(os.sep)]
        resolved: list[str] = []
        expansions = 0
        while pending:
            part = pending.pop(0)
            if part in {"", "."}:
                continue
            if part == "..":
                if not resolved:
                    raise ValueError(
                        f"skill symlink graph escapes its root: {'/'.join(symlink_path)} -> {target}"
                    )
                resolved.pop()
                continue
            resolved.append(part)
            nested_target = targets.get(tuple(resolved))
            if nested_target is None:
                continue
            expansions += 1
            if expansions > 40:
                raise ValueError(f"skill symlink graph contains a cycle: {'/'.join(symlink_path)}")
            resolved.pop()
            pending = [*nested_target.split(os.sep), *pending]


def hash_field(digest: Any, value: bytes) -> None:
    digest.update(len(value).to_bytes(8, "big"))
    digest.update(value)


def collect_tree_entries(
    directory_fd: int,
    relative_prefix: str = "",
) -> list[tuple[str, int]]:
    entries: list[tuple[str, int]] = []
    for entry in os.scandir(directory_fd):
        relative = f"{relative_prefix}/{entry.name}" if relative_prefix else entry.name
        entry_stat = entry.stat(follow_symlinks=False)
        entries.append((relative, entry_stat.st_mode))
        if stat.S_ISDIR(entry_stat.st_mode):
            child_fd = open_child_directory(directory_fd, entry.name, create=False)
            try:
                entries.extend(collect_tree_entries(child_fd, relative))
            finally:
                os.close(child_fd)
    return entries


def open_relative_entry_parent(root_fd: int, relative: str) -> tuple[int, str]:
    parts = relative.split("/")
    current_fd = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            next_fd = open_child_directory(current_fd, part, create=False)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd, parts[-1]
    except BaseException:
        os.close(current_fd)
        raise


def snapshot_hash_fd(directory_fd: int) -> str:
    digest = hashlib.sha256(b"sdlc-snapshot-v3\0")
    entries = sorted(collect_tree_entries(directory_fd), key=lambda item: item[0])
    for relative, entry_mode in entries:
        parent_fd, name = open_relative_entry_parent(directory_fd, relative)
        try:
            if stat.S_ISLNK(entry_mode):
                hash_field(digest, b"link")
                hash_field(digest, relative.encode())
                hash_field(digest, os.readlink(name, dir_fd=parent_fd).encode())
            elif stat.S_ISDIR(entry_mode):
                hash_field(digest, b"dir")
                hash_field(digest, relative.encode())
            elif stat.S_ISREG(entry_mode):
                hash_field(digest, b"file")
                hash_field(digest, relative.encode())
                executable = b"1" if stat.S_IMODE(entry_mode) & 0o111 else b"0"
                hash_field(digest, executable)
                file_fd = os.open(name, os.O_RDONLY | OPEN_NOFOLLOW, dir_fd=parent_fd)
                try:
                    file_stat = os.fstat(file_fd)
                    digest.update(file_stat.st_size.to_bytes(8, "big"))
                    remaining = file_stat.st_size
                    while remaining:
                        chunk = os.read(file_fd, min(1024 * 1024, remaining))
                        if not chunk:
                            raise RuntimeError(f"installed payload changed while hashing: {relative}")
                        digest.update(chunk)
                        remaining -= len(chunk)
                    if os.read(file_fd, 1):
                        raise RuntimeError(f"installed payload changed while hashing: {relative}")
                finally:
                    os.close(file_fd)
            else:
                raise ValueError(f"unsupported file type in installed payload: {relative}")
        finally:
            os.close(parent_fd)
    return digest.hexdigest()


def rename_noreplace_primitive() -> tuple[Any, int]:
    libc = ctypes.CDLL(None, use_errno=True)
    if hasattr(libc, "renameat2"):
        rename = libc.renameat2
        flag = 1
    elif hasattr(libc, "renameatx_np"):
        rename = libc.renameatx_np
        flag = 0x00000004
    else:
        raise RuntimeError("safe skill publication requires renameat2 or renameatx_np")
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
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    result = rename(
        source_parent_fd,
        source_bytes,
        destination_parent_fd,
        destination_bytes,
        flag,
    )
    if result == 0:
        return True
    error_number = ctypes.get_errno()
    if error_number == errno.EEXIST:
        return False
    raise OSError(error_number, os.strerror(error_number), destination)


def check_atomic_rename_support(path: Path, write_probe: bool) -> None:
    directory_fd, _ = open_directory_path(path, create=False)
    source = f".sdlc-rename-probe-{secrets.token_hex(12)}"
    destination = f"{source}-published"
    probe_created = False
    probe_renamed = False
    try:
        rename, flag = rename_noreplace_primitive()
        if not write_probe:
            return
        os.mkdir(source, mode=0o700, dir_fd=directory_fd)
        probe_created = True
        result = rename(
            directory_fd,
            os.fsencode(source),
            directory_fd,
            os.fsencode(destination),
            flag,
        )
        if result != 0:
            error_number = ctypes.get_errno()
            raise OSError(error_number, os.strerror(error_number), destination)
        probe_renamed = True
    finally:
        try:
            if probe_created:
                probe_name = destination if probe_renamed else source
                os.rmdir(probe_name, dir_fd=directory_fd)
                os.fsync(directory_fd)
        finally:
            os.close(directory_fd)


def list_entries(directory_fd: int) -> list[str]:
    try:
        return os.listdir(directory_fd)
    except OSError as error:
        raise RuntimeError("could not list staged skill directory") from error


def entry_stat(directory_fd: int, name: str) -> os.stat_result:
    try:
        return os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except OSError as error:
        raise RuntimeError(f"could not inspect staged skill entry: {name}") from error


def remove_directory_entry(directory_fd: int, name: str) -> None:
    try:
        os.rmdir(name, dir_fd=directory_fd)
    except OSError as error:
        raise RuntimeError(f"could not remove staged skill directory: {name}") from error


def unlink_entry(directory_fd: int, name: str) -> None:
    try:
        os.unlink(name, dir_fd=directory_fd)
    except OSError as error:
        raise RuntimeError(f"could not remove staged skill entry: {name}") from error


def remove_open_directory_entry(parent_fd: int, name: str, opened_fd: int) -> None:
    expected = os.fstat(opened_fd)
    try:
        actual = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as error:
        raise RuntimeError(f"staged directory disappeared during cleanup: {name}") from error
    if not stat.S_ISDIR(actual.st_mode) or (actual.st_dev, actual.st_ino) != (
        expected.st_dev,
        expected.st_ino,
    ):
        raise RuntimeError(f"staged directory changed during cleanup: {name}")
    remove_directory_entry(parent_fd, name)


def preserve_stale_staging(parent_fd: int, name: str, staging_fd: int) -> str:
    expected = os.fstat(staging_fd)
    for _attempt in range(8):
        preserved = f".sdlc-preserved-{secrets.token_hex(12)}"
        if atomic_rename_noreplace(parent_fd, name, parent_fd, preserved):
            break
    else:
        raise RuntimeError(f"could not quarantine stale staging directory: {name}")
    try:
        moved = os.stat(preserved, dir_fd=parent_fd, follow_symlinks=False)
    except OSError as error:
        raise RuntimeError(f"could not inspect quarantined stale staging: {preserved}") from error
    if not stat.S_ISDIR(moved.st_mode) or (moved.st_dev, moved.st_ino) != (
        expected.st_dev,
        expected.st_ino,
    ):
        raise RuntimeError(f"stale staging changed while quarantining: {name}; preserved as {preserved}")
    os.fsync(parent_fd)
    print(
        f"warning: preserved interrupted installer staging as {preserved}; inspect and remove it manually",
        file=sys.stderr,
    )
    return preserved


def remove_tree_contents(directory_fd: int) -> None:
    for name in list_entries(directory_fd):
        staged_stat = entry_stat(directory_fd, name)
        if stat.S_ISDIR(staged_stat.st_mode):
            child_fd = open_child_directory(directory_fd, name, create=False)
            try:
                remove_tree_contents(child_fd)
                remove_open_directory_entry(directory_fd, name, child_fd)
            finally:
                os.close(child_fd)
        else:
            unlink_entry(directory_fd, name)


def remove_staging_directory(parent_fd: int, name: str, staging_fd: int | None = None) -> None:
    opened_here = staging_fd is None
    if staging_fd is None:
        staging_fd = open_child_directory(parent_fd, name, create=False)
    try:
        remove_tree_contents(staging_fd)
        remove_open_directory_entry(parent_fd, name, staging_fd)
    finally:
        if opened_here:
            os.close(staging_fd)


def sha256_entry(directory_fd: int, name: str) -> str:
    digest = hashlib.sha256()
    descriptor = os.open(
        name,
        os.O_RDONLY | OPEN_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        dir_fd=directory_fd,
    )
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ValueError(f"installed vendor metadata must be a regular file: {name}")
        while chunk := os.read(descriptor, 1024 * 1024):
            digest.update(chunk)
    finally:
        os.close(descriptor)
    return digest.hexdigest()


def add_vendor_metadata(
    destination_fd: int,
    provenance: Path | None,
    license_file: Path | None,
    expected_provenance_sha256: str | None,
    expected_license_sha256: str | None,
) -> None:
    if provenance is None and license_file is None:
        if expected_provenance_sha256 is not None or expected_license_sha256 is not None:
            raise ValueError("vendor metadata hashes require provenance and license files")
        return
    if (
        provenance is None
        or license_file is None
        or expected_provenance_sha256 is None
        or expected_license_sha256 is None
    ):
        raise ValueError("vendored metadata requires files and expected hashes")
    try:
        os.mkdir(".sdlc-vendor", mode=0o755, dir_fd=destination_fd)
    except OSError as error:
        raise RuntimeError("could not create installed vendor metadata directory") from error
    metadata_fd = open_child_directory(destination_fd, ".sdlc-vendor", create=False)
    try:
        copy_source_to_new_file(provenance, metadata_fd, "provenance.json", INSTALLED_REGULAR_MODE)
        copy_source_to_new_file(license_file, metadata_fd, "LICENSE.txt", INSTALLED_REGULAR_MODE)
        if (
            sha256_entry(metadata_fd, "provenance.json") != expected_provenance_sha256
            or sha256_entry(metadata_fd, "LICENSE.txt") != expected_license_sha256
        ):
            raise RuntimeError("staged vendor metadata hash differs from its lock")
        os.fchmod(metadata_fd, INSTALLED_DIRECTORY_MODE)
        os.utime(metadata_fd, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
        os.fsync(metadata_fd)
    finally:
        os.close(metadata_fd)


def normalize_tree_timestamps(directory_fd: int) -> None:
    for entry in os.scandir(directory_fd):
        entry_stat = entry.stat(follow_symlinks=False)
        if stat.S_ISLNK(entry_stat.st_mode):
            os.utime(
                entry.name,
                ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS),
                dir_fd=directory_fd,
                follow_symlinks=False,
            )
        elif stat.S_ISDIR(entry_stat.st_mode):
            child_fd = open_child_directory(directory_fd, entry.name, create=False)
            try:
                normalize_tree_timestamps(child_fd)
            finally:
                os.close(child_fd)
        elif stat.S_ISREG(entry_stat.st_mode):
            file_fd = os.open(entry.name, os.O_RDONLY | OPEN_NOFOLLOW, dir_fd=directory_fd)
            try:
                os.utime(file_fd, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
                os.fsync(file_fd)
            finally:
                os.close(file_fd)
        else:
            raise ValueError(f"unsupported file type while normalizing timestamps: {entry.name}")
    os.utime(directory_fd, ns=(NORMALIZED_TIMESTAMP_NS, NORMALIZED_TIMESTAMP_NS))
    os.fsync(directory_fd)


def validate_tree_payload_identity(control_fd: int, payload_fd: int) -> None:
    expected = os.fstat(payload_fd)
    try:
        actual = os.stat("payload", dir_fd=control_fd, follow_symlinks=False)
    except OSError as error:
        raise RuntimeError("private tree payload disappeared before publication") from error
    if not stat.S_ISDIR(actual.st_mode) or (actual.st_dev, actual.st_ino) != (
        expected.st_dev,
        expected.st_ino,
    ):
        raise RuntimeError("private tree payload changed before publication")


def publish_tree(
    allowed_root: Path,
    source: Path,
    destination: Path,
    provenance: Path | None = None,
    license_file: Path | None = None,
    expected_content_sha256: str | None = None,
    expected_provenance_sha256: str | None = None,
    expected_license_sha256: str | None = None,
) -> bool:
    parent_fd, name = open_parent_directory(allowed_root, destination)
    try:
        lock_and_recover_parent(parent_fd)
        control_name, control_fd = create_staging_wrapper(
            parent_fd,
            skill_staging_prefix(name),
        )
    except BaseException:
        os.close(parent_fd)
        raise
    published = False
    payload_fd: int | None = None
    final_mode = INSTALLED_DIRECTORY_MODE
    try:
        os.mkdir("payload", mode=0o700, dir_fd=control_fd)
        os.fsync(control_fd)
        payload_fd = open_child_directory(control_fd, "payload", create=False)
        copy_tree_entries(source, payload_fd)
        validate_staged_symlink_graph(payload_fd)
        if expected_content_sha256 is None:
            reject_staged_symlinks(payload_fd)
        else:
            actual_content_sha256 = snapshot_hash_fd(payload_fd)
            if actual_content_sha256 != expected_content_sha256:
                raise RuntimeError("staged skill differs from its locked content hash")
        add_vendor_metadata(
            payload_fd,
            provenance,
            license_file,
            expected_provenance_sha256,
            expected_license_sha256,
        )
        os.fchmod(payload_fd, final_mode)
        normalize_tree_timestamps(payload_fd)
        validate_tree_payload_identity(control_fd, payload_fd)
        if not atomic_rename_noreplace(control_fd, "payload", parent_fd, name):
            return False
        published = True
        os.fsync(payload_fd)
        os.fsync(control_fd)
        os.fsync(parent_fd)
        return True
    finally:
        try:
            if payload_fd is not None:
                try:
                    if not published:
                        os.fchmod(payload_fd, 0o700)
                finally:
                    os.close(payload_fd)
        finally:
            try:
                remove_staging_directory(parent_fd, control_name, control_fd)
                os.fsync(parent_fd)
            finally:
                os.close(control_fd)
                os.close(parent_fd)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    source_parser = subparsers.add_parser("source")
    source_parser.add_argument("path", type=Path)
    file_parser = subparsers.add_parser("file")
    file_parser.add_argument("allowed_root", type=Path)
    file_parser.add_argument("source", type=Path)
    file_parser.add_argument("destination", type=Path)
    root_parser = subparsers.add_parser("root")
    root_parser.add_argument("path", type=Path)
    root_parser.add_argument("--create", action="store_true")
    check_parser = subparsers.add_parser("check")
    check_parser.add_argument("path", type=Path)
    check_parser.add_argument("--write-probe", action="store_true")
    tree_parser = subparsers.add_parser("tree")
    tree_parser.add_argument("allowed_root", type=Path)
    tree_parser.add_argument("source", type=Path)
    tree_parser.add_argument("destination", type=Path)
    tree_parser.add_argument("--provenance", type=Path)
    tree_parser.add_argument("--license", dest="license_file", type=Path)
    tree_parser.add_argument("--expected-content-sha256")
    tree_parser.add_argument("--expected-provenance-sha256")
    tree_parser.add_argument("--expected-license-sha256")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.command == "source":
        validate_source_file(args.path)
        print("valid")
        return
    if args.command == "root":
        prepare_directory_root(args.path, args.create)
        print("ready")
        return
    if args.command == "check":
        check_atomic_rename_support(args.path, args.write_probe)
        print("supported")
        return
    if args.command == "file":
        added = publish_file(args.allowed_root, args.source, args.destination)
    else:
        added = publish_tree(
            args.allowed_root,
            args.source,
            args.destination,
            args.provenance,
            args.license_file,
            args.expected_content_sha256,
            args.expected_provenance_sha256,
            args.expected_license_sha256,
        )
    print("added" if added else "exists")


if __name__ == "__main__":
    main()
