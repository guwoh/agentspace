# Testing the starter
## Package checks
Run the commands in [PRIVACY.md](PRIVACY.md). The standard-library Python checker has synthetic negative cases for secrets, local home paths, unexpected files, and binary data.

## Manual handoff acceptance
Use a private throwaway project, not real work:
1. Copy the starter into a private working folder using the README instructions.
2. Connect file tools and send the startup prompt without a project.
3. Confirm the AI asks for a project instead of assuming one.
4. Name a fictional project. Confirm it says no prior handoff exists.
5. Give it a fictional goal and an unfinished task; say save context.
6. Confirm a snapshot, identical CURRENT.md, and index entry were written and read back.
7. Change one fictional decision; save again. Confirm a new ID, unchanged old snapshot, updated CURRENT and index.
8. Open a genuinely new chat or authorized account, reconnect tools, and send the startup prompt.
9. Confirm the summary distinguishes completed work from plans and preserves the reason for the changed decision.
10. Confirm merely quoting the phrase save context does not trigger a save.
11. Switch to a second fictional project and verify no unrelated context is loaded.

Do not claim step 8 passed based on rereading files in the same conversation. No cross-account or platform compatibility claim is implied by the package checks.
