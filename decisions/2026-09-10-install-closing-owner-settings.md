---
date: '2026-09-10'
question: |
  An install can finish clean — audit green, workflow installed, everything
  committed — and still leave the repository unable to check or act on
  itself, because three GitHub settings only a repository administrator can
  set were never mentioned: a developer token stored as a repository
  secret, a default branch named `main`, and "Allow GitHub Actions to
  create and approve pull requests". Should these be left to be discovered
  when something fails, or named as a required part of every first
  install's closing message?
decision: |
  Named, and in two places at once. INSTALL.md §1 gains step 10 (§0 gains
  step 9) requiring a first install to close by naming all three, with the
  click-path and the consequence of each; SETUP.md gains the same as step 7
  in the guided conversation's plain language; templates/GETTING_STARTED.md
  ships a "Settings Only You Can Turn On" section so the instantiated file
  carries them from the moment it is written; GITHUB_ACTIONS.md records the
  two Actions-related ones beside the workflow they affect. The rule itself
  is folded into practices/github-setup-disclosed.md rather than minted as a
  new practice — it is that practice's first-install case, not a different
  rule — and its occasion now fires on a finished install as well as on an
  install step that adds something GitHub-specific.
alternatives: |
  ["Mint a new practice for the closing message -- rejected because
  github-setup-disclosed already says exactly this ('GitHub-specific setup
  is disclosed where the reader will actually see it'); a second slug
  covering the same ground splits the rule and gives a session two places
  to half-read",
  "Put it only in GETTING_STARTED.md, as the practice's own destination
  rule already prescribes -- rejected because a file written during the
  install is not what the administrator acts on at the end of the install.
  The reply is what gets acted on; the file is what survives the
  conversation. Requiring both is the whole point",
  "Widen github-setup-disclosed's applies_to globs to INSTALL.md and
  SETUP.md so the practice fires while those files are edited -- rejected:
  the routing pass already tried and reverted exactly that
  (tools/routing_scope.json), since those files are where the fact is
  DISCLOSED, not what makes the practice fire",
  "Leave the token out and name only the two Actions settings, since
  nothing shipped here reads a repository secret today -- rejected on the
  owner's instruction, and on the reason behind it: an agent session that
  cannot push a branch or open a pull request discovers that at the moment
  it is most expensive, and the fix needs a person who may not be there"]
decided_by: Morgan, in session, 2026-09-10
strength: decided
---
