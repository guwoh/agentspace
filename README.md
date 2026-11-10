# AgentSpace
**Portable project handoffs for AI-assisted work. Save once. Resume in another chat.**

[Tiếng Việt](README.vi.md) · [DevSpace setup](docs/DEVSPACE.md) · [Workflow](protocol/WORKFLOW.md)

AgentSpace is a small, file-based working convention for people using AI across multiple projects, conversations, accounts, and clients. The AI reads a shared protocol, selects a project, and restores its latest saved handoff. You decide when to save by typing **save context**.

This is a starter kit, not a background service, model memory plugin, or chat-history exporter. It cannot recover conversations that were never saved, guarantee an agent follows instructions, or make cloud inference local.

## Quick start
Keep this public starter checkout separate from your private working folder:

```bash
git clone https://github.com/guwoh/agentspace.git agentspace-starter
mkdir -p ~/work/agentspace-private/contexts
cp agentspace-starter/AGENTS.md ~/work/agentspace-private/
cp -R agentspace-starter/protocol agentspace-starter/prompts ~/work/agentspace-private/
cp agentspace-starter/templates/INDEX.md ~/work/agentspace-private/contexts/INDEX.md
```

The example commands target Bash (Linux/macOS/WSL). Do not overwrite existing files when adopting an existing setup. No server or AI API key is required for AgentSpace itself. Your AI needs file tools that can access the private working folder and selected project folders; [DevSpace](docs/DEVSPACE.md) is one option.

1. Connect your AI's file tools.
2. Copy [prompts/START.txt](prompts/START.txt), replacing `<AGENTSPACE_ROOT>` with the absolute path to your **private** working folder.
3. Name the project, or let the agent list registered projects.
4. Work normally. Type `save context` to create a handoff.
5. In a new chat or authorized account, reconnect file access and send the same startup prompt.

The private context layout uses:
- `contexts/INDEX.md`: project IDs, local paths, and latest session IDs.
- `contexts/<project-id>/CURRENT.md`: latest handoff.
- `contexts/<project-id>/sessions/YYYY-MM-DD-NN.md`: immutable saved snapshots.

Read only the selected project. Keep research, software, coursework, and other projects separate. Register a new project on its first requested save.

## What gets saved
Goal, confirmed decisions and reasons, completed work and checks, open questions, next actions, and relevant file paths. Mark plans and assumptions explicitly. See [the template](protocol/HANDOFF_TEMPLATE.md) and [a fictional example](examples/HANDOFF.md).

## Public starter vs private data
Publish only generic rules, templates, and fictional examples. Keep real contexts, paths, recordings, attachments, credentials, and transcripts in the private working folder. The starter uses a deny-by-default Git ignore list and an [allowlist/content audit](docs/PRIVACY.md); these are checks, not a guarantee against every kind of sensitive information.

## Verification and limits
Run `python3 scripts/check_public.py` from the starter root. After staging, run `python3 scripts/check_public.py --staged`; after committing, use `--history` too. Tests here check the public package, not cross-account behavior or a real DevSpace installation. Use [the manual acceptance test](docs/TESTING.md) to verify your own environment.

No automatic save runs after each chat turn. Work since the last successful save can be lost. File snapshots do not preserve an entire model context window. Avoid concurrent writers to the same handoff.

## Credits and license
Original workflow documents written for this starter. Inspired by [AGENTS.md](https://github.com/agentsmd/agents.md), [Cline Memory Bank](https://docs.cline.bot/best-practices/memory-bank), and [Beads](https://github.com/gastownhall/beads).
[DevSpace](https://github.com/Waishnav/devspace) is an independent upstream project; no upstream code is bundled.
MIT — see [LICENSE](LICENSE).
