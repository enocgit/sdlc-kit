#!/usr/bin/env python3
"""Offline release gate for critical sdlc kit invariants.

Checks map to the installer guarantees: containment, no-clobber publication,
restrictive umask, dry-run immutability, interrupted-run cleanup, source
rejection, inventory integrity, vendored-snapshot identity, and
directory-enumeration rewinding.
"""
from __future__ import annotations

import ast
import contextlib
import hashlib
import importlib.util
import json
import os
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Sequence
from pathlib import Path


class CheckError(RuntimeError):
    """A validation assertion failed."""


def run(
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
    timeout: int = 300,
    umask: int | None = None,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    if umask is not None:
        command = ("bash", "-c", f"umask {umask:o}; exec \"$@\"", "validate", *command)
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=merged,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as timed_out:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=1)
        except subprocess.TimeoutExpired:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(
            command, timeout, output=stdout, stderr=stderr
        ) from timed_out
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def expect_ok(result: subprocess.CompletedProcess[str], label: str) -> None:
    if result.returncode:
        raise CheckError(
            f"{label} failed ({result.returncode})\n{result.stdout[-2000:]}{result.stderr[-2000:]}"
        )


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


def assert_same_tree(left: Path, right: Path) -> None:
    if snapshot(left) != snapshot(right):
        raise CheckError(f"tree mismatch: {left} != {right}")


def assert_mode(path: Path, expected: int) -> None:
    actual = stat.S_IMODE(path.stat().st_mode)
    if actual != expected:
        raise CheckError(f"{path} has mode {actual:o}, expected {expected:o}")


def assert_no_changes(root: Path, before: dict[str, tuple[str, int, int]]) -> None:
    if snapshot(root) != before:
        raise CheckError("dry run changed the target tree")


def kit_version(kit: Path) -> str:
    lines = (kit / "CHANGELOG.md").read_text().splitlines()
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
    raise CheckError("CHANGELOG.md has no released version section")


class Fixture:
    def __init__(self, kit: Path):
        self.kit = kit
        self._tmp = tempfile.TemporaryDirectory(prefix="sdlc-validate-")
        self.root = Path(self._tmp.name)

    def close(self) -> None:
        self._tmp.cleanup()

    def __enter__(self) -> Fixture:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def target(self, name: str = "target") -> Path:
        path = self.root / name
        path.mkdir(parents=True)
        return path

    def kit_copy(self) -> Path:
        destination = self.root / "kit"
        if destination.exists():
            return destination
        shutil.copytree(
            self.kit,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
        return destination

    def install(self, target: Path, *, dry_run: bool = False,
                env: dict[str, str] | None = None, umask: int | None = None,
                kit: Path | None = None, upgrade: bool = False,
                adopt: Sequence[str] = (),
                resolved: Sequence[str] = ()) -> subprocess.CompletedProcess[str]:
        source_kit = kit or self.kit
        args = ["bash", str(source_kit / "install.sh")]
        if dry_run:
            args.append("--dry-run")
        if upgrade:
            args.append("--upgrade")
        for rel in adopt:
            args.extend(["--adopt", rel])
        for rel in resolved:
            args.extend(["--resolved", rel])
        args.append(str(target))
        return run(args, cwd=source_kit, env=env, umask=umask, timeout=300)


class Validator:
    def __init__(self, kit: Path):
        self.kit = kit
        self.failures: list[str] = []

    def check(self, name: str, function) -> None:
        try:
            function()
            print(f"  ok   {name}")
        except (CheckError, OSError, subprocess.SubprocessError, ValueError) as exc:
            self.failures.append(f"{name}: {exc}")
            print(f"  FAIL {name}: {exc}")

    def static(self) -> None:
        expect_ok(run(["bash", "-n", "install.sh"], cwd=self.kit), "install syntax")
        for path in (self.kit / "scripts").glob("*.py"):
            ast.parse(path.read_text(), filename=str(path))
        try:
            json.loads((self.kit / "vendor/skills.lock.json").read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise CheckError(f"invalid vendor lock: {exc}") from exc
        expect_ok(run([sys.executable, "scripts/validate-required-skills.py", "required-skills.yml"], cwd=self.kit), "manifest")
        self.inventory()

    def pins(self) -> None:
        """Every verbatim snapshot matches its recorded per-file content hashes."""
        try:
            lock = json.loads((self.kit / "vendor/skills.lock.json").read_text())
        except (OSError, json.JSONDecodeError) as exc:
            raise CheckError(f"invalid vendor lock: {exc}") from exc
        if lock.get("version") != 3 or not isinstance(lock.get("pins"), dict) or not lock["pins"]:
            raise CheckError("vendor lock must be version 3 with a non-empty pins mapping")
        for name, entry in lock["pins"].items():
            root = self.kit / entry["path"]
            if not root.is_dir():
                raise CheckError(f"pinned snapshot directory is missing: {entry['path']}")
            actual = {
                path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sorted(root.rglob("*"))
                if path.is_file() and not path.is_symlink()
            }
            if actual != entry.get("files", {}):
                raise CheckError(f"pinned snapshot content mismatch: {name}")
            for field in ("source", "license"):
                if not entry.get(field):
                    raise CheckError(f"pin {name} is missing {field} provenance")

    def inventory(self) -> None:
        manifest = {
            line.strip() for line in (self.kit / "scripts/kit-manifest.txt").read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        actual = {
            path.relative_to(self.kit).as_posix()
            for root in (self.kit / "skills", self.kit / "templates")
            for path in root.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if manifest != actual:
            raise CheckError(f"kit inventory mismatch: missing={sorted(actual - manifest)} extra={sorted(manifest - actual)}")
        adaptations = {
            path.relative_to(self.kit / "skills").parts[0]
            for path in (self.kit / "skills").glob("*/SKILL.md")
            if "maintained adaptation" in path.read_text(encoding="utf-8")
        }
        missing_licenses = sorted(
            name
            for name in adaptations
            if not any((self.kit / "skills" / name).glob("LICENSE*"))
        )
        if missing_licenses:
            raise CheckError(
                f"maintained adaptations missing bundled upstream license: {', '.join(missing_licenses)}"
            )
        manifest_module = importlib.util.spec_from_file_location(
            "validate_required_skills", self.kit / "scripts/validate-required-skills.py"
        )
        if manifest_module is None or manifest_module.loader is None:
            raise CheckError("could not load required-skills validator")
        manifest_parser = importlib.util.module_from_spec(manifest_module)
        manifest_module.loader.exec_module(manifest_parser)
        try:
            required = manifest_parser.yaml.load(
                (self.kit / "required-skills.yml").read_text(),
                Loader=manifest_parser.UniqueKeyLoader,
            ) or {}
        except Exception as exc:
            raise CheckError(f"could not parse required-skills.yml: {exc}") from exc
        declared = {
            entry["sourcePath"]
            for entry in required.get("skills", [])
            if entry.get("kind") in {"local", "vendored"}
        }
        expected = {
            path.relative_to(self.kit).as_posix()
            for root in (self.kit / "skills", self.kit / "vendor/skills")
            for path in root.iterdir() if path.is_dir()
        }
        if declared != expected:
            raise CheckError(f"skill declarations mismatch: missing={sorted(expected - declared)} extra={sorted(declared - expected)}")

    def workflow_rules(self) -> None:
        """The files agents actually read carry the operative workflow rules.

        A harness without skills reads only AGENTS.md, so the template manual
        must carry the gates, the review order, and the no-compromise rules;
        the skills it names carry only what their reader needs.
        """
        required: dict[str, tuple[str, ...]] = {
            "templates/AGENTS.md": (
                "1. A human performs every merge.",
                "2. Review runs in a context that did not write the change",
                "3. A change to a trust boundary gets a security review before merge",
                "4. Implementation never drifts from a frozen contract.",
                "5. Behavior ships with tests, and each check is proven able to fail.",
                "6. The spec states what actually shipped.",
                "7. No secrets in the repository, logs, or artifacts.",
                "run `bootstrap` first",
                "**Gate: approve plan.** Stop and quote the smoke check",
                "No code before\n  approval, even when the task asks for a PR.",
                "**Gate: the human merges.**",
                "a failing test first",
                "is not\n  swapped for another input on your own",
                "Before opening the PR, get a review from a context that did not write the change",
                "on\n   a different model",
                "never\nyour summary",
                "If a third round\nstill finds required changes",
                "The PR names\nthe reviewer, its model, and the verdict.",
                "do not poll CI",
            ),
            "skills/bootstrap/SKILL.md": (
                "## Gate: approve foundation",
                "## Prove the checks",
                "Commit nothing before approval.",
            ),
            "skills/code-review/SKILL.md": (
                "A check that cannot run as approved is not a",
                "confirm it in the installed source",
                "Missing evidence is a note, not a block.",
            ),
        }
        for name, needles in required.items():
            text = (self.kit / name).read_text(encoding="utf-8")
            missing = [needle for needle in needles if needle not in text]
            if missing:
                raise CheckError(f"{name} is missing operative rules: {missing}")
        lines = len((self.kit / "templates/AGENTS.md").read_text(encoding="utf-8").splitlines())
        if lines > 125:
            raise CheckError(f"templates/AGENTS.md is {lines} lines; the budget is 125")

    def smoke(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install")
            for source, destination in (
                (self.kit / "templates/AGENTS.md", target / "AGENTS.md"),
                (self.kit / "templates/CLAUDE.md", target / "CLAUDE.md"),
                (self.kit / "required-skills.yml", target / "required-skills.yml"),
            ):
                if not destination.is_file() or destination.read_bytes() != source.read_bytes():
                    raise CheckError(f"missing or changed installed file: {destination}")
            for source_root, destination_root in (
                (self.kit / "templates/docs", target / "docs"),
                (self.kit / "templates/github", target / ".github"),
            ):
                for source in source_root.rglob("*"):
                    if source.is_file():
                        destination = destination_root / source.relative_to(source_root)
                        if not destination.is_file() or destination.read_bytes() != source.read_bytes():
                            raise CheckError(f"missing installed template: {destination}")
            for source in (self.kit / "skills").iterdir():
                if source.is_dir():
                    assert_same_tree(source, target / ".agents/skills" / source.name)

            assert_mode(target / ".agents/skills/grilling/SKILL.md", 0o644)
            marker = target / ".sdlc-kit-version"
            if marker.read_text() != kit_version(self.kit) + "\n":
                raise CheckError(f"installed kit version marker is wrong: {marker.read_text()!r}")
            if (target / "docs/runbook.md").exists():
                raise CheckError("runbook template was installed but is no longer in the payload")

    def dry_run(self) -> None:
        with Fixture(self.kit) as fx:
            kit = fx.kit_copy()
            parent = fx.root / "dry-run-parent"
            parent.mkdir()
            target = parent / "nested" / "target"
            parent_before = snapshot(parent)
            kit_before = snapshot(kit)
            expect_ok(fx.install(target, dry_run=True, kit=kit), "dry run")
            if target.exists():
                raise CheckError("dry run created a nonexistent target")
            assert_no_changes(parent, parent_before)
            assert_no_changes(kit, kit_before)

    def umask(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target, umask=0o077), "restrictive umask install")
            for path in (target / "AGENTS.md", target / ".agents/skills/grilling/SKILL.md"):
                assert_mode(path, 0o644)

    def no_clobber(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            existing = target / "AGENTS.md"
            existing.write_text("keep\n")
            (target / "docs/adr").mkdir(parents=True)
            (target / "docs/adr/existing.md").write_text("keep this document\n")
            existing_skill = target / ".agents/skills/bootstrap/SKILL.md"
            existing_skill.parent.mkdir(parents=True)
            existing_skill.write_text("keep this skill\n")
            expect_ok(fx.install(target), "merge install")
            if existing.read_text() != "keep\n":
                raise CheckError("existing file was overwritten")
            if (target / "docs/adr/existing.md").read_text() != "keep this document\n":
                raise CheckError("existing nested document was overwritten")
            if not (target / "docs/adr/TEMPLATE.md").is_file():
                raise CheckError("merge install did not preserve the existing directory")
            if existing_skill.read_text() != "keep this skill\n":
                raise CheckError("existing local skill was overwritten")

    def interrupted_cleanup(self) -> None:
        """Remove generated staging names but preserve ambiguous lookalikes."""
        with Fixture(self.kit) as fx:
            target = fx.target()
            stale_dir = target / (".sdlc-skill-interrupted-" + "4" * 24)
            stale_dir.mkdir()
            (stale_dir / "partial").write_text("partial\n")
            stale_file = target / (".sdlc-file-" + "5" * 24)
            stale_file.write_text("partial file\n")
            lookalike_file = target / ".sdlc-file-deadbeef"
            lookalike_file.write_text("adopter data\n")
            lookalike_dir = target / ".sdlc-skill-not-ours"
            lookalike_dir.mkdir()
            (lookalike_dir / "keep.txt").write_text("adopter data\n")
            legacy_name = target / ".sdlc-staging-intent"
            legacy_name.write_text("adopter data\n")
            expect_ok(fx.install(target), "install after interruption")
            for stale in (stale_dir, stale_file):
                if os.path.lexists(stale):
                    raise CheckError(f"generated interrupted-run staging survived: {stale.name}")
            for preserved in (lookalike_file, lookalike_dir, legacy_name):
                if not os.path.lexists(preserved):
                    raise CheckError(f"ambiguous adopter entry was deleted: {preserved.name}")
            if (lookalike_file.read_text() != "adopter data\n"
                    or (lookalike_dir / "keep.txt").read_text() != "adopter data\n"
                    or legacy_name.read_text() != "adopter data\n"):
                raise CheckError("cleanup changed ambiguous adopter data")
            if not (target / "AGENTS.md").is_file():
                raise CheckError("cleanup pass broke the install itself")

    def cleanup_on_no_clobber_rerun(self) -> None:
        """A complete install rerun cleans stale names even when payloads are skipped."""
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "initial install before cleanup rerun")
            stale_root = target / (".sdlc-file-" + "6" * 24)
            stale_nested = target / "docs" / (".sdlc-file-" + "7" * 24)
            skills_root = target / ".agents/skills"
            stale_skill = skills_root / (".sdlc-skill-interrupted-" + "8" * 24)
            stale_root.write_text("partial\n")
            stale_nested.write_text("partial\n")
            stale_skill.mkdir()
            (stale_skill / "partial").write_text("partial\n")
            expect_ok(fx.install(target), "no-clobber install rerun")
            leftovers = [path for path in (stale_root, stale_nested, stale_skill) if os.path.lexists(path)]
            if leftovers:
                raise CheckError(f"no-clobber rerun left stale staging behind: {leftovers}")
            if (target / "AGENTS.md").read_text() != (self.kit / "templates/AGENTS.md").read_text():
                raise CheckError("cleanup-on-rerun changed the installed payload")

    def timeout_kills_process_group(self) -> None:
        """A timeout sends SIGTERM to descendants before escalating to SIGKILL."""
        child = (
            "import pathlib,signal,sys,time; "
            "term_marker=pathlib.Path(sys.argv[1]); "
            "survived_marker=pathlib.Path(sys.argv[2]); "
            "ready_marker=pathlib.Path(sys.argv[3]); "
            "signal.signal(signal.SIGTERM, lambda *_: (term_marker.write_text('SIGTERM'), sys.exit(0))); "
            "ready_marker.write_text('ready'); time.sleep(10); survived_marker.write_text('survived')"
        )
        parent = (
            "import pathlib,subprocess,sys,time\n"
            "subprocess.Popen([sys.executable, '-c', " + repr(child) + ", sys.argv[1], sys.argv[2], sys.argv[3]])\n"
            "ready=pathlib.Path(sys.argv[3]); deadline=time.monotonic()+30\n"
            "while not ready.exists() and time.monotonic()<deadline:\n"
            "    time.sleep(0.01)\n"
            "time.sleep(30)\n"
        )
        with tempfile.TemporaryDirectory(prefix="sdlc-timeout-") as temporary:
            term_marker = Path(temporary) / "child-received-sigterm"
            child_marker = Path(temporary) / "child-survived"
            ready_marker = Path(temporary) / "child-ready"
            try:
                run([sys.executable, "-c", parent, str(term_marker), str(child_marker), str(ready_marker)],
                    cwd=self.kit, timeout=5)
            except subprocess.TimeoutExpired:
                pass
            else:
                raise CheckError("timed-out command unexpectedly completed")
            if not term_marker.exists():
                raise CheckError("timeout did not deliver SIGTERM to the child process group")
            deadline = time.monotonic() + 1.5
            while time.monotonic() < deadline and not child_marker.exists():
                time.sleep(0.05)
            if child_marker.exists():
                raise CheckError("timeout left a child process running")

    def version_marker(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            stale_marker = target / ".sdlc-kit-version"
            stale_marker.write_text("0.0.1\n")
            expect_ok(fx.install(target), "install for marker check")
            if stale_marker.read_text() != kit_version(self.kit) + "\n":
                raise CheckError("install did not update the kit version marker")
            assert_mode(stale_marker, 0o644)

            empty_unreleased_kit = fx.kit_copy()
            changelog = empty_unreleased_kit / "CHANGELOG.md"
            lines = changelog.read_text().splitlines()
            unreleased_heading = lines.index("## [Unreleased]")
            next_release = next(index for index in range(unreleased_heading + 1, len(lines))
                                if lines[index].startswith("## ["))
            changelog.write_text("\n".join(lines[:unreleased_heading + 1] + lines[next_release:]) + "\n")
            old_target = fx.target("empty-unreleased-target")
            expect_ok(fx.install(old_target, kit=empty_unreleased_kit), "install with empty Unreleased section")
            if (old_target / ".sdlc-kit-version").read_text() != kit_version(empty_unreleased_kit) + "\n":
                raise CheckError("empty Unreleased section did not select the released version")

    def containment(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            link = fx.root / "linked-target"
            link.symlink_to(target, target_is_directory=True)
            expect_fail(fx.install(link), "symlink target")
            target_before = snapshot(target)
            escape = fx.root / "escape"
            expect_fail(fx.install(target, env={"SKILLS_DIR": "../escape"}), "relative skills escape")
            assert_no_changes(target, target_before)
            if os.path.lexists(escape):
                raise CheckError("relative skills escape created an external destination")

            home = fx.root / "home"
            global_skills = home / ".agents/skills"
            global_skills.mkdir(parents=True)
            expect_ok(
                fx.install(target, env={"HOME": str(home), "SKILLS_DIR": str(global_skills)}),
                "explicit external skills path",
            )
            if (target / ".agents/skills").exists():
                raise CheckError("external skills install created the target's default skills directory")
            for source in (self.kit / "skills").iterdir():
                if source.is_dir():
                    assert_same_tree(source, global_skills / source.name)

    def source_rejection(self) -> None:
        with Fixture(self.kit) as fx:
            kit = fx.kit_copy()
            source = kit / "templates/docs/.validation-symlink"
            source.symlink_to("missing")
            expect_fail(fx.install(fx.target("symlink-target"), kit=kit), "source symlink")
            source.unlink()
            special = kit / "templates/docs/.validation-fifo"
            os.mkfifo(special)
            expect_fail(fx.install(fx.target("special-target"), kit=kit), "source special file")

    def enumeration_rewind(self) -> None:
        """Directory descriptors must be rewound before every readdir.

        A descriptor opened while its directory was empty can otherwise report no entries
        for names created through it afterwards (btrfs caches the last directory index at
        open time), which silently skips staging cleanup and tree verification.
        """
        name = "scripts/install-safe.py"
        tree = ast.parse((self.kit / name).read_text(), filename=name)
        for function in ast.walk(tree):
            if not isinstance(function, ast.FunctionDef):
                continue
            calls = [node for node in ast.walk(function) if isinstance(node, ast.Call)]
            rewinds = any(isinstance(node.func, ast.Name) and node.func.id == "rewind_directory"
                          for node in calls)
            if rewinds:
                continue
            for node in calls:
                if (isinstance(node.func, ast.Attribute) and node.func.attr in {"scandir", "listdir"}
                        and isinstance(node.func.value, ast.Name) and node.func.value.id == "os"):
                    raise CheckError(
                        f"{name}:{node.lineno} enumerates a directory without rewinding it first"
                    )
        # Exercise the real publication path on the kit's own filesystem; the shared temp
        # directory may be a tmpfs that never reproduces the cached-index behaviour.
        staging = Path(tempfile.mkdtemp(prefix="sdlc-validate-fs-", dir=self.kit.parent))
        try:
            destination = staging / "required-skills.yml"
            destination.write_text("keep\n")
            result = run([sys.executable, "scripts/install-safe.py", "file", str(staging),
                          str(self.kit / "required-skills.yml"), str(destination)], cwd=self.kit)
            expect_ok(result, "publish over an existing file")
            if result.stdout.strip() != "exists":
                raise CheckError(f"expected a no-clobber skip, got: {result.stdout.strip()}")
            if destination.read_text() != "keep\n":
                raise CheckError("existing file was overwritten")
            leftovers = [entry.name for entry in staging.iterdir() if entry.name.startswith(".sdlc-")]
            if leftovers:
                raise CheckError(f"publication left staging behind: {leftovers}")
        finally:
            shutil.rmtree(staging, ignore_errors=True)

    def _payload_hashes(self, target: Path) -> dict[str, str]:
        return {
            path.relative_to(target).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(target.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def upgrade_noop(self) -> None:
        """Upgrading an unchanged kit changes nothing except bookkeeping."""
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before no-op upgrade")
            before = self._payload_hashes(target)
            expect_ok(fx.install(target, upgrade=True), "no-op upgrade")
            after = self._payload_hashes(target)
            if before != after:
                raise CheckError("no-op upgrade changed the installed payload")
            try:
                manifest = json.loads((target / ".sdlc-kit-manifest.json").read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError(f"upgrade did not write a readable manifest: {exc}") from exc
            if manifest.get("kit") != kit_version(self.kit):
                raise CheckError("upgrade did not record the kit version in the manifest")

    def upgrade_applies(self) -> None:
        """Untouched kit files update, adopter edits survive, removals apply.

        RED→GREEN for the checksum-gated upgrade contract: the installed
        manifest distinguishes an untouched kit copy from an adopter-modified
        file, so the upgrade can replace the former and must preserve the
        latter.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before upgrade")
            kit = fx.kit_copy()
            # Kit-side changes for the next release simulation:
            agents = kit / "templates/AGENTS.md"
            agents.write_text(agents.read_text() + "\nNew kit rule.\n")
            (kit / "templates/docs").joinpath("new-template.md").write_text("new payload\n")
            (kit / "templates/docs/test-strategy.md").unlink()
            skill = kit / "skills/bootstrap/SKILL.md"
            skill.write_text(skill.read_text() + "\nRouter update.\n")
            # Adopter-side edit of an installer-added file:
            context = target / "docs/context.md"
            context.write_text(context.read_text() + "\nAdopter note.\n")
            upgrade_result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(upgrade_result, "content upgrade")
            report = upgrade_result.stdout
            if "New kit rule." not in (target / "AGENTS.md").read_text():
                raise CheckError("upgrade did not update an untouched kit file")
            if "Router update." not in (target / ".agents/skills/bootstrap/SKILL.md").read_text():
                raise CheckError("upgrade did not update an untouched skill file")
            if not (target / "docs/new-template.md").is_file():
                raise CheckError("upgrade did not add a new kit file")
            if "Adopter note." not in context.read_text():
                raise CheckError("upgrade overwrote an adopter-modified file")
            if (target / "docs/test-strategy.md").exists():
                raise CheckError("upgrade left an untouched file removed upstream")
            for needle in ("docs/context.md", "docs/test-strategy.md"):
                if needle not in report:
                    raise CheckError(f"upgrade report did not mention {needle}")
            try:
                manifest = json.loads((target / ".sdlc-kit-manifest.json").read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError(f"upgrade did not write a readable manifest: {exc}") from exc
            new_agents = kit / "templates/AGENTS.md"
            entry = manifest["target"]["AGENTS.md"]
            if not isinstance(entry, dict) or entry.get("base") != new_agents.read_text():
                raise CheckError("upgrade manifest does not anchor the updated file to the new version")
            if "docs/test-strategy.md" in manifest["target"]:
                raise CheckError("upgrade manifest still tracks a file removed upstream")
            if (target / ".sdlc-kit-version").read_text() != kit_version(kit) + "\n":
                raise CheckError("upgrade did not refresh the version marker")

    def upgrade_without_manifest(self) -> None:
        """Pre-manifest installs stay fully no-clobber and are told why."""
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before manifest removal")
            (target / ".sdlc-kit-manifest.json").unlink()
            kit = fx.kit_copy()
            agents = kit / "templates/AGENTS.md"
            agents.write_text(agents.read_text() + "\nNew kit rule.\n")
            before = self._payload_hashes(target)
            result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(result, "conservative upgrade without manifest")
            if self._payload_hashes(target) != before:
                raise CheckError("manifest-less upgrade changed installed files")
            if "manifest" not in result.stdout.lower():
                raise CheckError("manifest-less upgrade did not explain itself")

    def upgrade_merges_disjoint_edits(self) -> None:
        """A living file edited on both sides auto-merges disjoint hunks.

        RED→GREEN for the three-way merge contract: the install manifest must
        carry the installed-base content, so an upgrade can merge the kit's
        new version with adopter edits instead of forcing a whole-file
        hand-merge. Dry-run must predict the merge without writing.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before merge upgrade")
            kit = fx.kit_copy()
            kit_agents = kit / "templates/AGENTS.md"
            lines = kit_agents.read_text().splitlines()
            lines.insert(1, "Kit v2 rule sits near the top.")
            kit_agents.write_text("\n".join(lines) + "\n")
            adopter_agents = target / "AGENTS.md"
            adopter_agents.write_text(adopter_agents.read_text() + "\nAdopter convention at the end.\n")
            dry = fx.install(target, upgrade=True, kit=kit, dry_run=True)
            expect_ok(dry, "dry-run merge upgrade")
            if "Adopter convention at the end." not in adopter_agents.read_text():
                raise CheckError("dry-run merge upgrade modified the installed file")
            if "merged" not in dry.stdout:
                raise CheckError("dry-run upgrade did not predict the merge")
            result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(result, "merge upgrade")
            merged = adopter_agents.read_text()
            if "Kit v2 rule sits near the top." not in merged:
                raise CheckError("merge dropped the kit change")
            if "Adopter convention at the end." not in merged:
                raise CheckError("merge dropped the adopter edit")
            if "AGENTS.md" not in result.stdout or "merged" not in result.stdout:
                raise CheckError("upgrade report did not record the merge")
            try:
                manifest = json.loads((target / ".sdlc-kit-manifest.json").read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError(f"merge upgrade did not write a readable manifest: {exc}") from exc
            if manifest.get("version") != 3:
                raise CheckError("merge upgrade did not advance the manifest to version 3")
            entry = manifest["target"]["AGENTS.md"]
            if entry.get("class") != "living":
                raise CheckError("manifest does not classify AGENTS.md as living")
            if entry.get("base") != kit_agents.read_text():
                raise CheckError("manifest base was not re-anchored to the new kit version")
            if (target / "AGENTS.md.sdlc-conflict").exists():
                raise CheckError("clean merge left a conflict sibling behind")
            if (target / ".sdlc-kit-base").exists():
                raise CheckError("upgrade still materializes a base snapshot directory")

    def upgrade_conflict_preserves_adopter(self) -> None:
        """A conflicting hunk keeps the adopter file and writes a resolution copy.

        The adopter file is agent-consumed, so conflict markers must never
        land in it; the conflicted merge goes beside the base snapshot for
        the human to resolve.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before conflict upgrade")
            kit = fx.kit_copy()
            kit_agents = kit / "templates/AGENTS.md"
            kit_agents.write_text(kit_agents.read_text() + "\nKit rewrites the closing line.\n")
            adopter_agents = target / "AGENTS.md"
            adopter_agents.write_text(adopter_agents.read_text() + "\nAdopter rewrites the closing line.\n")
            before = adopter_agents.read_bytes()
            result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(result, "conflict upgrade")
            if adopter_agents.read_bytes() != before:
                raise CheckError("conflict upgrade modified the adopter file")
            conflict = target / "AGENTS.md.sdlc-conflict"
            if "<<<<<<<" not in conflict.read_text():
                raise CheckError("conflict upgrade wrote no resolution copy")
            if "AGENTS.md" not in result.stdout or "1 region(s)" not in result.stdout:
                raise CheckError("upgrade report did not record the conflict and its regions")

    def upgrade_ignores_reworded_placeholders(self) -> None:
        """Rewording a placeholder the adopter filled must not hold back other kit changes."""
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before placeholder upgrade")
            placeholder = "{One paragraph: the product and its users.}"
            adopter_agents = target / "AGENTS.md"
            text = adopter_agents.read_text()
            if placeholder not in text:
                raise CheckError("templates/AGENTS.md no longer has the project placeholder")
            adopter_agents.write_text(text.replace(placeholder, "Our product helps contributors."))
            kit = fx.kit_copy()
            kit_agents = kit / "templates/AGENTS.md"
            lines = kit_agents.read_text().replace(placeholder, "{One paragraph: what it does.}")
            kit_agents.write_text(lines.replace("## Where things live",
                                                "Kit v2 rule.\n\n## Where things live", 1))
            result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(result, "placeholder upgrade")
            merged = adopter_agents.read_text()
            if "Our product helps contributors." not in merged or "Kit v2 rule." not in merged:
                raise CheckError("placeholder rewording blocked the merge of other kit changes")
            if (target / "AGENTS.md.sdlc-conflict").exists():
                raise CheckError("placeholder rewording produced a conflict")

    def upgrade_resolved_reanchors(self) -> None:
        """A hand-resolved conflict, or a reconciled adopted file, is managed again."""
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before resolved upgrade")
            kit = fx.kit_copy()
            kit_agents = kit / "templates/AGENTS.md"
            kit_agents.write_text(kit_agents.read_text() + "\nKit rewrites the closing line.\n")
            adopter_agents = target / "AGENTS.md"
            adopter_text = adopter_agents.read_text() + "\nAdopter rewrites the closing line.\n"
            adopter_agents.write_text(adopter_text)
            expect_ok(fx.install(target, upgrade=True, kit=kit), "conflict before resolution")
            conflict = target / "AGENTS.md.sdlc-conflict"
            adopter_agents.write_text(conflict.read_text())
            marked = fx.install(target, upgrade=True, kit=kit, resolved=["AGENTS.md"])
            if marked.returncode == 0:
                raise CheckError("--resolved accepted a file that still has conflict markers")
            adopter_agents.write_text(adopter_text + "Kit rewrites the closing line.\n")
            expect_ok(fx.install(target, upgrade=True, kit=kit, adopt=["docs/context.md"]),
                      "adopt before resolution")
            result = fx.install(target, upgrade=True, kit=kit,
                                resolved=["AGENTS.md", "docs/context.md"])
            expect_ok(result, "resolved upgrade")
            if conflict.exists():
                raise CheckError("--resolved left the conflict file behind")
            manifest = json.loads((target / ".sdlc-kit-manifest.json").read_text())
            for rel, source in (("AGENTS.md", kit_agents),
                                ("docs/context.md", kit / "templates/docs/context.md")):
                entry = manifest["target"][rel]
                if entry.get("adopted") or entry.get("base") != source.read_text():
                    raise CheckError(f"--resolved did not re-anchor {rel} on the new kit version")
            if "Adopter rewrites the closing line." not in adopter_agents.read_text():
                raise CheckError("--resolved changed the resolved file")
            again = fx.install(target, upgrade=True, kit=kit)
            expect_ok(again, "upgrade after resolution")
            if "C AGENTS.md" in again.stdout or conflict.exists():
                raise CheckError("a resolved file conflicted again on the next upgrade")

    def upgrade_removes_legacy_vendor_metadata(self) -> None:
        """Older installers left .sdlc-vendor/ metadata the manifest never tracked."""
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before legacy cleanup")
            skills = target / ".agents/skills"
            for name in ("grilling", "retired-skill"):
                legacy = skills / name / ".sdlc-vendor"
                legacy.mkdir(parents=True)
                (legacy / "provenance.json").write_text("{}\n")
            own = skills / "team-skill"
            own.mkdir()
            (own / "SKILL.md").write_text("team skill\n")
            expect_ok(fx.install(target, upgrade=True), "legacy cleanup upgrade")
            if (skills / "grilling/.sdlc-vendor").exists() or (skills / "retired-skill").exists():
                raise CheckError("upgrade left legacy .sdlc-vendor metadata or its empty directory")
            if not (skills / "grilling/SKILL.md").is_file() or not (own / "SKILL.md").is_file():
                raise CheckError("legacy cleanup removed a skill file")

    def upgrade_class_routing(self) -> None:
        """Instance templates and pinned snapshots are never merged.

        A filled instance is adopter-owned even when the kit template changes;
        a pinned snapshot must stay byte-identical, so adopter edits there are
        reported divergence, not merge input.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before class-routing upgrade")
            kit = fx.kit_copy()
            arch = kit / "templates/docs/architecture.md"
            arch.write_text(arch.read_text() + "\nKit template drift.\n")
            specs = kit / "templates/docs/specs/README.md"
            specs.write_text(specs.read_text() + "\nKit spec-index drift.\n")
            pinned = kit / "vendor/skills/frontend-design/SKILL.md"
            pinned.write_text(pinned.read_text() + "\nKit edit to a pinned snapshot.\n")
            adopter_arch = target / "docs/architecture.md"
            adopter_arch.write_text(adopter_arch.read_text() + "\nAdopter shipped-architecture note.\n")
            adopter_specs = target / "docs/specs/README.md"
            adopter_specs.write_text(adopter_specs.read_text() + "\nAdopter product area.\n")
            adopter_pinned = target / ".agents/skills/frontend-design/SKILL.md"
            adopter_pinned.write_text(adopter_pinned.read_text() + "\nAdopter edit to a pinned snapshot.\n")
            before = (adopter_arch.read_bytes(), adopter_specs.read_bytes(), adopter_pinned.read_bytes())
            result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(result, "class-routing upgrade")
            if (adopter_arch.read_bytes(), adopter_specs.read_bytes(), adopter_pinned.read_bytes()) != before:
                raise CheckError("class routing merged a non-mergeable file")
            if "\n  C " in result.stdout or "\n  M " in result.stdout:
                raise CheckError("class routing merged a non-mergeable file")
            for needle in ("docs/architecture.md", "docs/specs/README.md", "frontend-design/SKILL.md"):
                if needle not in result.stdout:
                    raise CheckError(f"upgrade report did not mention {needle}")

    def upgrade_second_run_preserves_adopter(self) -> None:
        """Consecutive upgrades never mistake adopter content for kit content.

        RED→GREEN for the incident class: recording the installed file's hash
        as the kit's content made the second upgrade overwrite an
        adopter-modified file wholesale. The anchor must be the kit version
        the file is grounded in, and merged files must merge again rather
        than be replaced.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before consecutive upgrades")
            adopter_agents = target / "AGENTS.md"
            adopter_agents.write_text(adopter_agents.read_text() + "\nAdopter convention.\n")
            kit = fx.kit_copy()
            agents = kit / "templates/AGENTS.md"
            lines = agents.read_text().splitlines()
            lines.insert(1, "Kit rule one sits near the top.")
            agents.write_text("\n".join(lines) + "\n")
            expect_ok(fx.install(target, upgrade=True, kit=kit), "first upgrade merges")
            if "Adopter convention." not in adopter_agents.read_text():
                raise CheckError("first upgrade lost the adopter edit")
            if "Kit rule one sits near the top." not in adopter_agents.read_text():
                raise CheckError("first upgrade lost the kit change")
            kit_two = fx.kit_copy()
            agents_two = kit_two / "templates/AGENTS.md"
            lines = agents_two.read_text().splitlines()
            lines.insert(2, "Kit rule two also sits near the top.")
            agents_two.write_text("\n".join(lines) + "\n")
            expect_ok(fx.install(target, upgrade=True, kit=kit_two), "second upgrade merges again")
            after = adopter_agents.read_text()
            for needle in ("Adopter convention.", "Kit rule one sits near the top.",
                           "Kit rule two also sits near the top."):
                if needle not in after:
                    raise CheckError(f"consecutive upgrade lost content: {needle}")

    def upgrade_adopted_files(self) -> None:
        """--adopt transfers ownership: no writes, merges, siblings, or re-adds.

        RED→GREEN for the adopter-ownership contract: an adopted file stays
        byte-for-byte through template changes without a conflict sibling,
        and an adopted deleted file is never re-added.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before adopt")
            agents = target / "AGENTS.md"
            agents.write_text(agents.read_text() + "\nAdopter owns this line.\n")
            kit = fx.kit_copy()
            kit_agents = kit / "templates/AGENTS.md"
            kit_agents.write_text(kit_agents.read_text() + "\nKit rewrites the closing line.\n")
            before = agents.read_bytes()
            result = fx.install(target, upgrade=True, kit=kit, adopt=("AGENTS.md",))
            expect_ok(result, "adopt a modified file")
            if agents.read_bytes() != before:
                raise CheckError("the upgrade modified an adopted file")
            if (target / "AGENTS.md.sdlc-conflict").exists():
                raise CheckError("an adopted file produced a conflict sibling")
            if "adopted" not in result.stdout or "AGENTS.md" not in result.stdout:
                raise CheckError("upgrade report did not record the adoption")
            try:
                manifest = json.loads((target / ".sdlc-kit-manifest.json").read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError(f"upgrade did not write a readable manifest: {exc}") from exc
            entry = manifest["target"]["AGENTS.md"]
            if not (isinstance(entry, dict) and entry.get("adopted")):
                raise CheckError("manifest did not record the adopted flag")
            before = agents.read_bytes()
            expect_ok(fx.install(target, upgrade=True, kit=kit), "upgrade after adoption")
            if agents.read_bytes() != before:
                raise CheckError("a later upgrade modified an adopted file")
            strategy = target / "docs/test-strategy.md"
            strategy.unlink()
            result = fx.install(target, upgrade=True, kit=kit, adopt=("docs/test-strategy.md",))
            expect_ok(result, "adopt an absent file")
            if strategy.exists():
                raise CheckError("adopting an absent file re-added it")
            try:
                manifest = json.loads((target / ".sdlc-kit-manifest.json").read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError(f"upgrade did not write a readable manifest: {exc}") from exc
            if not (isinstance(manifest["target"].get("docs/test-strategy.md"), dict)
                    and manifest["target"]["docs/test-strategy.md"].get("adopted")):
                raise CheckError("manifest did not record the absent adopted file")
            expect_ok(fx.install(target, upgrade=True, kit=kit),
                      "upgrade with an absent adopted file")
            if strategy.exists():
                raise CheckError("a later upgrade re-added an adopted absent file")
            result = fx.install(target, upgrade=True, kit=kit, adopt=("no/such/file.md",))
            if result.returncode == 0:
                raise CheckError("an unknown --adopt target was accepted")
            if "not part of the kit payload" not in result.stdout + result.stderr:
                raise CheckError("an unknown --adopt target failed without explanation")

    def upgrade_removes_untouched(self) -> None:
        """Files removed upstream are deleted only when the adopter never touched them.

        RED→GREEN for removal: an untouched kit copy goes, along with a
        directory it leaves empty; an edited, adopted, or adopter-added file
        stays and is reported; a dry run deletes nothing.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before removal")
            adopted = "docs/specs/TEMPLATE.md"
            expect_ok(fx.install(target, upgrade=True, adopt=(adopted,)), "adopt before removal")
            skill_dir = target / ".agents/skills/address-review"
            (skill_dir / "notes.md").write_text("adopter notes\n")
            strategy = target / "docs/test-strategy.md"
            strategy.write_text(strategy.read_text() + "\nAdopter layer.\n")
            kit = fx.kit_copy()
            shutil.rmtree(kit / "skills/address-review")
            (kit / "templates/docs/test-strategy.md").unlink()
            (kit / "templates/docs/specs/TEMPLATE.md").unlink()
            (kit / "templates/docs/specs/README.md").unlink()

            before = self._payload_hashes(target)
            dry = fx.install(target, upgrade=True, kit=kit, dry_run=True)
            expect_ok(dry, "dry-run removal")
            if self._payload_hashes(target) != before:
                raise CheckError("a dry-run upgrade deleted files")
            if "address-review/SKILL.md" not in dry.stdout:
                raise CheckError("dry-run report did not list the pending deletion")

            result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(result, "upgrade with removals")
            if (skill_dir / "SKILL.md").exists():
                raise CheckError("upgrade left an untouched skill file removed upstream")
            if not (skill_dir / "notes.md").is_file():
                raise CheckError("upgrade deleted an adopter-added file")
            if (target / "docs/specs/README.md").exists():
                raise CheckError("upgrade left an untouched template removed upstream")
            if not (target / "docs/specs").is_dir():
                raise CheckError("upgrade removed a directory that still holds an adopted file")
            if not (target / adopted).is_file():
                raise CheckError("upgrade deleted an adopted file removed upstream")
            if "Adopter layer." not in strategy.read_text():
                raise CheckError("upgrade deleted an adopter-modified file removed upstream")
            for needle in ("docs/test-strategy.md", adopted):
                if needle not in result.stdout:
                    raise CheckError(f"upgrade report did not mention kept file {needle}")
            try:
                manifest = json.loads((target / ".sdlc-kit-manifest.json").read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError(f"upgrade did not write a readable manifest: {exc}") from exc
            stale = [rel for rel in manifest["skills"]["files"] if rel.startswith("address-review/")]
            if stale or "docs/test-strategy.md" in manifest["target"]:
                raise CheckError("upgrade manifest still tracks files removed upstream")

            skill_dir2 = target / ".agents/skills/grilling"
            shutil.rmtree(kit / "skills/grilling")
            expect_ok(fx.install(target, upgrade=True, kit=kit), "upgrade removing a whole skill")
            if skill_dir2.exists():
                raise CheckError("upgrade left the empty directory of a removed skill")

    def upgrade_after_move(self) -> None:
        """A moved or cloned checkout still upgrades its project-local skills.

        RED→GREEN: the manifest once recorded the skills root as an absolute
        path, so a teammate's clone at another path silently skipped every
        skill update. Both the current record and a legacy absolute record
        from another location must still match.
        """
        with Fixture(self.kit) as fx:
            original = fx.target("original")
            expect_ok(fx.install(original), "install before move")
            moved = fx.root / "moved"
            original.rename(moved)
            kit = fx.kit_copy()
            skill = kit / "skills/bootstrap/SKILL.md"
            skill.write_text(skill.read_text() + "\nRouter update.\n")
            expect_ok(fx.install(moved, upgrade=True, kit=kit), "upgrade after move")
            if "Router update." not in (moved / ".agents/skills/bootstrap/SKILL.md").read_text():
                raise CheckError("upgrade skipped skills in a moved checkout")
            manifest_path = moved / ".sdlc-kit-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["skills"]["root"] = "/elsewhere/clone/.agents/skills"
            manifest_path.write_text(json.dumps(manifest))
            skill.write_text(skill.read_text() + "\nSecond update.\n")
            expect_ok(fx.install(moved, upgrade=True, kit=kit), "upgrade with a legacy absolute root")
            if "Second update." not in (moved / ".agents/skills/bootstrap/SKILL.md").read_text():
                raise CheckError("upgrade skipped skills recorded under another clone's absolute path")

    def upgrade_keeps_workflows(self) -> None:
        """An installed CI workflow is never replaced or deleted by an upgrade.

        RED→GREEN: an unedited workflow is still a running pipeline, so a
        kit template change (or removal) must be reported, not applied.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install before workflow upgrade")
            workflow = target / ".github/workflows/ci.yml"
            before = workflow.read_bytes()
            kit = fx.kit_copy()
            kit_workflow = kit / "templates/github/workflows/ci.yml"
            kit_workflow.write_text(kit_workflow.read_text() + "# kit template change\n")
            result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(result, "upgrade with a changed workflow template")
            if workflow.read_bytes() != before:
                raise CheckError("upgrade replaced an installed CI workflow")
            if ".github/workflows/ci.yml" not in result.stdout:
                raise CheckError("upgrade report did not mention the changed workflow template")
            kit_workflow.unlink()
            result = fx.install(target, upgrade=True, kit=kit)
            expect_ok(result, "upgrade with a removed workflow template")
            if workflow.read_bytes() != before:
                raise CheckError("upgrade deleted an installed CI workflow")

    def identical_tracking(self) -> None:
        """Existing files identical to kit content are tracked for upgrades.

        A re-establishment install must not leave untouched kit files
        untracked — otherwise later upgrades can neither update nor merge
        them. Adopter-modified files stay untracked: the installer cannot
        invent an anchor for content it did not lay down.
        """
        with Fixture(self.kit) as fx:
            target = fx.target()
            (target / "CLAUDE.md").write_text((self.kit / "templates/CLAUDE.md").read_text())
            (target / "AGENTS.md").write_text("adopter version\n")
            expect_ok(fx.install(target), "install over identical and modified files")
            try:
                manifest = json.loads((target / ".sdlc-kit-manifest.json").read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError(f"install did not write a readable manifest: {exc}") from exc
            entry = manifest["target"].get("CLAUDE.md")
            if not isinstance(entry, dict) or entry.get("base") != (self.kit / "templates/CLAUDE.md").read_text():
                raise CheckError("identical existing file was not tracked for upgrades")
            if "AGENTS.md" in manifest["target"]:
                raise CheckError("adopter-modified file was tracked by install")

    def run(self) -> int:
        checks = (("syntax, schemas, and provenance", self.static), ("snapshot pins", self.pins),
                  ("workflow rules in the files agents read", self.workflow_rules),
                  ("clean install", self.smoke),
                  ("dry-run immutability", self.dry_run), ("restrictive umask", self.umask),
                  ("no-clobber publication", self.no_clobber),
                  ("interrupted-run cleanup", self.interrupted_cleanup),
                  ("cleanup on no-clobber rerun", self.cleanup_on_no_clobber_rerun),
                  ("process-group timeout", self.timeout_kills_process_group),
                  ("kit version marker", self.version_marker),
                  ("target containment", self.containment), ("source entry rejection", self.source_rejection),
                  ("directory enumeration rewind", self.enumeration_rewind),
                  ("upgrade is a no-op when nothing changed", self.upgrade_noop),
                  ("upgrade applies kit changes and protects adopter edits", self.upgrade_applies),
                  ("upgrade without a manifest is conservative", self.upgrade_without_manifest),
                  ("upgrade merges disjoint edits in living files", self.upgrade_merges_disjoint_edits),
                  ("upgrade conflicts preserve the adopter file", self.upgrade_conflict_preserves_adopter),
                  ("upgrade ignores reworded placeholders", self.upgrade_ignores_reworded_placeholders),
                  ("upgrade re-anchors files marked resolved", self.upgrade_resolved_reanchors),
                  ("upgrade removes legacy vendor metadata", self.upgrade_removes_legacy_vendor_metadata),
                  ("upgrade routes instance and pinned classes without merging", self.upgrade_class_routing),
                  ("consecutive upgrades preserve adopter content", self.upgrade_second_run_preserves_adopter),
                  ("adopted files are never written, merged, or re-added", self.upgrade_adopted_files),
                  ("upgrade deletes untouched files removed upstream", self.upgrade_removes_untouched),
                  ("upgrade works after the checkout moves", self.upgrade_after_move),
                  ("upgrade never replaces a CI workflow", self.upgrade_keeps_workflows),
                  ("identical existing files are tracked", self.identical_tracking))
        for name, function in checks:
            self.check(name, function)
        if self.failures:
            print(f"\n{len(self.failures)} critical checks failed", file=sys.stderr)
            return 1
        print("\nALL CRITICAL CHECKS PASSED")
        return 0


if __name__ == "__main__":
    os.environ.pop("SKILLS_DIR", None)
    sys.exit(Validator(Path(__file__).resolve().parent.parent).run())
