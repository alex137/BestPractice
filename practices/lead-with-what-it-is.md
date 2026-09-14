---
slug:        lead-with-what-it-is
title:       A project's own document leads with what the project is
tier:        on-demand
severity:    default
applies_to:  ["README.md", "SETUP.md", "templates/GETTING_STARTED.md"]
occasion:    "writing a README or other project-facing entry document"
gates:       []
index_clause: "say what the project is before how it is maintained"
checked_by:  null
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 38
---
## Rule
An outward document that both describes a project and explains how
it's maintained — a README, an entry page — states what the project actually
is and does, in the project's own subject matter, before it says anything
about the maintenance or editing process layered on top of it. A reader
arriving cold learns *what this is* before *how to work with it*.

## Detail

## Why
A reader arriving cold has **no frame, so the first thing they read becomes the frame.** Process description read first does not register as background about how the project is maintained; it registers as what the project *is*. Everything after is then interpreted through it.

That is why this is an ordering rule rather than a completeness one. Nothing is missing from a README that opens with its process — every fact may be present and accurate — and it still misinforms, because the reader has already decided what kind of thing they are looking at before reaching the sentence that would have told them.

Ordering is also the cheapest possible fix: the same sentences, moved.

## Story
A newly created project's README once opened with a sentence about
how the project's memory lives in its repository and is edited by talking to
an AI assistant — true of the process layer, and the very first thing a
brand-new reader hit, before a single sentence told them what the project
itself was. "Wait, is this an AI assistant?" is the natural, correct reaction
to reading process-description with zero subject-matter context first.

## Install
[INSTALL.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/INSTALL.md)'s README-entry step and
[SETUP.md](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/SETUP.md)'s guided install both instruct: if the repo has no
README yet, write a short project-specific opening — from the
administrator's "what is this project about" answer — before inserting the
[README_AGENT_ENTRY.md.template](https://github.com/alex137/BestPractice/blob/precedent-beta-v01/templates/README_AGENT_ENTRY.md.template)
block. If a README already exists, insert only the entry block into it;
don't rewrite its opening.
