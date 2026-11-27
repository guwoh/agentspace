"""Regression tests for desktop services using disposable fictional workspaces."""
from pathlib import Path
import tempfile
import unittest
import zipfile

from agentspace import initialize
from desktop_core import (MODES, backup, make_prompt, project_files, read_text,
                          registry, restore, save_skill, skills)


class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / "private"
        initialize(self.root)
        self.project = self.root / "contexts" / "demo-site"
        (self.project / "sessions").mkdir(parents=True)
        (self.project / "CURRENT.md").write_text("# Fictional context", encoding="utf-8")
        (self.project / "BRIEF.md").write_text("# Fictional brief", encoding="utf-8")
        (self.project / "sessions" / "2030-01-01-01.md").write_text("# Fictional session", encoding="utf-8")
        (self.root / "contexts/INDEX.md").write_text(
            "| demo-site | Demo | demo-root | demo-site/BRIEF.md | 2030-01-01-01 |\n",
            encoding="utf-8")

    def test_registry_and_history(self):
        self.assertEqual(registry(self.root)[0]["id"], "demo-site")
        self.assertEqual(len(project_files(self.root, "demo-site")), 3)
        self.assertEqual(read_text(self.root, "contexts/demo-site/BRIEF.md"), "# Fictional brief")

    def test_folder_fallback(self):
        (self.root / "contexts/INDEX.md").write_text("# Legacy format", encoding="utf-8")
        self.assertFalse(registry(self.root)[0]["registered"])

    def test_prompts(self):
        for mode in MODES:
            result = make_prompt(self.root, "demo-site", mode, project_root="demo-root")
            self.assertIn("demo-site", result)
            self.assertIn("AGENTS.md", result)
        self.assertIn("explicitly request save context", make_prompt(self.root, "demo-site", "Save context"))
        self.assertIn("Do not modify files", make_prompt(self.root, "demo-site", "Overview"))
        self.assertIn("Wait before executing", make_prompt(self.root, "demo-site"))

    def test_invalid_project(self):
        with self.assertRaises(ValueError):
            make_prompt(self.root, "../demo-site")

    def test_path_escape(self):
        with self.assertRaises(ValueError):
            read_text(self.root, "../outside.md")

    def test_skills(self):
        save_skill(self.root, "coding", "# Coding")
        self.assertEqual(skills(self.root), ["coding"])
        self.assertIn("skills/coding/SKILL.md", make_prompt(self.root, "demo-site", selected_skills=["coding"]))
        with self.assertRaises(ValueError):
            make_prompt(self.root, "demo-site", selected_skills=["missing"])
        with self.assertRaises(ValueError):
            save_skill(self.root, "coding", "overwrite")
        with self.assertRaises(ValueError):
            save_skill(self.root, "coding", "overwrite", previous="stale")
        save_skill(self.root, "coding", "# Updated", previous="# Coding")
        self.assertEqual(read_text(self.root, "skills/coding/SKILL.md"), "# Updated")

    def test_backup_roundtrip(self):
        save_skill(self.root, "coding", "# Coding")
        (self.project / "raw.bin").write_bytes(b"fictional raw data")
        target = self.base / "backup.zip"
        count = backup(self.root, target)
        with zipfile.ZipFile(target) as z:
            self.assertNotIn("contexts/demo-site/raw.bin", z.namelist())
        dest = self.base / "restored"
        self.assertEqual(restore(target, dest), count)
        self.assertEqual(registry(dest), registry(self.root))
        self.assertEqual(skills(dest), ["coding"])
        with self.assertRaises(ValueError):
            restore(target, dest)
        with self.assertRaises(FileExistsError):
            backup(self.root, target)

    def test_backup_destination(self):
        with self.assertRaises(ValueError):
            backup(self.root, self.root / "backup.zip")

    def test_restore_traversal(self):
        target = self.base / "malicious.zip"
        with zipfile.ZipFile(target, "w") as z:
            z.writestr("AGENTS.md", "fictional")
            z.writestr("contexts/INDEX.md", "fictional")
            z.writestr("../escape.md", "fictional")
        with self.assertRaises(ValueError):
            restore(target, self.base / "restored")
        self.assertFalse((self.base / "restored").exists())

    def test_restore_windows_path(self):
        target = self.base / "malicious.zip"
        with zipfile.ZipFile(target, "w") as z:
            z.writestr("AGENTS.md", "fictional")
            z.writestr("contexts/INDEX.md", "fictional")
            z.writestr("contexts/..\\escape.md", "fictional")
        with self.assertRaises(ValueError):
            restore(target, self.base / "restored")


if __name__ == "__main__":
    unittest.main()
