---
slug:        practice-change-propagates
title:       A changed practice is changed everywhere it is cited
tier:        on-demand
severity:    default
applies_to:  ["practices/*.md", "local/practices/*.md"]
occasion:    "renaming, retiring, deduplicating, deleting or rewording a practice -- or taking an update that did"
gates:       ["merge"]
index_clause: "find every citation in every source; fix what you can reach, hand off the rest"
index_required: false
checked_by:  "tools/precedent_check.py"
defines:     ["live citation"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-27"
approved_by: "Morgan, 2026-09-27"
strength:    assented
---
## Rule
**A practice is cited in more places than its own file, and changing it
changes all of them.** When a branch renames, retires, deduplicates, deletes
or rewords the Rule of a practice, run
`python3 tools/precedent_practice_refs.py --changed-since <base>` before the
merge. It reads this repository and every source it declares, and lists each
**live citation** -- a link, a `precedent_show.py` lookup, or a mention that
is not history -- of what changed.

**Fix every live citation in each repository this session can write, in the
same session.** For each one it cannot write, `--handoff` prints the list as
one paste-ready block ([prompt-please](prompt-please.md)) naming every file.
A reworded Rule keeps its slug, so no check can judge whether a citation
still describes it: read each live one the tool lists.

**The consuming side does the same on every update.** Update Vendors lists
the citations in the repository's own files of anything the update withdrew
or reworded, and they are fixed in that update, not later.

**A practice file is never deleted.** Retire it in place -- `status:` and
`in_force_at:` naming where the rule went -- so that anyone reading an old
name can find out what it became, and the check can tell it apart from an
unrelated word.

## Detail
**History is left alone.** Frontmatter lineage, a Story or History section, a
record (`spec/`, `todo/`, `decisions/`, `gotchas/`, `record/`), a withdrawn
practice's own text, and a line that narrates the change itself ("renamed",
"retired", or naming the successor beside the old name) all describe what
was true when they were written. The tool marks them `history` and the check
never reads them.

**The check is narrow on purpose.** It refuses a link or a lookup command
pointing at a practice in force nowhere, or at one that now only forwards to
a different slug, anywhere in live text, and any mention of one inside an
in-force practice's `## Rule`. It does not refuse a bare backticked name
elsewhere, because *"exactly as `session-text` drew this line"* is lineage no
pattern can tell from a live citation. Those are listed for the session to
read instead. **A line that is recording history can say so** -- "renamed",
"retired", or the successor's name on the same line -- and it clears.

**This is [cross-source-rollout](cross-source-rollout.md) for one boundary it
used to exclude.** That rule leaves "this repo's own prose" out of scope,
which was right for prose and wrong for a practice's name, status and Rule:
those are what other sources cite.

## Why
A practice's name is how every other source refers to it. Change the name, or
what it means, and every citation that still uses the old one is now telling
its reader something false. The only repository that sees the change is the
one that made it, and it is often not the one holding the citation.

## Story
**2026-09-26, the go-merge rename.** `go-merge` became `go-update` here. The
change landed cleanly in this repository and left `go-merge` in the private
sets' practices and READMEs, still describing the old name as the rule in
force. It surfaced a day later, when Morgan used those sets and they
disagreed with this one. An engine fix the same day made links to the stub
forward in consumers. It did not fix the text in the sets, and nothing asked
anyone to.

**Measured 2026-09-27, across this repository and its four declared sets:**
most mentions of a practice no longer in force were history, correctly left
alone. Six were live pointers or mentions inside a Rule: three here, fixed by
the session that wrote this, and one in each of three sets, handed off. The
first run inside a set also caught the lookup's own blind spot: a set does
not declare itself as a source, so its own practices read as withdrawn from
inside it, and a correct citation was refused. It counts them now, and a stub
that only says "another set carries this" is treated as unknown rather than
withdrawn.

**It also found the reason the drift builds up**: that session could fetch
the sets and could not push to them, because they belong to a different
owner than this repository. The session that changes a practice here is
often not one that can fix the sets. So the check runs in every repository
the engine reaches, where the drift can be fixed, and the tool writes the
handoff rather than leaving it to be remembered.

Asked for by Morgan, 2026-09-27: when a practice is changed or deleted, go to
the sets it is cited in and fix the citations there, and do the same from a
repository that vendors them.

## Install
[tools/precedent_practice_refs.py](../tools/precedent_practice_refs.py) is
the lookup, vendored with the engine so every repository has it. The check
is `practice-change-propagates` in
[tools/precedent_check.py](../tools/precedent_check.py), and
[tools/precedent_update.py](../tools/precedent_update.py) runs the lookup as
a step of Update Vendors.
