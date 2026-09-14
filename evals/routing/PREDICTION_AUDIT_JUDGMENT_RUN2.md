<!-- Last updated: 2026-09-04 (Buenos Aires) by the session making bounded progress toward the fuller multi-run discipline -->

# Second, independent run of the audit-judgment eval

Written before this run's judge saw anything. Same mechanism and method as
[PREDICTION_AUDIT_JUDGMENT.md](PREDICTION_AUDIT_JUDGMENT.md) (isolated
worktree, fresh blind judge, closed one-at-a-time judgment) — this file
only states what's different: new cases, and why.

**Why a second run at all.** Run 1 scored 6/6 (100%,
[spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md)'s "audit-judgment
result"), explicitly flagged there as N=6/one run/one judge — not yet the
multi-run discipline the original routing eval used. This is one more data
point toward that, not a replacement for it: still bounded to a single
session's turn budget, still N=6, but a different judge and different cases
than run 1, so an inter-run consistency signal exists at all.

**Cases**, six total, none reused from run 1:

| slug | seed / real state | should_flag |
|---|---|---|
| `quote-discipline` | `spec/audit_eval_seed2/openviking_note.md`: cherry-picks OpenViking's 91% figure from spec/ATTENTION_CEILING.md's actual 34–91% range, drops the qualifier that document itself attaches | **true** |
| `verify-decomposition` | `spec/audit_eval_seed2/capacity_note.md`: asserts a negative/impossibility claim ("not possible to run X and Y in one session") as a bare total, no decomposed reasoning | **true** |
| `readers-vocabulary` | `ADOPTING.md` (explicitly written for a non-programmer — its own opening line says so): a sentence inserted naming `precedent.json`, "the resident block", and `RESIDENT_BUDGET_TOKENS` unglossed | **true** |
| `pr-template-honest-gates` | real, current state: this session added `.github/pull_request_template.md` earlier today | **false** |
| `section-order-by-frequency` | real, current state: this session reordered `INSTALL.md` earlier today (§1 now reads before §0) | **false** |
| `parallel-artifact-ledger` | real, current state: this session added `templates/harness/LEDGER.md` earlier today | **false** |

The three `false` cases are not synthetic controls — they are this
session's own fixes from earlier in this conversation, checked by a judge
with no memory of writing them. A `false` verdict here means the fix
worked, independently confirmed; a `true` verdict means the fix didn't
actually satisfy the practice and needs another look, which is real,
useful information regardless of what it does to the headline score.

**Prediction and bands, same as run 1's document**: ≥5/6 (≥83%) validates
run 1's result; ≤4/6 (≤67%) is discordant with run 1 and worth taking
seriously rather than averaging away — two runs disagreeing this much would
mean the true rate is genuinely uncertain, not that one run was wrong.
Reported honestly either way, appended to
[spec/ATTENTION_CEILING.md](../../spec/ATTENTION_CEILING.md) as its own
dated entry under "The audit-judgment result," not blended into run 1's
number.
