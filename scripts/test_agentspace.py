#!/usr/bin/env python3
"""Synthetic tests only; no real context or project files."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from agentspace import initialize, verify, STARTER

SESSION = "2030-01-01-01"
FULL = f"# Fictional handoff\n- Session ID: {SESSION}\n"
BRIEF = f"# Fictional brief\n- Project ID: demo-site\n- Source session: {SESSION}\n"


class AgentSpaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "private"
        initialize(self.root)
        self.project = self.root / "contexts" / "demo-site"
        (self.project / "sessions").mkdir(parents=True)
        self.current = self.project / "CURRENT.md"
        self.current.write_text(FULL, encoding="utf-8")
        self.snapshot = self.project / "sessions" / (SESSION + ".md")
        self.snapshot.write_bytes(self.current.read_bytes())
        self.brief = self.project / "BRIEF.md"
        self.brief.write_text(BRIEF, encoding="utf-8")
        self.registry = self.root / "contexts" / "INDEX.md"
        self.registry.write_text(
            f"| demo-site | Fictional | demo-project | demo-site/BRIEF.md | {SESSION} |\n",
            encoding="utf-8")

    def check(self):
        return verify(self.root, "demo-site")

    def test_valid(self):
        self.assertEqual(self.check(), ([], []))

    def test_init_preserves_existing(self):
        original = self.registry.read_bytes()
        self.assertEqual(initialize(self.root), (0, 7))
        self.assertEqual(self.registry.read_bytes(), original)

    def test_public_root_rejected(self):
        with self.assertRaises(ValueError):
            initialize(STARTER / "private")

    def test_invalid_project_id(self):
        with self.assertRaises(ValueError):
            verify(self.root, "../demo-site")

    def test_stale_brief(self):
        self.brief.write_text(BRIEF.replace(SESSION, "2030-01-01-02"), encoding="utf-8")
        self.assertTrue(self.check()[0])

    def test_snapshot_mismatch(self):
        self.snapshot.write_text("changed", encoding="utf-8")
        self.assertTrue(self.check()[0])

    def test_missing_snapshot(self):
        self.snapshot.unlink()
        self.assertTrue(self.check()[0])

    def test_registry_mismatch(self):
        self.registry.write_text(self.registry.read_text().replace(SESSION, "2030-01-01-02"))
        self.assertTrue(self.check()[0])

    def test_hash(self):
        digest = hashlib.sha256(self.current.read_bytes()).hexdigest()
        self.brief.write_text(BRIEF + f"- Source SHA-256: {digest}\n", encoding="utf-8")
        self.assertEqual(self.check(), ([], []))
        self.brief.write_text(BRIEF + "- Source SHA-256: invalid\n", encoding="utf-8")
        self.assertTrue(self.check()[0])

    def test_bilingual_header_with_historical_metadata(self):
        full = FULL + "\n## Earlier handoff\n- Session ID: 2029-12-31-01\n"
        self.current.write_text(full, encoding="utf-8")
        self.snapshot.write_bytes(self.current.read_bytes())
        digest = hashlib.sha256(self.current.read_bytes()).hexdigest()
        self.brief.write_text(
            f"# Fictional brief\n- Project ID: demo-site.\n"
            f"- Phiên nguồn: {SESSION}; cập nhật: 2030-01-01.\n"
            f"- SHA-256 của CURRENT.md: `{digest}` (đã kiểm tra)\n",
            encoding="utf-8")
        self.assertEqual(self.check(), ([], []))

    def test_ambiguous_hash(self):
        digest = hashlib.sha256(self.current.read_bytes()).hexdigest()
        self.brief.write_text(BRIEF + f"- Source SHA-256: {digest}\n"
                              f"- SHA256 nguồn: {digest}\n", encoding="utf-8")
        self.assertTrue(self.check()[0])

    def test_legacy(self):
        self.brief.unlink()
        self.registry.write_text(self.registry.read_text().replace("BRIEF.md", "CURRENT.md"))
        errors, warnings = self.check()
        self.assertFalse(errors)
        self.assertTrue(warnings)


if __name__ == "__main__":
    unittest.main()
