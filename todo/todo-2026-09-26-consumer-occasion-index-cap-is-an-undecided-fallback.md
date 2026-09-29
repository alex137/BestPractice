---
slug:              todo-2026-09-26-consumer-occasion-index-cap-is-an-undecided-fallback
kind:              manual
domain:            vendoring
severity:          null
status:            done
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          "derive it: each source declares occasion_share_tokens in its precedent-source.json, and a consumer's cap is their sum plus a repo-local allowance"
decision_strength: decided
waiting_on:        null
noted:             2026-09-26
closed:            2026-09-29
---
## What

**Every consumer's occasion index is capped at 4,000 tokens, and nobody
decided that number.** It is the literal fallback in
[tools/build_views.py](../tools/build_views.py)
(`_budget('occasion_index_tokens', 4000)`). The decided number is 3,600,
in [tools/session_load_budgets.json](../tools/session_load_budgets.json),
and Morgan chose it on 2026-09-14 for this repository's own catalogue. That
registry is deliberately not vendored
([tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py)
says so: a repo's budgets are its own declaration). So a consumer that has
not written its own `occasion_index_tokens` gets the fallback. That is all
four sets as of today, checked on disk. The 4,000 was written in the same
commit as the 3,600 (`826f6e3c`) with no reason recorded for it.

It is also applied to a different quantity. The 3,600 was sized against
one catalogue. A consumer's index carries every source it resolves, so the
number caps universal, shared, team and individual lines together.
[tools/build_views.py](../tools/build_views.py)'s own comment on the cap
says a consumer resolving four sources "legitimately has a far bigger one
than this repository's own catalogue", which is the argument against
applying this repo's number there. The fallback applies it anyway.

Registered as a risk input under
[constants-are-risk-inputs](../practices/constants-are-risk-inputs.md), in
the `_occasion_index_fallback_comment` of the same registry. The value is
unchanged.

**What prompted it.** On 2026-09-26 a consumer's index measured about
4,033 against the 4,000 and its merge check refused. The universal share
was trimmed from 2,375 to 1,961 tokens that day. That gives every consumer
about 414 tokens of room without a new number. It does not say whether
4,000 is the right number.

## Options

- **Keep 4,000 and record it as decided.** Costs nothing. The next
  squeeze lands on whichever session adds a practice, which is what the
  cap is for.
- **Have each consumer declare its own** `occasion_index_tokens` in its
  own registry, sized to what it resolves. It is more honest, but it makes
  four more numbers to keep up.
- **Derive it**, for example 3,600 plus an allowance per private source
  resolved. It scales with the thing that grows, but it is a formula
  somebody has to choose.

## How It Closes

Morgan picks one. Then the chosen number, or the formula, and his reason
go into the `_occasion_index_fallback_comment` in
[tools/session_load_budgets.json](../tools/session_load_budgets.json), and
the literal in [tools/build_views.py](../tools/build_views.py) is changed
to match if it has to be.

## Resolution

**Closed 2026-09-29: derived** (Morgan, strength: decided): *"give each
practice set its own allowance, the way universal now has one, and set each
repo's cap to the sum of the allowances for the sets it uses ... Approved,
please implement that."* Each source declares `occasion_share_tokens` in
its own `precedent-source.json` (universal 2,800, and each of the four sets
its measured share plus about 20%), and `tools/build_views.py` refuses to
build a source over it. A repository with no `occasion_index_tokens` of its
own is capped at the sum of its declared sources' allowances plus
`repo_local_occasion_tokens` (400 by default). The 4,000 literal is left
only for a source that declares no allowance yet, and the
`_occasion_index_fallback_comment` in
[tools/session_load_budgets.json](../tools/session_load_budgets.json) says
so. It came up because a consumer declaring all four sets measured about
4,050 against the old 4,000 after the universal share was capped.

