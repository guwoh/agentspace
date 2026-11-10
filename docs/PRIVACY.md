# Public package review
This repository is deliberately a generic starter. Private runtime data belongs in a separate folder outside its Git checkout.

## Before publishing any update
1. Write generic documents directly. Do not export or copy a live AgentSpace directory.
2. Keep real contexts, archives, user paths, recordings, screenshots, personal registry entries, tunnel URLs, credentials and raw chat logs out.
3. Inspect `git status --short`, `git diff`, and `git diff --cached`.
4. Stage explicit approved file paths. Avoid `git add .` in a folder containing private data.
5. Run:
```bash
python3 scripts/check_public.py --self-test
python3 scripts/check_public.py
python3 scripts/check_public.py --staged
python3 scripts/check_public.py --staged --history
```
The history check needs a Git repository. An empty history is not evidence about a future commit; rerun after committing.
Use `--deny <private-marker>` locally for known private names or identifiers. The checker reports paths and rule names, not matching secret values.
6. Review `git log --format=fuller` for author/committer identities. Use an appropriate public identity or GitHub noreply address.
7. Review the exact file tree and remote target before pushing.

## Protections and limitations
.gitignore uses an explicit allowlist for public files. It does not protect files already tracked, forced additions, or private text pasted into an allowed file.
The checker rejects unexpected paths, binary data, symlinks, common secret/path patterns, and missing files. It checks staged blobs and reachable history when requested.
A pattern scanner cannot identify every confidential sentence or credential. Human/agent review of all published text is still required.
If sensitive material has already been pushed, deletion in a later commit is insufficient. Stop publication, rotate affected credentials, and follow the hosting provider's history-removal process.

## Reports
For issues and contributions, supply a minimal fictional reproduction. Do not attach your live CURRENT.md, registry, auth configuration, or transcripts.
