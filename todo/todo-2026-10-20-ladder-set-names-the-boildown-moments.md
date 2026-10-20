---
slug:              todo-2026-10-20-ladder-set-names-the-boildown-moments
kind:              manual
domain:            practice
severity:          medium
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-10-20
closed:            2026-10-20
---
## What

The ladder set's half of naming the Boildown's moments. BestPractice's
[the-boildown](../practices/the-boildown.md) now names "the archive-line
reply" and "the closing reply", and the `boildown-moments-named` check in
[tools/precedent_check.py](../tools/precedent_check.py) refuses a practice
that restates either one. Its first run, through
[tools/precedent_moments.py](../tools/precedent_moments.py), found one
dependent in every checkout present: precedent-shared-ladder's
`stale-branch-cleanup`, whose title, occasion, `gates_why`,
`applies_to_why` and its note tool [tools/ladder/branch_page_note.py](https://github.com/themorgan/precedent-shared-ladder/blob/main/tools/ladder/branch_page_note.py) all
quote the archive sentence or the "Archive" answer.

The same session also drafted the attach-refusal fallback for that set's
`handoff-only-when-blocked`, matching what BestPractice's
[prompt-please](../practices/prompt-please.md) now says.

## Done when

The patch below, or its equivalent, is on precedent-shared-ladder's landing
branch, and `python3 ../BestPractice/tools/precedent_moments.py .` run from
that checkout prints "none" under restatements. Once the set's vendored
engine carries the new check (its own Update Vendors), `precedent_check.py
--only boildown-moments-named` passes there too.

## The patch

Against precedent-shared-ladder `main` at 1d4f44f. Apply from that
checkout's root with `patch -p1`.

```diff
diff -ru a/practices/handoff-only-when-blocked.md b/practices/handoff-only-when-blocked.md
--- a/practices/handoff-only-when-blocked.md	2026-10-20 10:03:49.213800451 -0300
+++ b/practices/handoff-only-when-blocked.md	2026-10-20 10:04:12.969479348 -0300
@@ -34,6 +34,8 @@
 
 The check has to happen here, at the moment of spawning, because there is no later point where it is possible: a session spawned into a repository this one could not attach cannot enumerate that repository's other sessions either, so the burden cannot be passed downstream. This is the same move as the capability check above -- measure rather than assume -- asked about a different question. That one asks whether I CAN do it; this one asks whether it is ALREADY being done, and satisfying the first says nothing about the second.
 
+**A handoff that tells the new session to attach another repository says what to do when the attach is refused**: do the part it can reach and report the rest plainly, or have me start the session with every repository selected. An attach asked for inside a seeded prompt can be refused by that session's own permission check even where the owners allow it ([`prompt-please`](https://github.com/alex137/BestPractice/blob/staging/practices/prompt-please.md), Detail, 2026-10-20); a seed that assumes it succeeds strands half the work.
+
 A handoff is normally **partial**, and that is the point. Three open items, one of which is in a file you already have open in the repository you are already rooted in: you fix that one, and the handoff document carries the other two. Sorting them is the work; a document listing all three is the work not done.
 
 ## Detail
diff -ru a/practices/stale-branch-cleanup.md b/practices/stale-branch-cleanup.md
--- a/practices/stale-branch-cleanup.md	2026-10-20 10:03:49.190016162 -0300
+++ b/practices/stale-branch-cleanup.md	2026-10-20 10:04:12.969064709 -0300
@@ -1,13 +1,13 @@
 ---
 slug:        stale-branch-cleanup
-title:       "Every reply that says the session can be archived links the person's one pinned page of every branch they can delete and every staging waiting to go live"
+title:       "Every archive-line reply and closing reply links the person's one pinned page of every branch they can delete and every staging waiting to go live"
 tier:        on-demand
 severity:    default
 applies_to:  ["**"]
-applies_to_why: "A moment, not a place: a reply that says the session can be archived. Routed by the `reply` gate."
-occasion:    "a reply that says \"You can archive this session\", or answers \"Archive\" or \"Archive?\""
+applies_to_why: "A moment, not a place: the archive-line reply and the closing reply, both named by the-boildown. Routed by the `reply` gate."
+occasion:    "the archive-line reply or the closing reply (the-boildown)"
 gates:       ["reply"]
-gates_why:   "This set's tools/ladder/branch_page_note.py counts the stale branches, and the repositories whose staging waits for main, at the start of every turn; the reply gate prints what it says (this set's reply_check.json, note_from_tool) only when there are any, so a reply that says the session can be archived is the one that can still carry the link."
+gates_why:   "This set's tools/ladder/branch_page_note.py counts the stale branches, and the repositories whose staging waits for main, at the start of every turn; the reply gate prints what it says (this set's reply_check.json, note_from_tool) only when there are any, so the archive-line reply or the closing reply (the-boildown) can still carry the link."
 index_clause: "with every archive line: link the pinned branch and staging page, only if any"
 index_required: false
 checked_by:  null
@@ -24,8 +24,9 @@
 
 ## Rule
 
-**In every reply that says "You can archive this session", and in one
-that answers "Archive" or "Archive?", when any branch can be deleted or any
+**In the archive-line reply and the closing reply -- the two moments
+[the-boildown](https://github.com/alex137/BestPractice/blob/staging/practices/the-boildown.md)
+names and owns -- when any branch can be deleted or any
 staging is waiting to go into main, link the page listing them in one
 Boildown line.** The list covers every
 repository open in the session where the person is a code owner. A branch
diff -ru a/tools/ladder/branch_page_note.py b/tools/ladder/branch_page_note.py
--- a/tools/ladder/branch_page_note.py	2026-10-20 10:03:49.202038576 -0300
+++ b/tools/ladder/branch_page_note.py	2026-10-20 10:04:26.475819987 -0300
@@ -1,13 +1,12 @@
 #!/usr/bin/env python3
-"""Prints the reply gate's note about the branch cleanup page -- only when some branches can be deleted or a staging waits to go into main -- for every Boildown that says the session can be archived (practices/stale-branch-cleanup.md); run by the gate through this set's reply_check.json `note_from_tool`
+"""Prints the reply gate's note about the branch cleanup page -- only when some branches can be deleted or a staging waits to go into main -- for the archive-line reply and the closing reply, the moments the-boildown names (practices/stale-branch-cleanup.md); run by the gate through this set's reply_check.json `note_from_tool`
 
-branch_page_note.py -- what a reply that says the session can be archived
-owes the branch cleanup page.
+branch_page_note.py -- what the archive-line reply and the closing reply
+(the moments the-boildown names) owe the branch cleanup page.
 
 The page itself is the engine's (tools/precedent_stale_branches.py): its
 delete button runs on GitHub, where nothing a set ships is present. What
-is this set's is the rule that a Boildown saying the session can be
-archived links the page (building and publishing it when this session's
+is this set's is the rule that those two replies link the page (building and publishing it when this session's
 branches changed), and only when there is something on it ("Don't do that if
 there aren't any", Morgan, 2026-10-05). That rule lived in BestPractice's
 reply gate until 2026-10-17 (BestPractice
@@ -51,8 +50,8 @@
     except Exception:                                         # noqa: BLE001
         url = ''
     where = f" ({url})" if url else ''
-    return (f"In EVERY reply that says \"You can archive this session\", and "
-            f"one that answers \"Archive\" or \"Archive?\": {what} (the page "
+    return (f"In the archive-line reply and the closing reply (the moments "
+            f"the-boildown names): {what} (the page "
             f"counts them, after a fetch), so link the branch cleanup "
             f"page{where} in one Boildown line. Build and publish it the first "
             f"time this session gives it, and again only when this session has "
@@ -71,8 +70,8 @@
             f"session, so rows from repositories this session cannot see, and "
             f"ticks saved since, are kept -- publish it as an artifact the way "
             f"its last line says (the page saves the person's ticks into "
-            f"itself). In a reply that does not say the session can be "
-            f"archived, say nothing about it (practice: stale-branch-cleanup).")
+            f"itself). In any other reply, say nothing about it (practice: "
+            f"stale-branch-cleanup).")
 
 
 if __name__ == '__main__':
```

## Progress

2026-10-20: the patch landed on precedent-shared-ladder staging (2628479).
The moments check was then widened to read each practice's Rule and Detail,
and found one more restatement there, in loss-comes-with-a-verdict's
Detail; it is fixed on precedent-shared-ladder branch
2026-10-20-themorgan-root-issues-moments-gate-amusp-5ntqi, with which the
tool prints "none" for that checkout. Left: that branch landing, and the
set's Update Vendors after PR #1314 reaches BestPractice main.

## Closed

2026-10-20: both conditions hold. The fix is on precedent-shared-ladder
`staging` and `main` ([PR #127](https://github.com/themorgan/precedent-shared-ladder/pull/127)),
`precedent_moments.py .` prints "none" there, and after that set's Update
Vendors from BestPractice main @ d04672e86b31, its own `precedent_check.py
--only boildown-moments-named` passes.
