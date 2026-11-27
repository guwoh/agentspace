# AgentSpace Desktop v0.2.0 (Developer Preview)

A local application over the same private Markdown workspace as the CLI. It does not run an AI, send API requests, create MCP credentials or upload data.

## Launch

From the public starter checkout or extracted source release:

```bash
python3 -B scripts/desktop.py
```

Windows: use `python -B scripts/desktop.py`. Python 3.8+ and Tkinter are required (on Linux, install your distribution's Tkinter package if missing). The desktop uses Tkinter so no Qt installation is required. Linux and Windows launchers can point to this command. The optional CI workflow also defines standalone desktop bundles, not OS installers.

To open an existing workspace without copying or migrating it:

```bash
python3 -B scripts/desktop.py --workspace ~/work/agentspace-private
```

Choose a separate private folder and click Initialize only if it needs starter files. Existing files are never overwritten. For a new project, use New project to generate the first prompt; the AI registers the project on the first explicit save. Existing folder-only contexts can be viewed even if the registry uses a legacy format; the structural checker expects the public five-column schema.

## Main actions

- Projects: inspect the registry and open a project, generate a startup prompt, or check the selected context.
- Prompt studio: choose Resume, Save context, Overview, Handover, Update skills or New project. Generate & copy, open the selected AI, then paste the prompt manually. Provider selection only changes the browser destination.
- Context & history: read brief, full handoff, file manifest and saved snapshots. Historical snapshots are never edited by this app.
- Skills: create/edit private `skills/<id>/SKILL.md` files; select skills explicitly to add paths to the prompt. Skills are guidance, not permissions. Close other writers before saving.
- Connections: open AI clients and the DevSpace setup guide; check whether the DevSpace executable is on PATH. This does not authenticate or verify an active MCP connection.
- Backup & settings: create an unencrypted ZIP of private Markdown records and prompt text (no source repositories or binary data). Restore only into a new folder; review project paths before use. Keep backups private. Use manual interface font sizing for mixed displays.

No context is generated or saved merely by clicking Copy. The user sends the prompt and the authorized AI performs the workflow. Close other writers before backup and skill edits. Backups may contain sensitive text and are not a substitute for full machine backups.

## Verification and releases

```bash
python3 -B scripts/test_agentspace.py -v
python3 -B scripts/test_desktop.py -v
python3 scripts/check_public.py --history
python3 -B scripts/desktop.py --smoke-test
python3 -B scripts/package_release.py ../AgentSpace-preview.zip
```

The smoke test requires a graphical display. Source packaging is deterministic and uses the public allowlist. Review the exact tree and history before publishing. The release workflow builds a source archive and platform-specific desktop bundles as CI artifacts on manual dispatch; it does not publish a release. Native installers, actual multi-monitor DPI behavior, and real cross-account handoff remain acceptance tasks.

See [privacy](PRIVACY.md), [DevSpace](DEVSPACE.md) and [workflow](../protocol/WORKFLOW.md).
