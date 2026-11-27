"""Regression tests for desktop services using disposable fictional workspaces."""
from pathlib import Path
import tempfile
import unittest
import zipfile

from agentspace import initialize, verify
from desktop_core import (MODES, backup, create_demo, filter_projects, make_prompt, project_files, read_text,
                          load_feature_map, check_feature_map, find_features, feature_routes, make_feature_prompt,
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

    def test_project_search(self):
        items = registry(self.root)
        self.assertEqual(filter_projects(items, "DEMO site"), items)
        self.assertEqual(filter_projects(items, "missing"), [])
        (self.root / "contexts/INDEX.md").write_text("# Legacy format", encoding="utf-8")
        items = registry(self.root)
        self.assertEqual(filter_projects(items), [])
        self.assertEqual(filter_projects(items, "demo", True), items)

    def test_blank_workspace_rejected(self):
        with self.assertRaises(ValueError):
            registry(" ")

    def test_prompts(self):
        for mode in MODES:
            pid = "new-site" if mode == "New project" else "demo-site"
            result = make_prompt(self.root, pid, mode, project_root="demo-root")
            self.assertIn(pid, result)
            self.assertIn("AGENTS.md", result)
        self.assertIn("explicitly request save context", make_prompt(self.root, "demo-site", "Save context"))
        self.assertIn("Do not modify files", make_prompt(self.root, "demo-site", "Overview"))
        self.assertIn("Wait before executing", make_prompt(self.root, "demo-site"))

    def test_demo_workspace(self):
        demo = create_demo(self.base / "demo")
        self.assertEqual(registry(demo)[0]["id"], "demo-robot")
        self.assertEqual(verify(demo, "demo-robot"), ([], []))
        self.assertEqual(len(project_files(demo, "demo-robot")), 4)
        self.assertEqual(skills(demo), ["demo-review"])
        self.assertIn("demo-robot", make_prompt(demo, "demo-robot"))
        self.assertEqual(registry(self.root)[0]["id"], "demo-site")

    def test_feature_map_routing(self):
        demo = create_demo(self.base / "demo")
        info = load_feature_map(demo, "demo-robot")
        self.assertEqual(check_feature_map(demo, "demo-robot", info), ([], []))
        self.assertEqual([r["id"] for r in find_features(info, "motor driver")], ["driver"])
        self.assertEqual([r["id"] for r in feature_routes(info, "driver")], ["driver", "design"])
        prompt = make_feature_prompt(demo, "demo-robot", "driver")
        self.assertIn("Focus only on feature driver", prompt)
        self.assertIn("Do not modify files", prompt)
        self.assertIn("workspace:contexts/demo-robot/CURRENT.md#Decisions", prompt)

    def test_feature_map_stale(self):
        demo = create_demo(self.base / "demo")
        index = demo / "contexts/INDEX.md"
        index.write_text(index.read_text(encoding="utf-8").replace("2030-01-01-01", "2030-01-01-02"), encoding="utf-8")
        info = load_feature_map(demo, "demo-robot")
        self.assertTrue(check_feature_map(demo, "demo-robot", info)[1])
        with self.assertRaises(ValueError):
            make_feature_prompt(demo, "demo-robot", "driver")

    def test_feature_map_invalid_paths_dependencies(self):
        demo = create_demo(self.base / "demo")
        info = load_feature_map(demo, "demo-robot")
        info["rows"]["design"]["sources"] = ["workspace:../escape.md", "workspace:missing.md"]
        info["rows"]["design"]["deps"] = ["driver"]
        errors, warnings = check_feature_map(demo, "demo-robot", info)
        self.assertTrue(any("cycle" in e for e in errors))
        self.assertTrue(any("Invalid scoped source" in e for e in errors))
        self.assertTrue(any("missing source" in e for e in errors))
        info["rows"]["design"]["deps"] = ["unknown"]
        self.assertTrue(any("Unknown dependency" in e for e in check_feature_map(demo, "demo-robot", info)[0]))

    def test_feature_map_missing_and_duplicate(self):
        self.assertIsNone(load_feature_map(self.root, "demo-site"))
        self.assertTrue(check_feature_map(self.root, "demo-site", None)[1])
        demo = create_demo(self.base / "demo")
        path = demo / "contexts/demo-robot/FEATURE_MAP.md"
        path.write_text(path.read_text(encoding="utf-8") +
                        "| design | Duplicate | test | workspace:AGENTS.md | - | example |\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            load_feature_map(demo, "demo-robot")

    def test_demo_no_overwrite(self):
        existing = self.base / "existing"
        existing.mkdir()
        marker = existing / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        with self.assertRaises(FileExistsError):
            create_demo(existing)
        self.assertEqual(marker.read_text(encoding="utf-8"), "keep")

    def test_duplicate_new_project(self):
        with self.assertRaises(ValueError):
            make_prompt(self.root, "demo-site", "New project", project_root="demo-root")

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
