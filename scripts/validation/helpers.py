"""Small, dependency-free helpers used by the kit validation harness."""
from __future__ import annotations

import hashlib
import os
import shutil
import signal
import stat
import subprocess
import tempfile
from pathlib import Path
from typing import Sequence


class CheckError(RuntimeError):
    """A validation assertion failed."""


def run(command: Sequence[str], *, cwd: Path, env: dict[str, str] | None = None,
        timeout: int = 180, umask: int | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    script = None
    if umask is not None:
        script = f'umask {umask:o}; exec "$@"'
        command = ("bash", "-c", script, "validate", *command)
    process = subprocess.Popen(
        command, cwd=cwd, env=merged, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr) from exc
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def expect_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode:
        raise CheckError(f"{label} failed ({result.returncode})\n{result.stdout[-2000:]}{result.stderr[-2000:]}")


def expect_fail(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode == 0:
        raise CheckError(f"{label} unexpectedly succeeded")


def snapshot(root: Path) -> dict[str, tuple[str, int, int]]:
    result: dict[str, tuple[str, int, int]] = {
        ".": ("directory", stat.S_IMODE(root.stat().st_mode), 0)
    }
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        entry = path.lstat()
        mode = stat.S_IMODE(entry.st_mode)
        if path.is_symlink():
            result[rel] = ("link:" + os.readlink(path), mode, 0)
        elif path.is_dir():
            result[rel] = ("directory", mode, 0)
        elif path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            result[rel] = (digest, mode, entry.st_size)
        else:
            result[rel] = (f"special:{stat.S_IFMT(entry.st_mode):o}", mode, 0)
    return result


def copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(
        source,
        target,
        symlinks=True,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )


def assert_same_tree(left: Path, right: Path) -> None:
    if snapshot(left) != snapshot(right):
        raise CheckError(f"tree mismatch: {left} != {right}")


def assert_mode(path: Path, expected: int) -> None:
    actual = stat.S_IMODE(path.stat().st_mode)
    if actual != expected:
        raise CheckError(f"{path} has mode {actual:o}, expected {expected:o}")


def assert_no_changes(root: Path, before: dict[str, tuple[str, int, int]]) -> None:
    after = snapshot(root)
    if before != after:
        raise CheckError("dry run changed the target tree")


class Fixture:
    def __init__(self, kit: Path):
        self.kit = kit
        self._tmp = tempfile.TemporaryDirectory(prefix="sdlc-validate-")
        self.root = Path(self._tmp.name)

    def close(self) -> None:
        self._tmp.cleanup()

    def __enter__(self) -> "Fixture":
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def target(self, name: str = "target") -> Path:
        path = self.root / name
        path.mkdir(parents=True)
        return path

    def kit_copy(self) -> Path:
        destination = self.root / "kit"
        copy_tree(self.kit, destination)
        return destination

    def install(self, target: Path, *, dry_run: bool = False,
                env: dict[str, str] | None = None, umask: int | None = None,
                kit: Path | None = None) -> subprocess.CompletedProcess[str]:
        source_kit = kit or self.kit
        args = ["bash", str(source_kit / "install.sh")]
        if dry_run:
            args.append("--dry-run")
        args.append(str(target))
        return run(args, cwd=source_kit, env=env, umask=umask, timeout=300)
