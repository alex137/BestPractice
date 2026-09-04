<!-- Template: instantiated by `tools/precedent_bootstrap_source.py --level team`
     (Precedent, https://github.com/alex137/BestPractice). Placeholders
     ({{NAME}}, {{APPROVER_NAME}}, {{APPROVER_GITHUB}}) are filled in at
     bootstrap time; edit this file freely afterward, it is yours. -->

# {{NAME}} — a team practice set

This is **{{NAME}}'s own private space** — one per team, holding the
conventions that team has agreed on. Everyone on the team can read it;
nobody else can.

## What's here

| File | What it's for |
|---|---|
| [`approvers.json`](approvers.json) | The list of people who can say yes to a change here. Whoever creates the set is its first approver (seeded below) — no ceremony, and there is always at least one. |
| [`practices/example-starter.md`](practices/example-starter.md) | One real, minimal practice file, so there's something working to copy and edit. Delete it once the team has written its own. |
| [`leak-blocklist.txt`](leak-blocklist.txt) | The private-term blocklist for Precedent's leak gate — client names, code words, anything that must never reach a public repo. Fill it in; see the file's own header for the format and the two environment/git settings that switch it on. |

## Writing practices

Each practice is one file under `practices/`, in Precedent's phase-1
format — frontmatter plus `## Rule` / `## Detail` / `## Why` / `## Story` /
`## Install`. The full spec is
[Precedent's `spec/PRACTICE_FORMAT.md`](https://github.com/alex137/BestPractice/blob/main/spec/PRACTICE_FORMAT.md);
`practices/example-starter.md` in this repo shows the shape directly.

## Approval

An assistant proposes a practice and asks an approver to look at it — a
review on this repo, so the approval *is* the record. `approvers.json`
holds the list `tools/precedent_land.py` checks a proposer's name against;
adding or removing an approver is itself a change to that file, so it
needs a current approver's own agreement, which is what stops someone
quietly adding themselves.

If the approver is also the person proposing the change — for a small
team, it usually is — there's no waiting: their "yes" in the conversation
*is* the approval, landed directly in the same sitting.

**Nobody is ever blocked waiting for a team approval to *use* a practice
right now.** Put it in your own individual set instead, where it applies
immediately with nobody's permission; offering it to the team is a
separate step, whenever it suits you.
