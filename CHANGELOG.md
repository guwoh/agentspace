# Changelog

## Unreleased — v0.3.0-dev

- Bundle an optional DevSpace configuration GUI with a separate launch action and bilingual remote-work setup guides. DevSpace itself is installed independently.

- Add optional Markdown feature maps with scoped source paths, keyword search, dependency routes, session checks and focused read-only prompts in CLI and desktop.
- Add map template, brief-first routing instructions and a fictional demo map. Preserve existing full handoffs and snapshots.

- Add a temporary fictional robot workspace and one-click Try demo / Exit demo for first-time users.
- Improve onboarding instructions and product positioning in both READMEs.
- Reject duplicate new-project IDs and clear selected skills and stale project fields on workspace changes.
- Add project search, optional folder-only entries and one-click resume prompt copying.
- Add app-owned fonts, keyboard zoom, initial window sizing based on font metrics, compact navigation and scrollable pages for small/high-DPI displays.
- Synchronize project selection between the browser and prompt studio; reject blank workspace paths.
- Add five automated regression tests and extend GUI smoke testing to demo, search, clipboard and small-window layout.

## v0.2.0 — Developer Preview (2026-11-27)

First versioned source release. The 22 automated core tests and basic Ubuntu GUI/clipboard checks passed. Native bundles, multi-monitor DPI, and real cross-account acceptance remain pending.

- Fix the context checker for bilingual metadata and historical handoffs embedded in the full record. Reject ambiguous hashes and add regression tests.

- Add desktop project browser, prompt studio, read-only context history, skill editor, AI client links and private backup/restore.
- Add portable source package builder, CI artifact workflow and desktop regression tests.
- Add bilingual README, a project banner and a workflow diagram.
- Use Tkinter for the initial dependency-light desktop. Native installers and cross-account acceptance are pending.

- Add a dependency-free private workspace initializer that never overwrites existing files.
- Add a read-only consistency checker for a selected project's registry, full handoff, snapshot and optional brief hash.
- Add synthetic regression tests and run them in CI.
- Document the private/public separation and command-line setup.

## Previous starter

- File-based project registry, full handoffs and explicit save protocol.
- Brief-first resume, fictional examples, bilingual documentation and public package audit.
