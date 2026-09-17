---
slug:            gotcha-2026-09-17-a-ledger-row-citing-its-own-commit-cannot-converge-by-amen
status:          live
noted:           2026-09-17
severity:        null
retired:         null
retires_when:    null
---
## Symptom

Writing [templates/harness/LEDGER.md](../templates/harness/LEDGER.md)'s own row for the commit it belongs to, then running `git commit --amend --no-edit` to fold the row into that same commit (per the ledger's "in the same commit" rule), changes the commit's hash — which makes the row's own citation stale again. Amending a second time to fix the citation changes the hash a second time, and so on: the row is content inside the very object whose identity it names, so no amend can ever make it correct.

## Story

**A ledger row that cites its own commit's hash cannot converge by
repeated amending — the row is content inside the object whose identity
it names, so every amend that corrects the citation changes the hash the
citation needs to name.** Hit this 2026-09-17 finishing a commit that
touched `commit-identity.sh`, two adapter READMEs, and a new
[grok-build/README.md](../templates/harness/grok-build/README.md): committed first (hash `b475621f5`), added the
required ledger row citing that hash, amended to fold the row in (per
[templates/harness/LEDGER.md](../templates/harness/LEDGER.md)'s own "add a
row here in the same commit" instruction) — new hash `73a4292eb`, row now
stale. Fixed the citation and amended again — new hash `e956e66bf`, row
stale again. The pattern repeats every time, because the object being
hashed always includes the string trying to name it.

**The fix is to stop chasing it with amends and split into two commits.**
`templates/harness/LEDGER.md` itself is not inside any of the three
directories [tools/precedent_check.py](../tools/precedent_check.py)'s `parallel-artifact-ledger` check
treats as family members (`templates/harness/claude-code`,
`templates/harness/codex`, `templates/harness/gemini-cli` — see
[templates/harness/README.md](../templates/harness/README.md)), so a
commit that touches only `LEDGER.md` never needs a row of its own. Freeze
the real commit — stop amending it once its content (other than the
citation) is final — then add one small follow-up commit, touching only
`LEDGER.md`, that corrects the citation to the now-fixed, no-longer-moving
hash. The follow-up commit needs no row because it never touches a member
directory, and the frozen commit's hash never changes again once the
follow-up lands.

## Fix

Never try to make a commit's ledger row cite its own final hash by
amending in a loop — it cannot converge. Freeze the substantive commit
once its non-ledger content is done, then correct the citation in a
separate, small, member-directory-free follow-up commit.
