#!/usr/bin/env python3
"""Offline release gate for critical sdlc kit invariants.

Checks map to the installer guarantees that survive PRD 0001: containment,
no-clobber publication, restrictive umask, dry-run immutability, interrupted-run
cleanup, source rejection, inventory integrity, vendored-snapshot identity, and
directory-enumeration rewinding. See docs/prd/0001-reader-first-restructure.md.
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
        shutil.copytree(
            self.kit,
            destination,
            symlinks=True,
            ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
        )
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
        expect_ok(run([sys.executable, "scripts/vendor-skills.py", "verify"], cwd=self.kit, timeout=300), "vendor")
        self.inventory()

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
            expect_ok(run([sys.executable, "scripts/vendor-skills.py", "verify-installed", str(target / ".agents/skills")], cwd=self.kit), "installed integrity")
            assert_mode(target / ".agents/skills/brainstorming/SKILL.md", 0o644)
            marker = target / ".sdlc-kit-version"
            if marker.read_text() != kit_version(self.kit) + "\n":
                raise CheckError(f"installed kit version marker is wrong: {marker.read_text()!r}")
            if (target / "docs/runbook.md").exists():
                raise CheckError("runbook template was installed but is no longer in the payload")

    def installer_rejects_caller_handoff(self) -> None:
        with Fixture(self.kit) as fx:
            kit = fx.kit_copy()
            vendor_script = kit / "scripts/vendor-skills.py"
            module_spec = importlib.util.spec_from_file_location("vendor_skills_handoff", vendor_script)
            if module_spec is None or module_spec.loader is None:
                raise CheckError("could not load vendor script for installer handoff test")
            vendor_module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(vendor_module)

            vendor = kit / "vendor"
            data = json.loads((vendor / "skills.lock.json").read_text())
            hashes = vendor_module.install_hash_environment(data)
            dry_target = fx.root / "direct-dry-run"
            dry_result = fx.install(
                dry_target, dry_run=True, kit=kit,
                env={"SDLC_VENDOR_LOCKED": "1", **hashes},
            )
            expect_ok(dry_result, "direct dry run with caller-supplied vendor handoff")
            if dry_target.exists():
                raise CheckError("direct dry run created its target")

            skill = "writing-plans"
            skill_file = vendor / "skills" / skill / "SKILL.md"
            skill_file.write_text(skill_file.read_text() + "caller-controlled change\n")
            content_hashes = json.loads(hashes["SDLC_VENDOR_CONTENT_HASHES"])
            content_hashes[skill] = vendor_module.snapshot_hash(vendor / "skills" / skill)
            hashes["SDLC_VENDOR_CONTENT_HASHES"] = json.dumps(content_hashes, sort_keys=True, separators=(",", ":"))
            env = {"SDLC_VENDOR_LOCKED": "1", **hashes}

            holder_script = (
                "import fcntl, os, sys, time; "
                "fd = os.open(sys.argv[1], os.O_RDONLY | getattr(os, 'O_DIRECTORY', 0)); "
                "fcntl.flock(fd, fcntl.LOCK_EX); print('locked', flush=True); time.sleep(60)"
            )
            holder = subprocess.Popen(
                [sys.executable, "-c", holder_script, str(kit)],
                cwd=kit, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            try:
                if holder.stdout is None or holder.stdout.readline() != "locked\n":
                    raise CheckError("unrelated process failed to acquire the kit lock")
                target = fx.target()
                result = fx.install(target, kit=kit, env=env)
                expect_fail(result, "direct install with forged hashes and unrelated lock holder")
                if (target / "AGENTS.md").exists():
                    raise CheckError("install wrote files before rejecting the invalid vendor handoff")
            finally:
                holder.terminate()
                try:
                    holder.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    holder.kill()
                    holder.communicate()

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
            for path in (target / "AGENTS.md", target / ".agents/skills/brainstorming/SKILL.md"):
                assert_mode(path, 0o644)

    def no_clobber(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            existing = target / "AGENTS.md"
            existing.write_text("keep\n")
            (target / "docs/adr").mkdir(parents=True)
            (target / "docs/adr/existing.md").write_text("keep this document\n")
            existing_skill = target / ".agents/skills/sdlc/SKILL.md"
            existing_skill.parent.mkdir(parents=True)
            existing_skill.write_text("keep this skill\n")
            expect_ok(fx.install(target), "merge install")
            if existing.read_text() != "keep\n":
                raise CheckError("existing file was overwritten")
            if (target / "docs/adr/existing.md").read_text() != "keep this document\n":
                raise CheckError("existing nested document was overwritten")
            if not (target / "docs/adr/0001-record-architecture-decisions.md").is_file():
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
            expect_ok(
                run(
                    [sys.executable, "scripts/vendor-skills.py", "verify-installed", str(global_skills)],
                    cwd=self.kit,
                ),
                "external installed integrity",
            )

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

    def vendor_staging_cleanup(self) -> None:
        with Fixture(self.kit) as fx:
            kit = fx.kit_copy()
            vendor_script = kit / "scripts/vendor-skills.py"
            module_spec = importlib.util.spec_from_file_location("vendor_skills_staging", vendor_script)
            if module_spec is None or module_spec.loader is None:
                raise CheckError("could not load vendor script for staging cleanup test")
            vendor_module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(vendor_module)

            empty_staging = kit / (vendor_module.STAGING_PREFIX + "a" * 24)
            empty_staging.mkdir()
            nonempty_staging = kit / (vendor_module.STAGING_PREFIX + "b" * 24)
            nonempty_staging.mkdir()
            (nonempty_staging / "partial").write_text("adopter data\\n")
            unrecognized_staging = kit / (vendor_module.STAGING_PREFIX + "c" * 24)
            unrecognized_staging.mkdir()
            (unrecognized_staging / vendor_module.VENDOR_STAGING_MARKER).write_text("unknown marker\\n")

            expect_ok(
                run([sys.executable, "scripts/vendor-skills.py", "verify"], cwd=kit),
                "verify after interrupted vendor staging",
            )
            if os.path.lexists(empty_staging):
                raise CheckError("next vendor operation left an empty interrupted staging directory")
            for preserved in (nonempty_staging, unrecognized_staging):
                if not os.path.lexists(preserved):
                    raise CheckError(f"cleanup removed ambiguous staging data: {preserved.name}")
            if (nonempty_staging / "partial").read_text() != "adopter data\\n":
                raise CheckError("cleanup changed an unmarked staging directory")

    def vendor_sync_and_update_track(self) -> None:
        with Fixture(self.kit) as fx:
            kit = fx.kit_copy()
            vendor_script = kit / "scripts/vendor-skills.py"
            module_spec = importlib.util.spec_from_file_location("vendor_skills_update", vendor_script)
            if module_spec is None or module_spec.loader is None:
                raise CheckError("could not load vendor script for sync/update test")
            vendor_module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(vendor_module)

            name = "writing-plans"
            vendor = kit / "vendor"
            data = json.loads((vendor / "skills.lock.json").read_text())
            entry = data["skills"][name]
            source = "https://github.com/validator-fixture/vendor-skills.git"
            entry["source"] = source
            (vendor / "skills.lock.json").write_text(vendor_module.lock_text(data))
            (vendor / "provenance" / f"{name}.json").write_text(vendor_module.provenance_text(name, entry))

            repository = fx.root / "upstream-fixture"
            upstream_skill = repository / entry["upstreamPath"]
            shutil.copytree(vendor / "skills" / name, upstream_skill)
            skill_file = upstream_skill / "SKILL.md"
            skill_file.write_text(skill_file.read_text() + "\\nfixture update marker\\n")
            upstream_license = repository / entry["licenseSource"]
            upstream_license.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(vendor / "licenses" / f"{name}.txt", upstream_license)
            run(["git", "init", "--quiet"], cwd=repository)
            run(["git", "add", "-A"], cwd=repository)
            run(
                ["git", "-c", "user.name=validator", "-c", "user.email=validator@example.test",
                 "commit", "--quiet", "-m", "fixture update"],
                cwd=repository,
            )
            commit = run(["git", "rev-parse", "HEAD"], cwd=repository).stdout.strip()
            run(["git", "tag", "v-test"], cwd=repository)

            git_config = fx.root / "empty.gitconfig"
            git_config.write_text("")
            git_env = {
                "GIT_CONFIG_GLOBAL": str(git_config),
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": f"url.{repository.as_uri()}.insteadOf",
                "GIT_CONFIG_VALUE_0": source,
            }
            expect_ok(
                run(
                    [sys.executable, "scripts/vendor-skills.py", "update", name, "--track", "refs/tags/v-test"],
                    cwd=kit, env=git_env,
                ),
                "offline update with track",
            )
            updated = json.loads((vendor / "skills.lock.json").read_text())["skills"][name]
            if updated["track"] != "refs/tags/v-test" or updated["commit"] != commit:
                raise CheckError("update did not record the selected tag and resolved commit")
            expected_content = skill_file.read_text()
            if (vendor / "skills" / name / "SKILL.md").read_text() != expected_content:
                raise CheckError("update did not publish the tagged snapshot")
            expect_ok(run([sys.executable, "scripts/vendor-skills.py", "verify"], cwd=kit), "post-update verify")

            installed_snapshot = vendor / "skills" / name / "SKILL.md"
            installed_snapshot.write_text("damaged local snapshot\\n")
            expect_ok(
                run([sys.executable, "scripts/vendor-skills.py", "sync", name], cwd=kit, env=git_env),
                "offline sync restore",
            )
            if installed_snapshot.read_text() != expected_content:
                raise CheckError("sync did not restore the snapshot at the locked commit")
            expect_ok(run([sys.executable, "scripts/vendor-skills.py", "verify"], cwd=kit), "post-sync verify")

    def vendor_removal(self) -> None:
        with Fixture(self.kit) as fx:
            kit = fx.kit_copy()
            vendor_script = kit / "scripts/vendor-skills.py"
            module_spec = importlib.util.spec_from_file_location("vendor_skills_removal", vendor_script)
            if module_spec is None or module_spec.loader is None:
                raise CheckError("could not load vendor script for removal test")
            vendor_module = importlib.util.module_from_spec(module_spec)
            module_spec.loader.exec_module(vendor_module)

            vendor = kit / "vendor"

            def assert_no_removal_residue(label: str) -> None:
                residue = [
                    kit / vendor_module.VENDOR_OLD_NAME,
                    *kit.glob(f"{vendor_module.STAGING_PREFIX}*"),
                    *kit.glob(f"{vendor_module.VENDOR_OLD_NAME}.tmp-*"),
                ]
                residue = [path for path in residue if os.path.lexists(path)]
                if residue:
                    raise CheckError(f"{label} left transaction residue: {residue}")

            removed_name = "using-git-worktrees"
            source_name = "writing-plans"
            shutil.copytree(vendor / "skills" / source_name, vendor / "skills" / removed_name, symlinks=True)
            (vendor / "licenses" / f"{removed_name}.txt").write_bytes(
                (vendor / "licenses" / f"{source_name}.txt").read_bytes()
            )
            try:
                data = json.loads((vendor / "skills.lock.json").read_text())
            except (OSError, json.JSONDecodeError) as exc:
                raise CheckError("could not load vendor lock for removal test") from exc
            data["skills"][removed_name] = dict(data["skills"][source_name])
            (vendor / "skills.lock.json").write_text(vendor_module.lock_text(data))
            (vendor / "provenance" / f"{removed_name}.json").write_text(
                vendor_module.provenance_text(removed_name, data["skills"][removed_name])
            )

            before = snapshot(vendor)
            failed = run(
                [sys.executable, "scripts/vendor-skills.py", "remove", "missing-skill"],
                cwd=kit,
            )
            expect_fail(failed, "unknown vendor removal")
            assert_no_changes(vendor, before)
            assert_no_removal_residue("failed vendor removal")

            final_before = snapshot(vendor)
            final_removal = run(
                [sys.executable, "scripts/vendor-skills.py", "remove", *data["skills"]],
                cwd=kit,
            )
            expect_fail(final_removal, "final vendor removal")
            assert_no_changes(vendor, final_before)
            assert_no_removal_residue("failed final vendor removal")

            remaining = [name for name in data["skills"] if name != removed_name]
            remaining_skill_snapshots = {
                name: snapshot(vendor / "skills" / name) for name in remaining
            }
            remaining_metadata = {
                path: path.read_bytes()
                for directory in (vendor / "licenses", vendor / "provenance")
                for path in directory.iterdir()
                if path.stem != removed_name
            }
            offline_git_env = {
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.proxy",
                "GIT_CONFIG_VALUE_0": "http://127.0.0.1:1",
                "GIT_TERMINAL_PROMPT": "0",
            }
            expect_ok(
                run(
                    [sys.executable, "scripts/vendor-skills.py", "remove", removed_name, removed_name],
                    cwd=kit, env=offline_git_env,
                ),
                "offline vendor removal",
            )
            assert_no_removal_residue("successful vendor removal")
            if (vendor / "skills" / removed_name).exists():
                raise CheckError("removed vendor snapshot still exists")
            if (vendor / "licenses" / f"{removed_name}.txt").exists():
                raise CheckError("removed vendor license still exists")
            if (vendor / "provenance" / f"{removed_name}.json").exists():
                raise CheckError("removed vendor provenance still exists")
            expect_ok(run([sys.executable, "scripts/vendor-skills.py", "verify"], cwd=kit), "post-removal vendor verify")
            for name, expected in remaining_skill_snapshots.items():
                if snapshot(vendor / "skills" / name) != expected:
                    raise CheckError(f"remaining vendor snapshot changed: {name}")
            for path, expected in remaining_metadata.items():
                if path.read_bytes() != expected:
                    raise CheckError(f"remaining vendor metadata changed: {path.relative_to(vendor)}")

    def tamper(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install for tamper check")
            payload = target / ".agents/skills/to-spec/SKILL.md"
            payload.write_text(payload.read_text() + "tampered\n")
            expect_fail(run([sys.executable, "scripts/vendor-skills.py", "verify-installed", str(target / ".agents/skills")], cwd=self.kit), "tampered payload")

    def enumeration_rewind(self) -> None:
        """Directory descriptors must be rewound before every readdir.

        A descriptor opened while its directory was empty can otherwise report no entries
        for names created through it afterwards (btrfs caches the last directory index at
        open time), which silently skips staging cleanup and tree verification.
        """
        for name in ("scripts/install-safe.py", "scripts/vendor-skills.py"):
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

    def run(self) -> int:
        checks = (("syntax, schemas, and provenance", self.static), ("clean install", self.smoke),
                  ("installer rejects caller-controlled vendor handoff", self.installer_rejects_caller_handoff),
                  ("dry-run immutability", self.dry_run), ("restrictive umask", self.umask),
                  ("no-clobber publication", self.no_clobber),
                  ("interrupted-run cleanup", self.interrupted_cleanup),
                  ("cleanup on no-clobber rerun", self.cleanup_on_no_clobber_rerun),
                  ("process-group timeout", self.timeout_kills_process_group),
                  ("kit version marker", self.version_marker),
                  ("target containment", self.containment), ("source entry rejection", self.source_rejection),
                  ("vendor staging cleanup", self.vendor_staging_cleanup),
                  ("offline vendor sync and update track", self.vendor_sync_and_update_track),
                  ("vendored removal", self.vendor_removal), ("installed tamper detection", self.tamper),
                  ("directory enumeration rewind", self.enumeration_rewind))
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
