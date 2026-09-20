# Computational and experimental research records

The same [local ticket workflow](../research-ticket-workflow.md) can preserve a computational question, design, result, interpretation and decision. This extension installs no ML training pipeline, server, remote job runner or external tracker.

| Kind | Required meaning in the body |
| --- | --- |
| question | The uncertainty and why it matters |
| hypothesis | Falsifiable expectation, assumptions and scope |
| experiment | Design, contrast/baseline, inputs, metric, seeds, code/config version, predeclared success/stop criterion and budget |
| activity | Actual implementation, execution, collection, analysis or reproduction work |
| result | Observed data and exact source manifest, including failures and negative/null/invalid results |
| analysis | Interpretation, uncertainty, alternatives and limits |
| decision | Go/no-go, revised design, stop or defer, with evidence and rationale |

Use `question → hypothesis → experiment → result → analysis → decision → next question/design` as readable history, not a mandatory linear pipeline. Analyses may compare designs. Preserve negative routes and reasons for retrying. One activity may cover several repeated runs unless the question, recoverable failure or decision changes.

Only `activity` may begin/end an operational session or become Done. Completing execution never establishes support or activates a conditional follow-up. Keep such follow-ups Backlog until an explicit recorded decision activates them. The writer checks blockers but does not enforce this scientific decision policy.

Use scoped `tests` (design → hypothesis/question), `produces` (design/activity → result), `supports`/`challenges` (result/analysis → hypothesis), `interprets` (analysis → result), `informs` (result/analysis → decision) and `motivates` (decision → question/hypothesis/design/activity). Each edge retains route, logic, evidence and endpoint versions. No graph aggregation computes truth or readiness. Use mathematical `refutes` only for an actual exact-scope refutation.

Bind records with `source_refs` from exact local text or committed manifests. Outcome on result/analysis may be positive, negative, null, mixed, inconclusive or invalid; omitted/JSON null means unassessed, whereas the string `"null"` records a null finding. Outcome is interpretation under the design, not process exit status. An activity can be Done while its result is negative.

Nonmathematical unbound records have role research-record. `propose` is reserved for mathematical formulations: create a revised design or interpretation and retain its predecessor. Preserve contaminated observations and their exclusion rationale even after a clean rerun. Check current source bytes and historical reference validity before relying on evidence. Keep old event hashes unchanged.

Run `python3 -B meta/research-tickets/examples/experimental-cycle.py` for a synthetic design, two fictional executions, negative finding, scoped analysis, no-go decision, canceled conditional activity and deferred revision. The script uses a new temporary project, no real jobs or network. [WRITE-API.md](WRITE-API.md) defines exact request and recovery semantics.
