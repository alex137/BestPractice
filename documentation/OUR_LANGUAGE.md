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
| **universal set** | The practices everyone gets. It is BestPractice's own collection, named `precedent`. |
| **individual set** | The practices just for you. Usually a repository named `precedent-individual`. |
| **shared set** | Practices a group of people share. A repository may use none, one, or several. |
| **full set** | Every practice set in force for you: the universal set, your individual set, your shared sets, and the repo-local practices of the repository you are in. |
| **repo-local** | Belonging to the repository you are working in -- your work repository, the one with BestPractice copied in. Its own practices, kept in its `local/` folder, are its repo-local practices, and apply only there. |
| **in force** | A practice that actually applies here, right now. |
| **source** | Where a set of practices comes from, usually a repository. |
| **level** | Which kind of set a source is: universal, shared, individual, or repo-local. |
| **primary branch** | The one shared branch regular work lands on. (A branch is a separate line of work in a repository.) |
| **landing branch** | The branch your saved work lands on when you say "Go update": pre-staging if you use all three branch tiers, otherwise staging, or main. |
| **feature branch** | The short-lived branch one session works on, on GitHub -- the kind named like `claude/<topic>-<random>`. GitHub's own word for it; some teams say "topic branch". It survives a lost session but is easy to forget, and it is deleted once its work is merged. |
| **pre-staging, staging, main** | The three branches work climbs through, in that order. Pre-staging is where saved work waits, staging is where it is fully checked, and main is production -- what everyone gets. |
| **tier branch** | One of the branches in the pre-staging, staging, main climb, or one of the two that travel with them: staging's old name `precedent-beta-v01` and Promote's lock branch `precedent-promote-lock`. A tier branch is never offered for deletion. |
| **stage** | One of the five steps work climbs from idea to production: Consider, Act, Booked, Debut, Produce. "Promote 3" means stage 3, and each stage is read back before it runs. |
<!--/gen:words-->

*This table is built from one list, so it cannot drift from what the AI
Assistant uses. Numbers by: our_language.py. To change a word, change
[tools/our_language.json](../tools/our_language.json), never this page.*

For the phrases you can say to your AI Assistant -- "Go update", "Three
Things" and the rest -- see [How to Use This Day to
Day](DAILY_HABITS.md), or just say **"Vocabulary"**. For every term the
project defines, not just these, see the full
[GLOSSARY.md](../GLOSSARY.md).
