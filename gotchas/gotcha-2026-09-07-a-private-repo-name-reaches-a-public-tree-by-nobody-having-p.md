---
slug:            gotcha-2026-09-07-a-private-repo-name-reaches-a-public-tree-by-nobody-having-p
status:          retired
noted:           2026-09-07
severity:        null
retired:         "2026-09-07"
retires_when:    null
---
## Symptom

A private repo name reaches a public tree by nobody having predicted

## Story

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A private repo name reaches a public tree by nobody having predicted
  it, so repo references are an ALLOWLIST now, not a blocklist.** The
  vocabulary layer blocks the literal strings somebody typed, which failed in
  both directions on 2026-09-07: it missed a private repository nobody had
  listed, and it blocked two names that had become public, forcing 88 hits
  clearable only by deleting content about public files. Declare an owner
  private-by-default in the private blocklist file
  (`# visibility-audit: private-owner <account> -- reason`) and every
  `owner/name` mention is refused unless an `allow` line gives a reason. It
  caught an abandoned private fork on its first run, plus its own manual's
  example, which had used a real account name. The set of names you may
  mention is small and known; the set of repos you might create is unbounded.
  **The URL form is the case that matters and is easy to miss**: the
  lookbehind keeping `a/acct/x` from matching also rejects
  `github.com/acct/x`, because the character before the owner is `/` there
  too — a stated test case caught that, reading it did not.
  [tools/very_deep_check.py](../tools/very_deep_check.py) does the other half on
  request, asking the GitHub API whether each referenced repo is actually
  private and whether a blocklisted name has since gone public; the push gate
  cannot, because it must work offline and in continuous integration (CI).
  Its reach is limited to repos the session can see — `/user/repos` answers
  *"sessions are bound to their configured repositories"* — so it reports how
  many it could NOT determine rather than counting those as passes.

  **A blocklist entry catches the name somebody typed, never the SHORT form
  of it.** The 2026-09-07 sweep scrubbed a private consumer repo's name from
  this tree, `d167ada` caught four stragglers at 17:12 — and two hits of
  `<that repo>-local` survived both, in
  [spec/SOURCE_NAMING.md](../spec/SOURCE_NAMING.md) and [TODO.md](../TODO.md),
  written at 07:02 and not removed until 21:17, all on the same public
  branch and the same day. That string was the name its repo-local practice
  source carried before `source-naming` renamed it to `local`, so it was
  written by sessions describing a *rename*, in exactly the documents that
  exist to explain the convention. The repo-reference allowlist could not see
  it at all — that layer only matches `owner/name`.

  **The vocabulary layer's miss is the instructive half, and the obvious
  reading of it is wrong.** The suffix was never the problem: a `\bFullName\b`
  pattern DOES match `FullName-local`, because a hyphen is a word boundary.
  What defeated it is that the leak used the repo's short form — a head the
  full-name pattern does not begin to cover. So the fix that matters is
  **truncating each pattern to a distinctive stem**, and a trailing `[\w-]*`
  is belt-and-braces on top of it, not the mechanism. Landed 2026-09-07 in the
  individual practice set, seven patterns, with the evidence recorded beside
  them: each stem was cut only as far as its measured hit count against this
  tree stayed at zero (the shorter cuts of the same names score in the tens to
  the low thousands here, which is why "just truncate harder" is not the
  rule), and two further cuts that scored zero were still rejected as
  fragments an ordinary camelCase identifier could produce. Positive control,
  replayed over the two commits that actually carried the leak: the old
  full-name list reports the tree clean, the stems report three hits.
  A private repo leaks through what is named AFTER it — a practice source, a
  branch, a directory, a tag, a check — long after the repo's own name is
  gone, and it leaks under the short name people actually type.

</details>

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
