#!/usr/bin/env python3
"""Offline release gate for critical sdlc kit invariants."""
from __future__ import annotations

import ast
import concurrent.futures
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from importlib import import_module

_helpers = import_module("validation.helpers")
CheckError = _helpers.CheckError
Fixture = _helpers.Fixture
assert_mode = _helpers.assert_mode
assert_no_changes = _helpers.assert_no_changes
assert_same_tree = _helpers.assert_same_tree
copy_tree = _helpers.copy_tree
expect_fail = _helpers.expect_fail
expect_ok = _helpers.expect_ok
run = _helpers.run
snapshot = _helpers.snapshot


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
            result = fx.install(target)
            expect_ok(result, "install")
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

    def _publish_command(self, target: Path, source: Path, destination: Path,
                         kind: str = "file") -> list[str]:
        return [sys.executable, "scripts/install-safe.py", kind, str(target), str(source), str(destination)]

    def _tree_publisher(self, target: Path, source: Path, destination: Path) -> Any:
        module_spec = importlib.util.spec_from_file_location("install_safe", self.kit / "scripts/install-safe.py")
        if module_spec is None or module_spec.loader is None:
            raise CheckError("could not load install-safe module")
        module = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(module)
        return module

    def publication_race(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            sources = (fx.root / "first", fx.root / "second")
            for source, text in zip(sources, ("first\n", "second\n")):
                source.mkdir(mode=0o755)
                source.chmod(0o755)
                (source / "SKILL.md").write_text(text)
                (source / "SKILL.md").chmod(0o644)
            destination = target / "published"
            module = self._tree_publisher(target, sources[0], destination)
            barrier = threading.Barrier(2)
            original_rename = module.atomic_rename_noreplace

            def synchronized_rename(*args):
                barrier.wait(timeout=30)
                return original_rename(*args)

            setattr(module, "lock_and_recover_parent", lambda _parent_fd: None)
            setattr(module, "atomic_rename_noreplace", synchronized_rename)
            setattr(module, "write_staging_intent", lambda _parent_fd, _name: None)
            setattr(module, "clear_staging_intent", lambda _parent_fd, _missing_ok=False: None)
            publishers = [
                lambda source=source: module.publish_tree(target, source, destination)
                for source in sources
            ]
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda fn: fn(), publishers))
            if sorted(results) != [False, True]:
                raise CheckError(f"publication race violated no-clobber semantics: {results}")
            winner = sources[0] if (destination / "SKILL.md").read_text() == "first\n" else sources[1]
            assert_same_tree(winner, destination)

    def recovery(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            source = fx.root / "source"
            source.write_text("payload\n")
            staging = target / (".sdlc-skill-recovery-" + "1" * 24)
            staging.mkdir()
            (staging / ".sdlc-installing").write_bytes(b"sdlc-install-v1\n")
            (target / ".sdlc-staging-intent").write_text(staging.name + "\n")
            destination = target / "published"
            expect_ok(run(self._publish_command(target, source, destination), cwd=self.kit), "recovery publish")
            preserved = list(target.glob(".sdlc-preserved-*"))
            if len(preserved) != 1 or (target / ".sdlc-staging-intent").exists() or staging.exists():
                raise CheckError("interrupted publication was not recovered and quarantined")
            if destination.read_text() != "payload\n":
                raise CheckError("recovery did not publish the requested payload")

    def quarantine(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            source = fx.root / "source"
            source.write_text("payload\n")
            staging = target / (".sdlc-skill-quarantine-" + "2" * 24)
            staging.mkdir()
            (staging / ".sdlc-installing").write_bytes(b"sdlc-install-v1\n")
            (staging / "late-entry").write_text("preserve me\n")
            expect_ok(run(self._publish_command(target, source, target / "published"), cwd=self.kit), "quarantine publish")
            preserved = list(target.glob(".sdlc-preserved-*"))
            if len(preserved) != 1 or (preserved[0] / "late-entry").read_text() != "preserve me\n":
                raise CheckError("uncertain staging state was not preserved whole")
            if (target / "published").read_text() != "payload\n":
                raise CheckError("quarantine recovery did not publish the requested payload")

    def timeout_cleanup(self) -> None:
        with Fixture(self.kit) as fx:
            pid_file = fx.root / "descendant.pid"
            command = ["bash", "-c", f"sleep 30 & echo $! > {pid_file}; wait"]
            timed_out = False
            try:
                run(command, cwd=self.kit, timeout=1)
            except subprocess.TimeoutExpired:
                timed_out = True
            if not timed_out:
                raise CheckError("timeout fixture unexpectedly completed")
            try:
                pid = int(pid_file.read_text())
            except (OSError, ValueError) as exc:
                raise CheckError(f"timeout fixture did not record its descendant: {exc}") from exc
            for _ in range(20):
                try:
                    os.kill(pid, 0)
                except ProcessLookupError:
                    return
                time.sleep(0.05)
            raise CheckError(f"timed-out descendant survived: {pid}")

    def timeout_exit_race(self) -> None:
        original_killpg = _helpers.os.killpg
        setattr(_helpers.os, "killpg", lambda _pid, _signal: (_ for _ in ()).throw(ProcessLookupError()))
        try:
            try:
                run(["bash", "-c", "sleep 0.2"], cwd=self.kit, timeout=0.05)
            except subprocess.TimeoutExpired:
                return
            raise CheckError("timeout exit race unexpectedly completed")
        finally:
            setattr(_helpers.os, "killpg", original_killpg)

    def containment(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            link = fx.root / "linked-target"
            link.symlink_to(target, target_is_directory=True)
            expect_fail(fx.install(link), "symlink target")
            expect_fail(fx.install(target, env={"SKILLS_DIR": "../escape"}), "relative skills escape")
            home = fx.root / "home"
            global_skills = home / ".agents/skills"
            global_skills.mkdir(parents=True)
            alias = home / "pipeline-skills"
            alias.symlink_to(global_skills, target_is_directory=True)
            expect_fail(
                fx.install(target, env={"HOME": str(home), "SKILLS_DIR": str(alias)}),
                "user-global skills alias",
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

    def tamper(self) -> None:
        with Fixture(self.kit) as fx:
            target = fx.target()
            expect_ok(fx.install(target), "install for tamper check")
            payload = target / ".agents/skills/brainstorming/SKILL.md"
            payload.write_text(payload.read_text() + "tampered\n")
            expect_fail(run([sys.executable, "scripts/vendor-skills.py", "verify-installed", str(target / ".agents/skills")], cwd=self.kit), "tampered payload")

    def run(self) -> int:
        checks = (("syntax, schemas, and provenance", self.static), ("clean install", self.smoke),
                  ("dry-run immutability", self.dry_run), ("restrictive umask", self.umask),
                  ("no-clobber publication", self.no_clobber), ("publication race", self.publication_race),
                  ("interrupted publication recovery", self.recovery),
                  ("uncertain recovery quarantine", self.quarantine),
                  ("timeout process-group cleanup", self.timeout_cleanup),
                  ("timeout exit race cleanup", self.timeout_exit_race),
                  ("target containment", self.containment), ("source entry rejection", self.source_rejection),
                  ("installed tamper detection", self.tamper))
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
