"""Companion GUI tests; never touch real DevSpace config, credentials or service."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import devspace_gui as gui


class DevSpaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.config = self.root / "config.json"
        self.config.write_text(json.dumps({"port": 7676, "workspaces": {"allowedRoots": [str(self.root)]}, "extra": 123}), encoding="utf-8")

    def test_https(self):
        self.assertEqual(gui.normalize_url(" https://service.example.com/mcp/ "), "https://service.example.com")
        for url in ("http://service.example.com", "https://user:pass@service.example.com", "https://service.example.com?x=1", "https://service.example.com/other"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                gui.normalize_url(url)

    def test_preserve_unknown_config_and_backup(self):
        before = self.config.read_bytes()
        gui.save_config(self.config, "https://service.example.com", None, before)
        self.assertEqual(gui.read_config(self.config)["extra"], 123)
        self.assertEqual(self.config.with_name("config.json.gui-backup").read_bytes(), before)
        self.assertEqual(gui.read_config(self.config)["workspaces"]["allowedRoots"], [str(self.root)])

    def test_concurrent_config_rejected(self):
        before = self.config.read_bytes()
        self.config.write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            gui.save_config(self.config, "", None, before)
        self.assertEqual(self.config.read_text(), "{}")

    def test_invalid_roots_rejected(self):
        before = self.config.read_bytes()
        with self.assertRaises(ValueError):
            gui.save_config(self.config, "", [], before)
        with self.assertRaises(OSError):
            gui.save_config(self.config, "", [str(self.root / "missing")], before)
        self.assertEqual(self.config.read_bytes(), before)

    def test_explicit_owner_read(self):
        auth = self.root / "auth.json"
        auth.write_text(json.dumps({"ownerToken": "fictional-demo-value"}), encoding="utf-8")
        self.assertEqual(gui.read_owner_password(auth), "fictional-demo-value")
        auth.write_text("{}", encoding="utf-8")
        with self.assertRaises(ValueError):
            gui.read_owner_password(auth)

    def test_status_no_systemd(self):
        with patch.object(gui.subprocess, "run", side_effect=FileNotFoundError), patch.object(gui, "probe", return_value="mock response"):
            self.assertIn("manual / systemd unavailable", gui.status({"port": 7676}, ""))


if __name__ == "__main__":
    unittest.main()
