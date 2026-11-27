#!/usr/bin/env python3
"""Initialize a private AgentSpace folder and verify a saved project."""
import argparse
import hashlib
from pathlib import Path
import re
import sys

STARTER = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
STARTER_FILES = {
    "AGENTS.md": "AGENTS.md",
    "protocol/WORKFLOW.md": "protocol/WORKFLOW.md",
    "protocol/HANDOFF_TEMPLATE.md": "protocol/HANDOFF_TEMPLATE.md",
    "protocol/BRIEF_TEMPLATE.md": "protocol/BRIEF_TEMPLATE.md",
    "protocol/FEATURE_MAP_TEMPLATE.md": "protocol/FEATURE_MAP_TEMPLATE.md",
    "prompts/START.txt": "prompts/START.txt",
    "templates/INDEX.md": "contexts/INDEX.md",
}
PROJECT_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SESSION_ID = re.compile(r"\d{4}-\d{2}-\d{2}-\d{2,}")
PRIVATE_IGNORE = "# Private AgentSpace data: do not publish.\n*\n!.gitignore\n"


def outside_starter(root):
    root = Path(root).expanduser().resolve()
    if root == STARTER or STARTER in root.parents:
        raise ValueError("private root must be outside the public starter")
    return root


def initialize(root):
    root = outside_starter(root)
    sources = {target: (STARTER / source).read_bytes()
               for source, target in STARTER_FILES.items()}
    sources[".gitignore"] = PRIVATE_IGNORE.encode()
    created = skipped = 0
    # Preflight each target and its ancestors; never follow a destination symlink.
    for name in sources:
        target = root / name
        for parent in [target, *target.parents]:
            if parent == root:
                break
            if parent.is_symlink():
                raise ValueError("symlink in private starter destination")
        if target.exists() and not target.is_file():
            raise ValueError("non-file at private starter destination")
    for name, data in sources.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("xb") as handle:
                handle.write(data)
            created += 1
        except FileExistsError:
            skipped += 1
    return created, skipped


def field(text, name):
    # Metadata belongs to the opening header, not quoted historical handoffs.
    header = []
    for line in text.splitlines():
        if re.match(r"^#{2,6}\s", line):
            break
        header.append(line)
    aliases = {
        "Source session": ("Source session", "Phiên nguồn"),
        "Source SHA-256": ("Source SHA-256", "SHA-256 nguồn", "SHA256 nguồn",
                           "SHA-256 của CURRENT.md"),
    }
    labels = aliases.get(name, (name,))
    pattern = r"^[ \t]*[-*][ \t]+(?:" + "|".join(map(re.escape, labels)) + r"):[ \t]*(.*)$"
    matches = re.findall(pattern, "\n".join(header), re.MULTILINE)
    if not matches:
        return None
    if len(matches) != 1:
        return ""  # Ambiguous metadata is invalid, including an optional hash.
    value = matches[0].strip()
    # Older bilingual records append explanatory annotations.
    if name == "Project ID":
        value = re.split(r",\s*alias\b", value, maxsplit=1, flags=re.I)[0]
    elif name in ("Session ID", "Source session", "Source SHA-256"):
        value = re.split(r"\s+(?:·|\()|;\s*", value, maxsplit=1)[0]
    return value.strip().rstrip(".").strip("`")


def verify(root, project_id):
    root = outside_starter(root)
    if not PROJECT_ID.fullmatch(project_id):
        raise ValueError("invalid project ID")
    contexts = root / "contexts"
    project = contexts / project_id
    if contexts.is_symlink() or project.is_symlink():
        raise ValueError("symlink in context directory")
    errors, warnings = [], []

    def read(path):
        if path.is_symlink() or not path.is_file():
            errors.append(f"{path.name}: missing regular file")
            return None
        try:
            return path.read_bytes()
        except OSError:
            errors.append(f"{path.name}: unreadable file")
            return None

    registry = read(contexts / "INDEX.md")
    current = read(project / "CURRENT.md")
    if registry is None or current is None:
        return errors, warnings
    registry_text, full = registry.decode("utf-8"), current.decode("utf-8")
    session = field(full, "Session ID")
    if not session or not SESSION_ID.fullmatch(session):
        errors.append("CURRENT.md: invalid or missing session ID")
        return errors, warnings
    sessions = project / "sessions"
    if sessions.is_symlink():
        errors.append("sessions: symlink is not supported")
    else:
        snapshot = read(sessions / (session + ".md"))
        if snapshot is not None and snapshot != current:
            errors.append("CURRENT.md differs from its session snapshot")

    rows = []
    for line in registry_text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if cells and cells[0] == project_id:
            rows.append(cells)
    brief_path = project / "BRIEF.md"
    brief_present = brief_path.exists() or brief_path.is_symlink()
    entry = "BRIEF.md" if brief_present else "CURRENT.md"
    if len(rows) != 1 or len(rows[0]) != 5:
        errors.append("INDEX.md: expected one matching five-column project row")
    else:
        row = rows[0]
        if row[4] != session:
            errors.append("INDEX.md: latest session differs from CURRENT.md")
        expected = f"{project_id}/{entry}"
        link = re.fullmatch(r"\[[^\]]+\]\(([^)]+)\)", row[3])
        if (link.group(1) if link else row[3]) != expected:
            errors.append("INDEX.md: entry point differs from expected context file")
    if not brief_present:
        warnings.append("BRIEF.md absent; legacy CURRENT.md entry point")
    else:
        raw = read(brief_path)
        if raw is not None:
            brief = raw.decode("utf-8")
            if field(brief, "Project ID") != project_id:
                errors.append("BRIEF.md: project ID mismatch")
            if field(brief, "Source session") != session:
                errors.append("BRIEF.md: source session mismatch")
            digest = field(brief, "Source SHA-256")
            if digest is not None and digest != hashlib.sha256(current).hexdigest():
                errors.append("BRIEF.md: source hash mismatch")
    return errors, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="create missing private starter files; never overwrite")
    init.add_argument("root")
    check = sub.add_parser("check", help="read-only consistency check for one project")
    check.add_argument("root")
    check.add_argument("project_id")
    start = sub.add_parser("start", help="generate a startup prompt for one project")
    start.add_argument("root")
    start.add_argument("project_id")
    status = sub.add_parser("status", help="list projects from the private registry")
    status.add_argument("root")
    fmap = sub.add_parser("map", help="list or search feature routes without opening sources")
    fmap.add_argument("root")
    fmap.add_argument("project_id")
    fmap.add_argument("query", nargs="?", default="")
    fmap.add_argument("--feature", help="exact feature ID; include dependency routes")
    mapcheck = sub.add_parser("map-check", help="check map freshness, dependencies and paths")
    mapcheck.add_argument("root")
    mapcheck.add_argument("project_id")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            created, skipped = initialize(args.root)
            print(f"PASS: created {created} files; preserved {skipped} existing files")
            print("Connect your AI file tools and use prompts/START.txt in the private root.")
            return 0
        if args.command in ("map", "map-check"):
            from desktop_core import load_feature_map, check_feature_map, find_features, feature_routes
            info = load_feature_map(args.root, args.project_id)
            if args.command == "map-check":
                errors, warnings = check_feature_map(args.root, args.project_id, info)
                for item in warnings:
                    print("WARN:", item)
                for item in errors:
                    print("FAIL:", item)
                if not errors and not warnings:
                    print("PASS: feature map session, dependencies and source paths")
                return int(bool(errors or warnings))
            errors, warnings = check_feature_map(args.root, args.project_id, info)
            for item in errors + warnings:
                print("WARN:", item, file=sys.stderr)
            rows = (feature_routes(info, args.feature) if args.feature
                    else find_features(info, args.query))
            for row in rows:
                print(f"{row['id']}\t{row['name']}\t{'; '.join(row['sources'])}\t{','.join(row['deps']) or '-'}\t{row['status']}")
            return int(bool(errors or warnings))
        if args.command in ("start", "status"):
            from desktop_core import make_prompt, registry
            if args.command == "start":
                print(make_prompt(args.root, args.project_id))
            else:
                for item in registry(args.root):
                    print(f"{item['id']}\t{item['name']}\t{item['session']}")
            return 0
        errors, warnings = verify(args.root, args.project_id)
        for warning in warnings:
            print("WARN:", warning)
        for error in errors:
            print("FAIL:", error)
        if not errors:
            print("PASS: project registry, full snapshot and available brief agree")
        return int(bool(errors))
    except (OSError, ValueError) as exc:
        print("FAIL:", type(exc).__name__, "- operation could not complete", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
