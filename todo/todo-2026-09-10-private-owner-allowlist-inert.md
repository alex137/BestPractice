---
slug:              todo-2026-09-10-private-owner-allowlist-inert
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-10
closed:            null
---
## What

- <a id="private-owner-allowlist-inert"></a>**The repo-reference allowlist is
   inert here, and this public tree names the account that owns the private
   practice sets.** Found 2026-09-10 while answering a question about
   `PRECEDENT_SOURCE_BASE_URL`.

   **What is actually there.** [PER_MACHINE_SETUP.md](../documentation/PER_MACHINE_SETUP.md) explains that the
   base URL is an environment variable precisely so that **no tracked file
   names the account owning the private sets**. That is not true of this
   repository as it stands: `.claude/hooks/precedent-individual-bootstrap.sh`
   is tracked and carries the individual set's full URL, account included,
   and the same account name appears across a dozen files under
   [spec/](../spec/). Every one of those five repositories is private.

   **Why nothing caught it — and the first answer written here was wrong.**
   This item originally said the private-owner allowlist had never been
   declared, citing [tools/leak_gate.py](../tools/leak_gate.py)'s `NOTE: ... the
   repo-reference allowlist is INERT`. **That was a misreading, corrected
   2026-09-10** when a session rooted in the individual set read the real
   blocklist and found the declaration present and switched on. The gate had
   been reading `leak-blocklist.default.txt` — the committed fallback — in
   every session that could not reach the private list, and reporting what
   was missing from *that* file. The run's own summary named the fallback two
   lines below the notice, and the session that wrote this entry read past
   it.

   So the allowlist is **armed wherever the private list is reachable, and
   inert everywhere else** — which is every session without
   `PRECEDENT_GIT_TOKEN` or an exported `PRECEDENT_LEAK_BLOCKLIST`. The
   notice now names which of the two states it is in, since their remedies
   are opposite and it used to render identically for both.

   **What is not claimed.** That this is worth acting on. The names are
   already published and in git history, so nothing here is recoverable by
   editing the tree, and [no-rewrite-for-warnings](../practices/no-rewrite-for-warnings.md)
   rules out rewriting published history to chase it. The forward question is
   only whether to switch the allowlist on and work through what it flags, so
   the NEXT such name is caught before it lands.

   **Half of it is closed (2026-09-10), and it was the half with teeth.**
   Morgan approved both moves the same day. Of the 100 mentions, exactly
   **one was functional** — the hook's `DEFAULT_REPO_URL` — and it is gone:
   the URL is now derived as `$PRECEDENT_SOURCE_BASE_URL/precedent-individual`,
   which needs no new variable because
   [source-naming](../practices/source-naming.md) fixes that set's name for
   everybody and the base URL already carried the account for the team sets.
   The template was fixed in the same commit, so no adopting repo
   instantiates the defect again. `verify_harness.py`'s
   `check_public_tree_bakes_in_no_owner_account` now fails any tracked
   `.sh`/`.py`/`.yml` in a `visibility: public` repo that hard-codes an
   account before a declared set name — verified to catch the original line
   by restoring it.

   **What is actually left, now that the allowlist turns out to be armed.**
   Two things, both his.

   First, **`themorgan/precedent-individual` is pre-allowed in that
   blocklist**, which is exactly what
   [templates/leak-blocklist.txt.template](../templates/leak-blocklist.txt.template)
   tells people not to do — an allow line for a personal set discloses that
   the set exists. The existing reason is not empty (the name is already
   declared as a source in this repo's [precedent.json](../precedent.json)), so
   this is a real trade-off and a deliberate removal, not an oversight to
   sweep. Removing it makes the audit report that name on every run.

   Second, **nobody has yet run the armed gate against this tree.** That
   needs one session holding both the private blocklist and this repository,
   which is the `PRECEDENT_GIT_TOKEN` configuration — not a session rooted in
   the individual set, which cannot attach this repo at all.

   The ≈99 prose mentions are deliberately NOT being scrubbed either way:
   naming which repository an incident happened in is the value of the
   record, the account is already published, and a private repo answers 404
   to a stranger regardless.

   **blocked-on:** Morgan — the blocklist file lives in his individual set,
   under a different owner, so this cannot be done from a session rooted
   here at all.

   **Disposition:** wait (2026-09-10, Morgan) — the code half is done; the
   remaining half needs a session rooted in his own account.

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
