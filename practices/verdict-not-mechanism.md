---
slug:        verdict-not-mechanism
title:       When a tool flags something, judge it and give a verdict, never the mechanism
tier:        on-demand
severity:    default
applies_to:  ["**"]
occasion:    "a tool, hook, check or gate flags something the person would otherwise have to judge"
gates:       ["reply"]
index_clause: "judge what a tool flagged; give the person a verdict and why, never its name"
index_required: true
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-09-26"
approved_by: "Morgan, 2026-09-26: \"TELL ME IF YOU RECOMMEND ME LOSING THEM OR NOT, I DON'T KNOW WHAT STOP HOOKS ARE, SO YOU NEED TO EVALUATE THE STOP HOOKS AND MAKE A RECOMMENDATION, AND THE SAME FOR OTHER SIMILAR ISSUES NOT JUST STOP HOOKS.\" Commits that change no file are never mentioned, and ahead/behind counts are of commits that changed files: Morgan, 2026-09-27 -- \"let's have the system stop describing and/or reporting and/or mentioning empty merges\" (strength: decided)."
strength:    decided
---
## Rule
**When a hook, check, gate, scanner or any other tool raises something, the
session works out what it means and hands the person a verdict.** A verdict
is what to do and why, in terms of what they keep, lose, risk or gain. A
tool's name and its complaint are not a verdict. Never pass the flag along
for the person to judge ("the stop hook counts these as unsaved -- tell me
if you're fine losing them"). They may not know what the tool is, and the
session has everything it needs to look.

**So look first, then say one of three things:**

1. **It's handled.** The session could settle it and did. Say what it did
   in one line.
2. **I recommend X, because Y.** The choice is the person's, or the session
   was not allowed to act. Give the recommendation and the concrete reason.
   If the session tried and was blocked, say that in plain words ("the
   environment wouldn't let me delete files"). Don't make the person
   decide from the flag.
3. **This one really needs you.** Only when the answer turns on something
   the session cannot know, like whether they still want a draft. Ask that
   question in their words.

**A commit that changes no file is never mentioned.** A merge commit, an
empty sync commit, a branch that differs from another only in commits like
those: none of it is counted, described or reported to the person, by a
tool or by a session. When a reply says a branch is ahead of or behind
another, the number is **the commits that changed files**, and when there
are none, there is nothing to say. Morgan, 2026-09-27 (strength: decided):
*"let's have the system stop describing and/or reporting and/or mentioning
empty merges"*, and on the branch lines, count *"the number of commits
ahead/behind that made changes to the repo"*.

**When a tool's verdict and the session's disagree, the reply says what the
session found, not what the tool concluded.** If a fixed sentence the tool
requires no longer matches the truth, say which part the tool can't see, and
recommend the fix to the tool.

## Detail
**Looking means measuring, not recalling.** "Uncommitted changes" can be
somebody's afternoon of work or a byte-for-byte copy of files published
elsewhere. Diff them against where they came from before calling them
either. A cause the tool itself names is a hypothesis
([diagnosis-is-measured](diagnosis-is-measured.md)).

**This is the general form of rules that already exist for one case each.**
[the-boildown](the-boildown.md) says never to comment on the gate itself.
[my-options](my-options.md) ends every set of choices on a named
recommendation. [readers-vocabulary](readers-vocabulary.md) keeps a
category's internal name out of what a reader sees. This practice covers
every other place a tool's output reaches a reply.

**Not checked mechanically (`checked_by: null`), and the reason is
specific.** The obvious check is a phrase list in the reply check: refuse
"the stop hook says" or "tell me if you're fine". It would fire on replies
that name a tool while explaining it well, which is allowed. It would also
miss the same hand-off in any wording not on the list. What the rule asks
for is a judgment about whether the session looked, and that is not in the
text of the reply. It is taught at the `reply` gate instead.

**It never licenses acting past an authorization or a refusal.** "It's
handled" covers what the session was already allowed to do. When the
environment blocks an action, the verdict is a recommendation, and the
session does not route around the block.

## Why
A flag passed along unjudged moves the work onto the person least equipped
to do it. The session can read the tool's source, diff the files and see
where they came from. The person has only the tool's name, which may mean
nothing to them. Worse, it reads as if the session had checked, when
nobody has.

## Story
2026-09-26. A session closing out its work ended the reply with: "Don't
archive this session yet: the stop hook still counts those clone changes as
unsaved. Tell me you're fine losing them and it can be archived." Morgan
replied: "NEVER TELL ME THINGS LIKE THIS, TELL ME IF YOU RECOMMEND ME LOSING
THEM OR NOT, I DON'T KNOW WHAT STOP HOOKS ARE."

The changes were the engine refresh that runs at every session start, copied
into four practice-set clones. Once the session looked, every code file
matched the upstream `main` byte for byte, and the rest were generated from
those files. So the right verdict was "lose them; any new session re-creates
them". The session could have said that in the first place and didn't.

## Install
Nothing to install. It fires at the `reply` gate
([tools/precedent_gate.py](../tools/precedent_gate.py)), so every session
that writes a reply is shown it.
