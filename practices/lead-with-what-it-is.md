---
slug:        lead-with-what-it-is
title:       A project's own document leads with what the project is
tier:        on-demand
severity:    default
applies_to:  ["README.md"]
occasion:    "writing a README or other project-facing entry document"
checked_by:  null
defines:     []
status:      active
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

## Why
A newly created project's README once opened with a sentence about
how the project's memory lives in its repository and is edited by talking to
an AI assistant — true of the process layer, and the very first thing a
brand-new reader hit, before a single sentence told them what the project
itself was. "Wait, is this an AI assistant?" is the natural, correct reaction
to reading process-description with zero subject-matter context first.

## Story

## Install
[INSTALL.md](INSTALL.md)'s README-entry step and
[SETUP.md](SETUP.md)'s guided install both instruct: if the repo has no
README yet, write a short project-specific opening — from the
administrator's "what is this project about" answer — before inserting the
[README_AGENT_ENTRY.md.template](templates/README_AGENT_ENTRY.md.template)
block. If a README already exists, insert only the entry block into it;
don't rewrite its opening.
