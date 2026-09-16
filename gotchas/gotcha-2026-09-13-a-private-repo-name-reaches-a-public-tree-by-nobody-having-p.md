---
slug:            gotcha-2026-09-13-a-private-repo-name-reaches-a-public-tree-by-nobody-having-p
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

A private repo name reaches a public tree by nobody having predicted it, so repo references are an ALLOWLIST, not a blocklist.

## Story

**A private repo name reaches a public tree by nobody having predicted it, so
repo references are an ALLOWLIST, not a blocklist.** Declare an owner
private-by-default in the private blocklist file (`# visibility-audit:
private-owner <account> -- reason`) and every `owner/name` mention is refused
unless an `allow` line gives a reason. The blocklist approach failed in both
directions on 2026-09-07: it missed a private repository nobody had listed,
and blocked two names that had become public. **The set of names you may
mention is small and known; the set of repos you might create is unbounded.**
**The case that matters and is easy to miss is the URL form** — the lookbehind
keeping `a/acct/x` from matching also rejects `github.com/acct/x`, because the
character before the owner is `/` there too. A stated test case caught that;
reading it did not. **And a blocklist entry catches the name somebody typed,
never the SHORT form of it.** A private repo leaks through what is named AFTER
it — a practice source, a branch, a directory, a tag, a check — long after the
repo's own name is gone, under the short name people actually type. The fix is
truncating each pattern to a distinctive stem, verified at zero hits against
this tree; the measurement behind each cut is in the archive.
[tools/very_deep_check.py](../tools/very_deep_check.py) does the other half on
request, asking the GitHub API whether each referenced repo is actually
private; the push gate cannot, because it must work offline and in CI.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
