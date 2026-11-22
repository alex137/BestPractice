---
slug:            gotcha-2026-11-22-a-shared-set-under-another-account-is-looked-for-under-yours
status:          live
noted:           2026-11-22
severity:        notable
retired:         null
retires_when:    a set that is not found under the first account is looked for where it really lives, or the message says "no such repository under that account" in those words
---
## Symptom

Worker sessions in a project **cannot push**. Every push is refused with

> the loader block is built from sources this machine cannot reach, so "no
> drift" was not established

Session start has already said that one shared practice set "did not
resolve", and that git answered *"Invalid username or token ...
Authentication failed"*. The project's other sets arrive fine. A token is
set. It reads as a token that does not cover the missing set.

**It is not the token.** The set is being asked for at an address where no
such repository exists.

## Story

2026-11-22, reported from a private project whose workers had been handing
their work over as text, because none of them could push.

The project declares two shared sets **by name only**. One lives under the
project owner's own GitHub account. The other,
`precedent-shared-writing`, lives under a different account.

The engine builds a set's address as *account + name*, and it has **one**
account for every set a project declares:
`PRECEDENT_SOURCE_BASE_URL` when the environment sets it, and otherwise
the account the token belongs to
([precedent_source_credentials.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_source_credentials.py),
`source_base_url`). That environment set a token and no base address. So
both sets were asked for under the owner's account. One is there. The other
is not, and GitHub answers a request for a repository that does not exist
exactly as it answers a refused password, so the failure was reported as an
authentication failure.

Measured the same day in a session rooted in this repository, which
declares the same set and had the same environment:

| Address tried | With the token | With no token |
|---|---|---|
| the set under the account it really lives in | reached | reached |
| the set under the token's own account | "Invalid username or token" | "could not read Username" |
| the person's individual set, under their own account | reached | reached |

The set that "needed a credential" was readable with **no credential at
all**. The only address that failed was the one the engine had made up.

Then the refusal. With a declared set missing, the project's push check
runs its view check
(`build_views.py --views-only --check`), which prints *NOT VERIFIABLE* and
exits clean, and
[precedent_push_check.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_push_check.py)
turns those two words into a failure (`_guard_build_views`). So one
missing set refuses every push from that session, whatever the push
changes. Reproduced in a throwaway project: with the set declared by name
only, the clone failed and the view check printed the line; with the set's
address written on its declaration, the clone worked and the line was gone.

Two things made it expensive. The message named a credential, which sent
everybody to tokens and access lists. And the worker sessions did the
right thing by not going around the check, so the cost landed as slow,
error-prone handoffs instead of as a loud failure anybody would fix.

## Fix

**In a private project, write the set's address on its declaration.** In
`precedent.json`, the source entry takes a `repo` field, and a full address
there is used as given
([precedent_source_bootstrap.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_source_bootstrap.py),
`_clone_url`):

```json
{"level": "shared", "name": "precedent-shared-writing",
 "path": "../precedent-shared-writing",
 "repo": "https://github.com/<the account it lives under>/precedent-shared-writing"}
```

One commit, and every later session gets the set at session start with no
change to anybody's environment. **A public project must not do this** for
a private set: the address names the account, and the file is published.
There the route is the environment: `PRECEDENT_SOURCE_BASE_URL` set to the
account the shared sets live under, and `PRECEDENT_INDIVIDUAL_REPO` set to
the full address of the person's own set
([PER_MACHINE_SETUP.md](https://github.com/alex137/BestPractice/blob/staging/documentation/PER_MACHINE_SETUP.md)).
That route cannot serve shared sets under two different accounts; the open
item below is about that.

**In a session that is already stuck:** clone the set from its real
address into the place session start named, then run the push check again.
Where a typed `git clone` is stopped by a permission prompt, do not go
around it: once the address is declared,
`python3 tools/precedent_session_check.py --apply` does the clone, and the
installed settings allow that command without asking.

**When git says "Authentication failed" for a practice set, check the
address before the token.** A repository that is not there and a password
that is wrong look the same from the outside.

Open items:
[the push check refuses over a set the push does not touch](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-11-22-a-push-is-refused-over-a-practice-set-it-does-not-touch.md)
and
[one account for every set](https://github.com/alex137/BestPractice/blob/staging/todo/todo-2026-11-22-one-account-address-cannot-serve-sets-under-two-accounts.md).
