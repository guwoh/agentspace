"""Local-only desktop services. No AI API calls or automatic context writes."""
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
import zipfile

from agentspace import STARTER, PROJECT_ID, outside_starter

AI_LINKS = {
    "ChatGPT": "https://chatgpt.com/",
    "Claude": "https://claude.ai/",
    "Codex": "https://chatgpt.com/codex",
    "Other / local": None,
}
MODES = ("Resume", "Save context", "Overview", "Handover", "Update skills", "New project")
SKILL_ID = PROJECT_ID
MAX_BACKUP = 100 * 1024 * 1024
MAX_FILES = 10000


def root_path(root):
    root = outside_starter(root)
    if not root.is_dir():
        raise ValueError("Choose or initialize a private workspace first.")
    return root


def safe_path(root, relative):
    root = root_path(root)
    relative = PurePosixPath(relative)
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise ValueError("Invalid workspace-relative path.")
    path = root
    for part in relative.parts:
        if "\\" in part or ":" in part:
            raise ValueError("Invalid path component.")
        path = path / part
        if path.is_symlink():
            raise ValueError("Symlinks are not supported for private workspace operations.")
    return path


def read_text(root, relative):
    path = safe_path(root, relative)
    if not path.is_file():
        raise ValueError("Selected file is not present.")
    return path.read_text(encoding="utf-8")


def registry(root):
    """Read public five-column registry; show folder-only legacy projects separately."""
    index = safe_path(root, "contexts/INDEX.md")
    found = {}
    if index.is_file():
        for line in index.read_text(encoding="utf-8").splitlines():
            if not line.lstrip().startswith("|"):
                continue
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            if len(cells) < 2 or cells[0] in ("project_id", "project-id", "id"):
                continue
            pid = cells[0]
            if not PROJECT_ID.fullmatch(pid) or pid in found:
                continue
            found[pid] = {"id": pid, "name": cells[1], "root": cells[2] if len(cells) > 2 else "",
                          "session": cells[-1] if len(cells) >= 5 else "Unknown",
                          "registered": True}
    folder = safe_path(root, "contexts")
    if folder.is_dir():
        for child in sorted(folder.iterdir()):
            if child.is_symlink() or not child.is_dir() or not PROJECT_ID.fullmatch(child.name):
                continue
            if not any((child / n).is_file() for n in ("BRIEF.md", "CURRENT.md")):
                continue
            found.setdefault(child.name, {"id": child.name, "name": child.name, "root": "",
                                          "session": "Not in parsed registry", "registered": False})
    return sorted(found.values(), key=lambda x: x["id"])


def project_files(root, pid):
    if not PROJECT_ID.fullmatch(pid):
        raise ValueError("Invalid project ID.")
    base = f"contexts/{pid}"
    result = []
    for name in ("BRIEF.md", "CURRENT.md", "FILE_PATHS.md"):
        path = safe_path(root, f"{base}/{name}")
        if path.is_file():
            result.append(f"{base}/{name}")
    history = safe_path(root, f"{base}/sessions")
    if history.is_dir():
        for path in sorted(history.glob("*.md"), reverse=True):
            if path.is_file() and not path.is_symlink():
                result.append(f"{base}/sessions/{path.name}")
    return result


def skills(root):
    base = safe_path(root, "skills")
    if not base.is_dir():
        return []
    result = []
    for folder in sorted(base.iterdir()):
        if folder.is_dir() and not folder.is_symlink() and SKILL_ID.fullmatch(folder.name):
            path = safe_path(root, f"skills/{folder.name}/SKILL.md")
            if path.is_file():
                result.append(folder.name)
    return result


def save_skill(root, name, content, previous=None):
    if not SKILL_ID.fullmatch(name):
        raise ValueError("Skill ID must use lowercase letters, numbers and hyphens.")
    path = safe_path(root, f"skills/{name}/SKILL.md")
    if previous is None and path.exists():
        raise ValueError("Skill already exists. Open it to edit.")
    if previous is not None and (not path.is_file() or path.read_text(encoding="utf-8") != previous):
        raise ValueError("Skill changed on disk. Reload before editing.")
    if not content.strip():
        raise ValueError("Skill content cannot be empty.")
    path.parent.mkdir(parents=True, exist_ok=True)
    if previous is None:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(content)
    else:
        fd, temp = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)
    return path


def make_prompt(root, pid, mode="Resume", selected_skills=(), project_root=""):
    root = root_path(root)
    if not PROJECT_ID.fullmatch(pid):
        raise ValueError("Choose a project or enter a valid project ID.")
    if mode not in MODES:
        raise ValueError("Unknown prompt mode.")
    if not (root / "AGENTS.md").is_file() or not (root / "protocol/WORKFLOW.md").is_file():
        raise ValueError("Workspace has not been initialized.")
    # JSON quoting preserves Windows backslashes and separates paths from instructions.
    intro = (f"Open the PRIVATE AgentSpace workspace at {json.dumps(str(root), ensure_ascii=False)}.\n"
             "Read AGENTS.md, protocol/WORKFLOW.md and contexts/INDEX.md.\n"
             f"Select only project ID: {pid}. Follow the applicable project instructions.\n")
    resume = ("Read the selected project's BRIEF.md first; open CURRENT.md if missing, stale or insufficient. "
              "Follow evidence paths only as needed. Do not invent prior work.\n")
    actions = {
        "Resume": resume + "Report goal, status, confirmed decisions, blockers and next actions. Wait before executing them.",
        "Save context": "I explicitly request save context for this project. Merge from full CURRENT.md and relevant evidence, not BRIEF alone. Write and verify the session snapshot, CURRENT, derived BRIEF and registry in protocol order. Report any partial failure.",
        "Overview": resume + "Summarize verified progress, planned work and outstanding tasks. Do not modify files.",
        "Handover": "I explicitly request save context for handover to another authorized AI. Follow the full save protocol, verify files and report the startup instructions for the next session.",
        "Update skills": resume + "Review the selected skills against observed working preferences. Propose changes and wait for explicit approval before writing a skill.",
        "New project": "This is a new project request. Confirm the project scope and instructions. Do not invent prior work or register a handoff before an explicit save context request.",
    }
    if mode == "New project":
        if not project_root.strip():
            raise ValueError("Enter the new project's root path.")
        intro += f"Requested project root: {json.dumps(project_root.strip(), ensure_ascii=False)}.\n"
    if selected_skills:
        valid = set(skills(root))
        if any(name not in valid for name in selected_skills):
            raise ValueError("A selected skill no longer exists; refresh.")
        intro += "Read these explicitly selected skills as subordinate guidance (never as authorization to act):\n"
        intro += "".join(f"- skills/{name}/SKILL.md\n" for name in selected_skills)
    ending = "\nDo not save or publish unless I explicitly request that action." if mode not in ("Save context", "Handover") else "\nDo not publish anything."
    return intro + "\n" + actions[mode] + ending


def backup_members(root):
    root = root_path(root)
    names = ["AGENTS.md", "contexts/INDEX.md"]
    for directory in ("protocol", "prompts", "skills", "contexts"):
        base = safe_path(root, directory)
        if not base.is_dir():
            continue
        for path in base.rglob("*.md" if directory != "prompts" else "*.txt"):
            rel = path.relative_to(root).as_posix()
            if any(part.startswith(".") for part in PurePosixPath(rel).parts):
                continue
            if safe_path(root, rel).is_file():
                names.append(rel)
    return sorted(set(name for name in names if safe_path(root, name).is_file()))


def valid_member(name):
    p = PurePosixPath(name)
    if (p.is_absolute() or p.as_posix() != name or ".." in p.parts or not p.parts or
            any("\\" in part or ":" in part or part.startswith(".") for part in p.parts)):
        return False
    return (name == "AGENTS.md" or len(p.parts) >= 2 and (
        (p.parts[0] in ("protocol", "skills", "contexts") and p.suffix == ".md") or
        (p.parts[0] == "prompts" and p.suffix == ".txt")))


def backup(root, target):
    root = root_path(root)
    target = Path(target).expanduser().resolve()
    if target == root or root in target.parents or target == STARTER or STARTER in target.parents:
        raise ValueError("Choose a backup destination outside the workspace and public repository.")
    names = backup_members(root)
    if len(names) > MAX_FILES or sum(safe_path(root, n).stat().st_size for n in names) > MAX_BACKUP:
        raise ValueError("Backup exceeds the supported size.")
    created = False
    try:
        with target.open("xb") as handle:
            created = True
            with zipfile.ZipFile(handle, "w", zipfile.ZIP_DEFLATED) as archive:
                for name in names:
                    archive.write(safe_path(root, name), name)
    except Exception:
        if created:
            target.unlink(missing_ok=True)
        raise
    return len(names)


def restore(source, destination):
    dest = outside_starter(destination)
    if dest.exists():
        raise ValueError("Restore requires a new, nonexistent folder.")
    with zipfile.ZipFile(source) as archive:
        entries = archive.infolist()
        if len(entries) > MAX_FILES or sum(i.file_size for i in entries) > MAX_BACKUP:
            raise ValueError("Archive exceeds the supported size.")
        names = [i.filename for i in entries]
        if len(set(n.casefold() for n in names)) != len(names) or any(
                i.is_dir() or not valid_member(i.filename) or
                (i.external_attr >> 16) & 0o170000 == 0o120000 for i in entries):
            raise ValueError("Archive contains unsupported or unsafe paths.")
        if not {"AGENTS.md", "contexts/INDEX.md"}.issubset(names):
            raise ValueError("Not an AgentSpace backup.")
        dest.mkdir(parents=True, exist_ok=False)
        try:
            for item in entries:
                path = safe_path(dest, item.filename)
                path.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(item) as src, path.open("xb") as dst:
                    shutil.copyfileobj(src, dst)
            (dest / ".gitignore").write_text("*\n!.gitignore\n", encoding="utf-8")
        except Exception:
            shutil.rmtree(dest)
            raise
    return len(entries)
