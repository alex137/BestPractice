---
slug:            gotcha-2026-09-16-a-repo-cannot-need-its-own-commit-identity-github-verified-commi
status:          live
noted:           2026-09-16
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A repo-scoped git identity gets proposed to fix a GitHub "Verified" badge
mismatch — a different commit name/email for this repository than the
person's own, applied locally so it doesn't leak into other repos — before
anyone checks whether the repository actually needs one.

## Story

A session relayed another session's own reasoning verbatim: "GitHub needs
the committer identity to match the signing key for a verified badge...
fixing it locally, not globally, so [an individual source's] own
authorship convention stays untouched elsewhere." That reasoning was never
checked against how GitHub verification actually works, and a repo-scoped
`commit_identity` override in `precedent.json` — a new rung in
`commit-identity.sh`'s resolution chain, applied local-only — got designed
around it, in detail, before anyone searched the repository for a rule
that required it.

Searched afterward: nothing. No practice, no ruleset, no doc anywhere in
this repo ever required BestPractice to use a different commit identity
than the person running it, and the repo's own branch-protection checker
([tools/precedent_boundary_check.py](../tools/precedent_boundary_check.py))
has no signed-commit check at all.
More to the point, the claim doesn't match GitHub's own mechanism: the
Verified badge is scoped to *(a signing key) ↔ (the GitHub account it's
registered to) ↔ (that account's verified emails)* — never to which
repository a commit lands in. The same key, signing with the same
committer email, verifies identically everywhere or nowhere. A
requirement that differs by repository isn't something that check can
produce. What's real is narrower and person-level: the committer email
has to be a verified email on the account the signing key belongs to —
an account-level fact, not a BestPractice-specific one.

The repo-scoped design was dropped before being built
([spec/COMMIT_IDENTITY_PLAN.md](../spec/COMMIT_IDENTITY_PLAN.md)), in
favor of one self-declared identity plus a "guess, and say so" fallback in
`commit-identity.sh` — no per-repo split. The cost of not checking first
was a full design document (rungs, precedence rules, a risk analysis) for
a mechanism that solved nothing a real requirement asked for.

## Fix

Before designing a repo-scoped override for anything GitHub-badge- or
verification-shaped, check whether the claimed requirement is actually
scoped to the repository at all. GitHub's own identity model (signing
key ↔ account ↔ verified emails) is account-scoped for verification, and
none of it varies by repository — so a "this repo specifically needs X"
claim about verification is a diagnosis to measure
([diagnosis-is-measured](../practices/diagnosis-is-measured.md)), not a
starting premise. Grep this repo's `practices/`, its branch-protection
checker, and [gotchas/](.) for an actual documented requirement before
building machinery to satisfy an undocumented one.
