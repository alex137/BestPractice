---
slug:            gotcha-2026-10-14-leak-gate-knew-only-the-private-repos-cloned-beside-it
status:          live
noted:           2026-10-14
severity:        notable
retired:         null
retires_when:    null
---
## Symptom

A private repository's name sits in a public tree, and every leak gate run
passed it. Then one session's gate refuses it, for content that has not
changed in days.

## Story

**2026-10-06.** A session working only in BestPractice wrote "a session in
<a private consuming repository> read the short one back" into a docstring
in `tools/precedent_branches.py`. Its gate passed. `auto-cover-bare-names`
was on, but it builds its patterns from the clones on its own disk, and
that repository was not cloned there. The file then reached `main` and was
copied into two public practice sets' vendored engines.

**2026-10-14.** A session that had cloned that repository, to check a
handoff, ran the same gate on the same tree, and it refused the name in
BestPractice and in both sets. A note in one set's `precedent.json`, from
2026-09-10, named it too. So whether a private name was caught depended on
what the session happened to hold. GitHub would not list the account's
repositories either: from a session, `/user/repos` answers "sessions are
bound to their configured repositories".

## Fix

**The list is written down.** `private-repos.txt`, beside the person's
`leak-blocklist.txt` in their individual source, holds one `owner/name` per
line. The gate reads it in every session (`leak_gate.listed_private_refs`)
on top of the clones on disk. It is its own file rather than a new
directive line, because an engine older than a directive refuses the whole
blocklist over it, while an engine older than the file never opens it.

**A clone the list lacks is named at session start.**
`precedent_session_check.py` fails its row "every private repository cloned
here is on your private-repos list" and names the line to add.

**The leaked text is scrubbed where it lives**, and the copies follow by
the next Update Vendors. It stays in public git history: removing it from
there means rewriting a public branch, and that is the person's call.
