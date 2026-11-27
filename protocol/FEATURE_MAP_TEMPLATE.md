# Feature map

- Project ID: <project-id>
- Source session: <YYYY-MM-DD-NN>

A compact navigation index, not a substitute for the full handoff. Update affected rows after relevant changes. Record verified paths, not guessed ones. A source session refers to the registry session against which the map was reviewed.

| ID | Feature | Keywords | Sources | Depends on | Status |
|---|---|---|---|---|---|
| setup | Setup | install, initialize | project:README.md; project:scripts/setup.py#main | - | example |
| verify | Verification | tests, validation | project:tests/test_setup.py | setup | example |

Replace the sample rows; they are fictional. Use lowercase hyphenated IDs, comma-separated dependency IDs (or `-`), and semicolon-separated sources. Each source must use `project:` (relative to registered project root) or `workspace:` (relative to private AgentSpace root), with an optional `#symbol` locator. Use forward slashes, no absolute paths, parent traversal, or Markdown link syntax in Sources. Status describes coverage or verification, not an automatic test result. Use small maps; split detailed catalogs into separate documents. Search by ID, feature or keywords. Check relevant sources and project instructions before acting. A map with an old source session or missing paths is a hint only; reconcile with the authoritative handoff. Do not claim token savings without measurement.
