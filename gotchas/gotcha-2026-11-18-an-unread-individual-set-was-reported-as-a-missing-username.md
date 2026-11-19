---
slug:            gotcha-2026-11-18-an-unread-individual-set-was-reported-as-a-missing-username
status:          live
noted:           2026-11-18
severity:        notable
retired:         null
retires_when:    every consumer has refreshed precedent_gate.py and precedent_branch_name.py past the commit that makes the recurring reminder carry its remedy and the branch-name tool name an unread set
---
## Symptom

A cloud session works for two days with the person's individual set
unread. Every turn the reply gate prints

> 1 private source(s) did not resolve (individual/precedent-individual);
> said in full earlier this session

and nothing happens. Then the branch-name tool prints "no GitHub username
is declared" and offers to record one. The person confirms a username
that their set had declared all along. Replies were also written in the
fallback register for the whole session, because the person's declared
register sits in the same unread file.

## Story

2026-11-18, in a dependent repo. Session start tried to clone the
individual set and the credential was refused. The standing instruction
says to attach a missing source with `add_repo`, silently. The session did
not, or did and never said it had failed; the early turns had been
summarized away by the time anyone looked.

Two messages kept the failure in place. The gate's reminder is printed in
full once per session and as a pointer after that, and the pointer named
the problem with no action in it. A session whose context has been
summarized has no "earlier" to read. And the branch-name tool read "the
set that holds the username could not be read" as "no username is
declared", which sent the session to ask the person a question they had
answered long before.

One `add_repo` call, made when the person finally asked for it, resolved
the set at once.

## Fix

The pointer now ends with what to do, every time: attach the named set, or
tell the person in one line that their own rules are not loaded.
[precedent_branch_name.py](https://github.com/alex137/BestPractice/blob/staging/tools/precedent_branch_name.py) checks for an unread individual set before it
says a username is missing, and names the attach when there is one.

A message that recurs must carry its own remedy, and a tool that cannot
read a declaration must say it could not read it, never that it is absent.
