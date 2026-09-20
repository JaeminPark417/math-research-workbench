# Ticket harness verification

From the Workbench root, run:

```text
python3 -B -m unittest discover -s meta/research-tickets/tests -q
python3 scripts/vault-lint.py
python3 scripts/validate-release.py --release
```

Use `python` on Windows if that is the configured interpreter. The existing CI matrix runs ticket tests on macOS, Linux and Windows with Python 3.9 and 3.12. Tests use disposable local projects and Git repositories without contacting remotes. The fixture corpus is wholly synthetic; it contains no imported research prose, real source hashes, personal paths, account metadata or actual project records. Store files created by tests stay outside the distribution.

The engine is adapted from the local ticket harness with a dedicated filesystem adapter. Coverage includes bounded indexed queries, Unicode and mathematical excerpts, source/version guards, scoped graphs, idempotent transactions, process interruption/recovery, lock contention, exact-source drift, immutable bound identity, proposals, persistent operational sessions, explicit project/paper enrollment, partial coverage, historical commit evidence, negative/null results, paper revisions and multi-tag queries.

Windows inventories hash source bytes so restored modification times cannot hide edits; `inventory_bytes_read` reports this separately from parsing reads. POSIX uses no-follow directory descriptors; Windows rejects reparse points and uses msvcrt byte locks and path-based publication. No test should skip the entire Windows suite. POSIX FIFO cases run only where supported; Windows prevents renaming an open lock at the OS level. New portability tests exercise native lock exclusion, recovery and path policy; platform-specific limitations are recorded in [the workflow](../research-ticket-workflow.md). The harness is not an adversarial filesystem sandbox or a power-loss-safe database.

`examples/paper-review.py` and `examples/experimental-cycle.py` are executable synthetic workflows which retain their new temporary directory for inspection. They do not enroll real research. Tests establish storage and workflow behavior, not mathematical truth, PDF fidelity, human identity, statistical validity or remote publication. The release allowlist must remain exact: never include a real project's `tickets/` or broaden a directory wildcard to make a personalized copy publishable.
