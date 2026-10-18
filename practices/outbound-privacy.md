---
slug:        outbound-privacy
title:       A request leaving the machine never carries the person's private details
tier:        on-demand
severity:    default
applies_to:  ["**"]
applies_to_why: "Fires on any request to an outside service, which no path identifies; the gate and the scan enforce it on every tool call."
occasion:    "fetching a page, searching the web, calling an outside service, or writing a script or an agent brief that will"
gates:       []
index_clause: "nothing private in an outbound request; contact fields get a generic id"
checked_by:  null
defines:     ["private term"]
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       "2026-10-18"
approved_by: "Alex, 2026-10-18: \"Do all of the above\", on the proposal to block, log, scan, write the rule and send it upstream"
strength:    decided
---
## Rule
**No request that leaves the machine carries the person's private
details**: their email, name, address, or any term they list as private.
That covers a page fetched, a search, a call to an outside service, and
every header, query and script that builds one. **A site that asks
automated tools for contact details gets a generic identifier**, such as
`research-script/1.0`, never the person's. If it refuses a generic one,
read the page another way or skip it and say so. **A brief for an agent
that will fetch from the web says this in a line of its own.**

A private term is the signed-in person's email, which Claude Code puts in
the session's environment, and each line of `.precedent/private_terms.txt`
(untracked, this machine) and of the file `precedent.json` names at
`private_terms` (a private repository's list). Tell the person, in the
reply, of any refusal the gate made and anything the scan found.

## Detail
Two tools enforce it. **The gate**
([tools/outbound_privacy_gate.py](https://github.com/alex137/BestPractice/blob/main/tools/outbound_privacy_gate.py)),
before every tool call, refuses a web fetch, a web search, a fetching Model
Context Protocol (MCP) tool, or a shell command that reaches the network, when its text holds a
private term, and appends the refusal, the term masked, to
`.precedent/outbound_refusals.jsonl`. **The scan**
([tools/outbound_privacy_scan.py](https://github.com/alex137/BestPractice/blob/main/tools/outbound_privacy_scan.py)),
at the end of each turn, reads the session's own record of its tool calls
and its agents' records, and stops the turn once for each request that
already went out with a private term, so the reply has to say what, where
and when. Run it bare to read every transcript on the machine.

A git push is not refused: a commit's author address is attribution the
person chose, to their own repository. Search queries carry the work's
subject matter, which is not private in this sense; a private repository
that wants unfiled project names kept out of searches lists them as
private terms.

## Why
A site's request for contact details is a courtesy it asks of automated
tools, not an obligation, and the person never agreed to answer it. An
agent that knows the person's email will fill such a field with it unless
something stops it, and a rule in its context did not.

## Story
2026-10-18, in a consuming repository: a research agent fetching
encyclopedia pages set its download script's identification header to
"Research/1.0 (<the person's email>)", because the site asks for contact
details, though its context said never to send that address anywhere. Four
pages went out that way in one command. It came to light only because the
agent mentioned it in its report; the scan, run afterwards over every
transcript on the machine, found that one command and nothing else.
