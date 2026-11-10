#!/usr/bin/env python3
"""Audit the generic public starter. No dependencies; no file writes."""
import argparse
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ALLOWED = {
    "README.md", "README.vi.md", "AGENTS.md", "LICENSE", ".gitignore",
    "protocol/WORKFLOW.md", "protocol/HANDOFF_TEMPLATE.md",
    "prompts/START.txt", "templates/INDEX.md", "examples/HANDOFF.md",
    "docs/DEVSPACE.md", "docs/PRIVACY.md", "docs/TESTING.md",
    "scripts/check_public.py", ".github/workflows/verify.yml",
}
PATTERNS = [
    ("local home path", re.compile(r"/(?:home|Users)/[^\s/<>]+")),
    ("Windows user path", re.compile(r"[A-Za-z]:\\Users\\", re.I)),
    ("private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")),
    ("API token", re.compile(r"sk-[A-Za-z0-9_-]{24,}")),
    ("private tunnel hostname", re.compile(r"https?://[^\s/]+\.(?:ts\.net|trycloudflare\.com|ngrok-free\.app)")),
]
ROOT = Path(__file__).resolve().parents[1]

def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])

def audit(path, data, deny=()):
    errors = []
    if path not in ALLOWED:
        errors.append("file outside public allowlist")
    try:
        value = data.decode("utf-8")
    except UnicodeDecodeError:
        return errors + ["non-text data"]
    for name, pattern in PATTERNS:
        if pattern.search(value):
            errors.append(name)
    if any(term and term.casefold() in value.casefold() for term in deny):
        errors.append("user-supplied private marker")
    return errors

def self_test():
    assert not audit("README.md", b"Generic documentation.")
    assert audit("contexts/private/CURRENT.md", b"Generic documentation.")
    assert audit("README.md", ("/" + "home/" + "someone/project").encode())
    assert audit("README.md", ("gh" + "p_" + "A" * 30).encode())
    assert audit("README.md", b"private marker", ("private marker",))
    assert audit("README.md", b"\xff")
    assert not audit("README.md", b"https://service.example.com/mcp")
    print("PASS: allowlist, private paths, token, custom marker, binary rejection, placeholder URL")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--staged", action="store_true", help="inspect Git index blobs, not worktree copies")
    parser.add_argument("--history", action="store_true", help="also inspect every tree/blob in reachable commits")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--deny", action="append", default=[], help="additional private strings; never echoed")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    failures = []
    seen = set()

    def inspect(path, data, mode=None):
        seen.add(path)
        if mode is not None and mode not in ("100644", "100755"):
            failures.append((path, "symlink/submodule or unsupported Git mode"))
        for error in audit(path, data, args.deny):
            failures.append((path, error))

    if args.staged:
        for row in git("ls-files", "--stage", "-z").split(b"\0"):
            if not row:
                continue
            meta, raw_path = row.split(b"\t", 1)
            mode, oid, stage = meta.decode().split()
            path = raw_path.decode()
            if stage != "0":
                failures.append((path, "unmerged index entry"))
                continue
            inspect(path, git("cat-file", "blob", oid), mode)
    else:
        for file in ROOT.rglob("*"):
            rel = file.relative_to(ROOT)
            if ".git" in rel.parts:
                continue
            if file.is_symlink():
                failures.append((rel.as_posix(), "symlink"))
            elif file.is_file():
                inspect(rel.as_posix(), file.read_bytes())

    missing = ALLOWED - seen
    for path in sorted(missing):
        failures.append((path, "required public file missing"))

    if args.history:
        for commit in git("rev-list", "--all").decode().splitlines():
            for row in git("ls-tree", "-r", "-z", commit).split(b"\0"):
                if not row:
                    continue
                meta, raw_path = row.split(b"\t", 1)
                mode, kind, oid = meta.decode().split()
                path = raw_path.decode()
                if kind != "blob":
                    failures.append((path, "non-blob history entry"))
                    continue
                inspect(path, git("cat-file", "blob", oid), mode)

    # Verify relative Markdown links in the public worktree.
    for name in sorted(ALLOWED):
        file = ROOT / name
        if file.suffix != ".md" or not file.is_file():
            continue
        for target in re.findall(r"\]\(([^)]+)\)", file.read_text()):
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", target) or target.startswith("#"):
                continue
            target = target.split("#", 1)[0]
            if target and not (file.parent / target).exists():
                failures.append((name, "broken relative link"))
    for path, reason in failures:
        print("FAIL:", path, "-", reason)
    if failures:
        return 1
    print("PASS: public allowlist, content scan, required files, relative links" +
          ("; Git index checked" if args.staged else "") +
          ("; reachable commit history checked" if args.history else ""))
    return 0

if __name__ == "__main__":
    sys.exit(main())
