---
slug:            gotcha-2026-10-31-add-repo-answers-a-capitalized-repository-in-lowercase
status:          live
noted:           2026-10-31
severity:        notable
retired:         null
retires_when:    "add_repo answers in the spelling GitHub uses for the repository"
---
## Symptom

`add_repo` with `owner: owner, repo: SomeSet` answers `Repo owner/someset
added`, hands back a lowercase `clone_url`, and tells the session to call
`register_repo_root` with `repo: "someset"`. A session that follows it
clones from the lowercase URL, so the clone's origin, and anything copied
from it, now spells a declared repository a second way.

## Story

On 2026-10-31 a consuming repository's session attached two copied-in
sources that way. Its records already disagreed: `precedent.json` spelled
both as GitHub does, and both copy manifests spelled them in lowercase,
because `checkin.py record` copied the clone's origin in. The freshness
check then compared the declared URL with the clone's origin letter for
letter and printed NOT VERIFIED for a source it could read. The person
was asked to approve the same repository twice.

Measured the same evening, from a BestPractice session: `add_repo` for a
capitalized repository answered in lowercase; a second `add_repo` under the
capitalized spelling answered "already attached"; `register_repo_root`
accepted the capitalized spelling; a `git clone` of the capitalized URL
worked through the session's proxy. So the platform itself treats the two
spellings as one repository, and the lowercase answer is cosmetic. Whether
the two approvals came from `add_repo` and `register_repo_root` each
confirming was not measured: a session cannot see the person's prompts.

## Fix

Use the declared spelling throughout, and never `register_repo_root` a
practice source ([attach-never-clone-individual](../practices/attach-never-clone-individual.md),
"One spelling, no root"). Every tool compares repository names through
[`tools/precedent_repo_id.py`](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_repo_id.py), and the engine check
`repo-name-compare-via-helper` fails a tool that compares them itself.
`checkin.py record` writes the declared spelling and corrects an old one,
and `declared-repo-spelling` flags a manifest Update Vendors has not
corrected yet. The lowercase answer itself is the platform's; no session
can send Anthropic product feedback, so the person does, from the app.
