# Testing the starter
## Package checks
Run `python3 -B scripts/test_agentspace.py -v` from the starter root. The synthetic tests exercise safe initialization, existing-file preservation, path validation, valid and stale handoffs, mismatched snapshots and hashes, and legacy context. Run the commands in [PRIVACY.md](PRIVACY.md). The standard-library Python checker has synthetic negative cases for secrets, local home paths, unexpected files, and binary data.

The checker supports English and Vietnamese brief metadata, reads the opening metadata instead of embedded historical handoffs, and rejects ambiguous hashes. Redirect-only folders without their own session are not independent saved projects.

## Desktop checks

Run `python3 -B scripts/test_desktop.py -v` for registry, prompts, skills and backup/restore tests. Run `python3 -B scripts/desktop.py --smoke-test` with a display; manually verify clipboard, AI links, skill editing, backup restoration and font sizes on each platform. See [desktop guide](DESKTOP.md).

## Manual handoff acceptance
Use a private throwaway project, not real work:
1. Copy the starter into a private working folder using the README instructions.
2. Connect file tools and send the startup prompt without a project.
3. Confirm the AI asks for a project instead of assuming one.
4. Name a fictional project. Confirm it says no prior handoff exists.
5. Give it a fictional goal and an unfinished task; say save context.
6. Confirm the snapshot and CURRENT.md match. Check that BRIEF.md and the index point to the same session ID and to the right files.
7. Change one fictional decision and save again. Verify the first snapshot stayed intact, the new full files match, and the brief and index show the new ID.
8. Open a genuinely new chat or authorized account. Reconnect tools and send the startup prompt.
9. Confirm the AI starts with the brief and opens the relevant full section when asked for the evidence behind a decision. Check that its summary preserves the reason for the change.
10. In the throwaway project, set the brief's source session to the first ID and resume again. Confirm the AI checks CURRENT.md. Repeat with a project that has a full handoff and no brief.
11. Confirm that quoting the phrase save context leaves the saved files intact.
12. Switch to a second fictional project and verify that the AI reads only the context for that project.

Do not claim step 8 passed based on rereading files in the same conversation. No cross-account or platform compatibility claim is implied by the package checks.
