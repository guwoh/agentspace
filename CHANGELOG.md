# Changelog

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
