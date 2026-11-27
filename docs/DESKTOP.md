# AgentSpace Desktop (development branch)

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

## Try the app without an AI connection

Click **Try demo** in the toolbar. The app creates a new, temporary fictional robot workspace with a brief, full handoff, matching snapshot, registry and demo skill. Use Start project, copy a prompt, inspect history and check the context. Exit demo returns to the previous workspace; the temporary demo is cleaned up on normal app exit. Demo edits are not permanent. Do not confuse a generated prompt with a successful AI handoff.

## Feature map

Select a project, then open Feature map. Search feature IDs, names or keywords, select a result, inspect its dependency routes, and copy a focused read-only prompt. Validate / reload checks the source session, dependencies and existence of referenced files; it does not inspect source code or symbols. Missing, stale or invalid maps require review before focused prompt generation. To create a map, use the [template](../protocol/FEATURE_MAP_TEMPLATE.md) in the private project context folder. The demo has a fictional map.

## Main actions

- Projects: search by project ID or name, browse registered projects, copy a resume prompt directly or inspect the selected context. Enable Show folder-only to inspect legacy/unregistered folders (including redirects); they are not counted as registered projects. Ctrl+F focuses project search.
- Prompt studio: choose Resume, Save context, Overview, Handover, Update skills or New project. Generate & copy, open the selected AI, then paste the prompt manually. Provider selection only changes the browser destination.
- Context & history: read brief, full handoff, file manifest and saved snapshots. Historical snapshots are never edited by this app.
- Skills: create/edit private `skills/<id>/SKILL.md` files; select skills explicitly to add paths to the prompt. Skills are guidance, not permissions. Close other writers before saving.
- Connections: open AI clients, launch the optional DevSpace GUI, and check whether the DevSpace executable is on PATH. See the [English guide](DEVSPACE.md) or [Vietnamese guide](DEVSPACE.vi.md). This does not authenticate or verify an active MCP connection.
- Backup & settings: create an unencrypted ZIP of private Markdown records and prompt text (no source repositories or binary data). Restore only into a new folder; review project paths before use. Keep backups private. Use Ctrl+plus / Ctrl+minus or the settings buttons to adjust text size; Ctrl+0 resets it. The initial window uses measured font metrics and screen bounds. Pages scroll vertically and horizontally when content does not fit. Tk follows the operating system's global scaling; automatic per-monitor DPI switching is not guaranteed.

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
