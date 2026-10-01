# Our Language

*The question this page answers:* **What do the words people use about
Precedent actually mean?**

Conversations about Precedent lean on a handful of words -- "the
individual set", "pre-staging", "in force". None of them is hard, but each
one means something specific here, and a conversation is hard to follow
until you know them. This is the short list. A **repository** below just
means a project's folder of files, kept on GitHub.

<!--gen:words-->
| Word | What it means |
|---|---|
| **practice** | A rule. Each one is a single file holding the rule, the reason for it, and the story of how it came about. |
| **level** | A category you get practices from: universal, shared, individual, or repo-local. The repository that actually holds the rules is one instance of a level -- its source. |
| **universal set** | One level of practices: the one everyone who uses Precedent gets. It is BestPractice's own collection, named `precedent`. |
| **individual set** | One level of practices: the one just for you. Usually a repository named `precedent-individual`. |
| **shared set** | One level of practices: the one a group of people share. A repository may use none, one, or several. |
| **repo-local** | One level of practices: the one belonging to the repository you are working in -- your work repository, the one with BestPractice copied in. They live in its `local/` folder and apply only there. |
| **full set** | All the levels you have access to, together: the universal set, your individual set, your shared sets, and the repo-local practices of the repository you are in. |
| **source** | One instance of a level: the repository a set of practices comes from. |
| **universal source** | BestPractice, the repository everyone's universal practices come from. |
| **individual source** | Your own repository of practices, usually `precedent-individual`. Its rules apply to everything you do, in every repository. |
| **shared source** | One repository of practices that a group of people share, such as `precedent-shared-writing`. One instance of the shared set level. |
| **in force** | A practice that actually applies here, right now. |
| **decided** | How a decision was made: the person running the session actively wanted it, in their own words. Its counterpart is **assented**; every recorded decision is one or the other, or unknown. |
| **assented** | How a decision was made: the person running the session went along with a recommendation the session made, without pushing for it themselves. Its counterpart is **decided**. |
| **primary branch** | The one shared branch regular work lands on. (A branch is a separate line of work in a repository.) |
| **landing branch** | The branch your saved work lands on when you say "Booked" (or "Go update"): pre-staging if you use all three branch tiers, otherwise staging, or main. |
| **feature branch** | The short-lived branch one session works on, on GitHub -- the kind named like `claude/2026-10-01-feature-branch-naming-awpkv`: the day it was made, what the work is, and the end of the session's ID. GitHub's own word for it; some teams say "topic branch". It survives a lost session but is easy to forget, and it is deleted once its work is merged. |
| **pre-staging, staging, main** | The three branches work climbs through, in that order. Pre-staging is where saved work waits, staging is where it is fully checked, and main is production -- what everyone gets. |
| **tier branch** | One of these branches: pre-staging, staging or main, plus the two that travel with them -- staging's old name `precedent-beta-v01` and Promote's lock branch `precedent-promote-lock`. A tier branch is never offered for deletion. |
| **stage** | One of the five steps work climbs from idea to production: Consider, Act, Booked, Debut, Produce. "Promote 3" means stage 3, and each stage is read back before it runs. |
<!--/gen:words-->

*This table is built from one list, so it cannot drift from what the AI
Assistant uses. Numbers by: our_language.py. To change a word, change
[tools/our_language.json](../tools/our_language.json), never this page.*

## Words We No Longer Use

When a word is retired, it is replaced everywhere it is still used to mean
the thing, and a check keeps it from coming back. A quotation or a record
of the past keeps the old word.

<!--gen:retired-->
| Retired word | Say instead | Since |
|---|---|---|
| team (as a level) | **shared** | 2026-09-18 |
<!--/gen:retired-->

*Built from the same list. Numbers by: our_language.py.*

For the phrases you can say to your AI Assistant -- "Go update", "Three
Things" and the rest -- see [How to Use This Day to
Day](DAILY_HABITS.md), or just say **"Vocabulary"**. For every term the
project defines, not just these, see the full
[GLOSSARY.md](../GLOSSARY.md).
