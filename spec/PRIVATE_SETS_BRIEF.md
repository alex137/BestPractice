<!-- Last updated: 2026-09-01 (Buenos Aires) by a follow-up session -->

# Brief — Populating the Two Private Sets

**Done, 2026-09-01 — reported by Morgan, from a session opened directly
against the two private repos. Phase 3 is closed** (see
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md)'s Sequence table and
"What Phase 3 Built, and What It Could Not"). Kept below, unaltered, as the
record of what that session was handed and why it had to run from outside
Precedent — not as an open task.

**This is the one part of phase 3 that no session working in Precedent can
do.** [spec/SOURCES.md](SOURCES.md) records why: phase 3 built the *receiving*
half — resolver, precedence contract, example set, blocklist template — and
left the private sets empty. This brief is written for the session that fills
them, by the session that closed phase 4.

It is committed here rather than left in a chat thread because that is this
repo's own `repo-is-memory`: a brief that exists only in a conversation is
already lost. It contains no private content, and cannot — everything private
lives in the two repositories this describes.

## Which repositories, and with what access

| Repository | Access | Why |
|---|---|---|
| `themorgan/RepoPersonalPreferences` | **read** | The source. Its 46 rules are what gets split. Nothing needs to be written back at this stage. |
| `themorgan/precedent-individual` | **push** | One of the two destinations. |
| `themorgan/precedent-team-maintainers` | **push** | The other. |
| `alex137/BestPractice`, branch `precedent-beta-v01` | **read only** | The format spec, the resolver, the harness and the blocklist template all live here, and the work cannot be done without them. |

**The read-only access on the public repo is the whole point of running this
in a separate session, and it is not a formality.** Precedent is a branch of a
public repository owned by someone else, so every push there is publication
that cannot be taken back. A session holding 46 private rules *and* push
access to that repo is precisely the exposure the three-level separation
exists to prevent. Read-only makes the bad outcome structurally impossible
rather than a matter of care.

Phase 3 also recorded a platform restriction — that a session cannot hold
repositories from two owners with push access at once. As of 2026-08-31 all
four repositories above report as pushable at the account level, so that
restriction is **unconfirmed** and may not be what blocks it. It does not
matter: the arrangement above needs push on one owner's repositories only, so
it sidesteps the question either way.

## What the work is

Split RepoPersonalPreferences' 46 rules into the two private sets, in the
practice-file format, per the plan's
[Where Today's Practices Go](../PRACTICE_ENGINE_PLAN.md#where-todays-practices-go).

**1. Default every RPP rule to team.** Not because they are all team-shaped —
several are plainly generic — but because of an asymmetry: promoting a team
practice to universal is a designed path, while demoting a universal one means
it has already been published and imposed on everyone using Precedent.
Narrowest first. Promote to universal individually, and promotion means a
check-in to Precedent, not a file written by this session.

**2. Move the person-specific handful to individual.** Commit identity, the
Buenos Aires timezone, the name in a file header, GitHub attribution,
pronouns, the `go`/`merge` shorthand. RPP's own `morgan-scope` rule already
enumerates exactly these, which makes it a reliable inventory.

**3. Two rules die rather than move**, and doing this deliberately is the
first exercise of the lifecycle:

- `morgan-scope` — a meta-rule declaring which facts are person-specific. The
  *level* says that now, so the rule has nothing left to do.
- `bestpractice-wins` — declaring that the personal layer overrides the
  generic one. Precedence is a property of the engine now, not something to
  write down and hope is read.

Look for others of the same shape while you are in there: a written rule that
existed only because the structure could not express the thing. That is the
retirement path working as intended.

**4. Write the real private-term blocklist into the individual set.** Copy
[templates/leak-blocklist.txt.template](../templates/leak-blocklist.txt.template)
to `leak-blocklist.txt` in `precedent-individual`, fill it in there, and:

```
export PRECEDENT_LEAK_BLOCKLIST=<your individual set>/leak-blocklist.txt
git config precedent.requireVocabulary true
```

**This is the single highest-value item in the brief and the one nobody else
can do.** Precedent's leak gate has had its vocabulary layer switched on since
phase 3, but it has only ever run against the generic *template*, whose
entries are deliberate non-words. It is on and blocking nothing real. Read
`python3 tools/leak_gate.py --explain` before starting. The `git config` line
matters as much as the export: without it the layer fails **open**, and a
shell that starts without the variable scans only the structural rules and
exits 0.

## The format

One file per practice at `practices/<slug>.md`, five body sections
(`## Rule`, `## Detail`, `## Why`, `## Story`, `## Install`) and the
frontmatter documented in [spec/PRACTICE_FORMAT.md](PRACTICE_FORMAT.md).
[examples/practice-set/](../examples/practice-set) is a working three-practice
individual set with its user-level config — copy its *shape*, not its content,
which is invented and illustrative.

Four fields need real thought rather than a default, because a second and
third source now exist for the first time:

- **`added` and `approved_by`** were `null` and `"BestPractice (pre-fork)"`
  across the whole universal catalogue, for reasons that do not apply to a
  practice minted here. Fill them in properly.
- **`severity`** is `default` on all 52 universal practices, correctly — its
  only real job is resolving conflicts between sources at different
  precedence, which did not arise until now. Mark a team practice `blocking`
  only where an individual practice genuinely must not be able to override it;
  the resolver refuses the override and *reports* the refusal.
- **`overrides`** must name a slug that exists in a lower source. An override
  naming a slug nobody has is a silent no-op that looks like it works — the
  harness asserts this for the example set for exactly that reason.
- **`tier: resident`** — see the open gap below before marking anything
  resident.

## How to verify, from that session

```
python3 tools/precedent_resolve.py --repo <a consumer repo>
python3 tools/precedent_resolve.py --repo <a consumer repo> --explain SOME-SLUG
```

(`--explain` takes a slug — how did *that one practice* resolve — not a
bare flag; run without it first to see everything, then re-run with a
specific slug for anything that looks wrong.)

The resolver is the contract, and it is already tested against fixtures by
`check_source_precedence` in [tools/verify_harness.py](../tools/verify_harness.py)
(count grows as more cases are added — run the harness for the current
figure rather than trusting a number written here). What has **never** been
done is running it against the real 46. Expect the fixtures to have missed
something the real content raises; that is the point of doing it.

Check specifically that: precedence runs individual > team > universal; a
missing individual set degrades and *says on stderr* what is not in force; a
shared repo naming an individual source is refused by name; and a retired
practice is resolvable by slug but not in force.

## The cross-source resident cap — built 2026-09-01, unverified against the real sets

**Closed on Precedent's side; the one thing this can't finish from here.**
This brief used to ask you to report back a combined resident-block figure
so a Precedent session could build the cap — that never came back, and a
2026-09-01 deep-check audit found the gap still open with no report on file
anywhere. So the cap is now built directly:
[tools/precedent_resolve.py](../tools/precedent_resolve.py)'s
`resident_stats()` sums `## Rule` text across every `tier: resident`
practice in the RESOLVED set — whichever source contributed it — against
the same `RESIDENT_BUDGET_TOKENS = 2000` cap
[tools/build_views.py](../tools/build_views.py) already enforced for the
single-source case. `precedent_resolve.py` (plain, `--json`, run from any
consumer repo) now prints the combined figure every time and **exits 1
when it's over budget** — not gated behind `--strict`, matching the plan's
"mechanically enforced, not by discipline" for the single-repo case.
Tested both directions in `check_cross_source_resident_budget`
([tools/verify_harness.py](../tools/verify_harness.py)): this repo's own
resolved set stays clean, and a synthetic multi-source set built to exceed
the budget is refused.

**What's still needed, and can only happen from a session against the real
private sets** (never from here — see
[Why this cannot run from Precedent](../spec/PRIVATE_ENFORCEMENT_BRIEF.md#why-this-cannot-run-from-precedent)
for the same two structural reasons): run
`python3 tools/precedent_resolve.py --repo <a consumer repo>` with a real
`precedent.json` naming `precedent-team-maintainers` and a user config
naming `precedent-individual`, and see what the real combined resident
figure comes to. If either private set marked more than a practice or two
`tier: resident`, this is very likely to actually fire — that's the point
of running it, not a sign something is wrong.

## What must never happen

- **No private content in `alex137/BestPractice`, ever** — not in a file, not
  in a commit message, not in a branch name. The read-only access makes this
  structurally impossible, which is why it is set that way.
- **The blocklist itself is never published.** It is a map of the secrets.
- **Do not name the individual set in any shared repository's
  `precedent.json`.** The tools refuse it, by name, with the reason in the
  message: it would leak that set's existence and location to everyone on the
  team, and their sessions would try to open a repository they cannot read.

## Done when

- Both private sets hold practices in the format, parsing under the
  catalogue's own parser.
- The person-specific handful is in `precedent-individual`, everything else in
  `precedent-team-maintainers`, and `morgan-scope` and `bestpractice-wins`
  are retired rather than moved.
- A real `leak-blocklist.txt` exists in the individual set and
  `PRECEDENT_LEAK_BLOCKLIST` points at it.
- The resolver resolves all three sources against the real content, and
  precedence is checked against the four behaviours listed above.
- `python3 tools/precedent_resolve.py --repo <a consumer repo>` has actually
  been run against the real two private sets, and exits 0 (the cross-source
  cap is built; this is the one remaining step, and it can only happen from
  a session against the real sets — see above).
