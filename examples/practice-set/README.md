<!-- Last updated: 2026-08-31 (Buenos Aires) by a phase-3 build session -->

# An example practice set

This is what a **personal practice set** looks like from the inside. It is
here so that someone setting up their own has something concrete to copy,
without anyone having to show them a real one.

Everything in it is invented. Nobody works this way; the practices are
written to demonstrate the mechanics, not to be adopted.

## What it demonstrates

| File | What to look at |
|---|---|
| [practices/name-in-capitals.md](practices/name-in-capitals.md) | The plainest case: a fact about one person, written once, in force everywhere they work. |
| [practices/keep-the-tone-casual.md](practices/keep-the-tone-casual.md) | What happens when a personal preference meets a shared standard — and loses. |
| [practices/link-what-i-cite.md](practices/link-what-i-cite.md) | Replacing a practice from a lower source by name, with `overrides:`. |
| [config.json](config.json) | The user-level file that tells the tools where a personal set lives. |

## The three things worth knowing before you make your own

**It is a separate repository, and it is private.** Not a folder inside a
shared project. The separation is what keeps it private: file permissions are
per-repository, so a folder boundary inside a shared repository is a
convention rather than a control.

**You declare it in your own configuration, never in a shared project.** A
project that named your personal set would tell everyone on the team that it
exists and where it lives, and everyone else's tools would try to open a
repository they are not allowed to read. So a project names only the sources
everyone working there can already see, and you name your own. Two people
working in the same project get different sets, each seeing their own.

**You have one of them, however many teams you are in.** *"Always write my
name in capitals"* is written once and follows you into every project. It is
never copied, never re-approved, never remembered in three places.

## What this is not

It is **not a copy of anyone's real set**, and it is not kept in step with
one. It was written for this repository, from scratch, and it is frozen: it
shows the shape and then stops.

That is deliberate rather than a shortcut. A real personal set is private
precisely because of what is in it — the client names, the working
arrangements, the things someone would rather not publish. Copying one into a
public repository, even a scrubbed copy, is the exact disclosure the whole
separation exists to prevent. So the example is invented, and says so.
