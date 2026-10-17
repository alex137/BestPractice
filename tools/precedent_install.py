#!/usr/bin/env python3
"""Installs Precedent into a project in one command (INSTALL.md section 0 performed mechanically: catalogue, engine, precedent.json, templates, sync, lint) and prints the placeholders it left for a person to adapt

precedent_install.py -- install Precedent into a project in one command.

Run from a clone of Precedent (this repository), pointed at the project:

  python3 tools/precedent_install.py <project path> --project-name "Recipe Book" \\
      [--about "one sentence, used only if the project has no README yet"] \\
      [--base-branch main] [--visibility private|public] \\
      [--output-paths docs,site] [--content-paths notes/,TODO.md] \\
      [--admin github-handle] [--team NAME=PATH ...] [--no-terminal] [--force]

--no-terminal says the assistant that will work here has no terminal
(ChatGPT connected to GitHub, say): precedent.json gets
"github_ci_main_test": "always", so GitHub checks every push to main, in a
private repository too -- the only check such an assistant gets.

--visibility, when not given, is read from GitHub for a GitHub origin, and
is public when it cannot be read: the safe direction, since a private repo
installed as public only keeps its private-level practices out of the
tracked AGENTS.md (2026-10-17). The output says which it chose and why.

--content-paths names the person's own material kept in the project (a
personal to-do list, notes, a manuscript): precedent.json `content_paths`,
which the checks about session work skip. A path ending in "/" is a folder.

It performs INSTALL.md section 0 -- the loader install -- mechanically: it
vendors the practice catalogue and the engine, writes precedent.json,
instantiates every template section 0 names with the placeholders this
tool can know filled in, runs the sync, lints the files it wrote, and then
prints exactly what it could NOT decide: the placeholders left for a person
or an assistant to adapt, and any wording that still names a layout this
project does not have. It never commits and never asks. It pushes in one
case only: for a person on the ladder, it makes the branch tiers on an
origin that already has main (_tiers; Morgan, 2026-09-27).

WHY THIS EXISTS (practice: cite-the-incident). The 2026-09-14 very deep
check rehearsed section 0 as written and found that a correct install took
nine prose steps, a table of exceptions, and a grep, and still came back
with a red check and a template the adopter was told not to touch failing
the light check. Every one of those defects was a document describing a
sequence of file operations drifting from the operations. A tool that
performs the operations cannot drift from itself, and what it prints at the
end is the part that genuinely needs judgment. The guided install
(SETUP.md) runs this and adapts what it lists.

WHAT IT DOES NOT DO, on purpose. It does not fill in
local/practices/project-voice.md's or
local/practices/project-visual-identity.md's sections (an install
does the essentials and stops -- INSTALL.md, "Essentials only").
It does not wire a shared or individual source beyond what --team declares;
the shared/individual question is a conversation with the administrator
(INSTALL.md section 0 step 3). It does not commit: a person reviews the tree
first. And it does not run the freshness guard or any session hook -- those
run in the project's own sessions from then on.

IT INSTALLS THREE GITHUB ACTIONS WORKFLOWS BY DEFAULT, since 2026-09-25:
leak-gate.yml and light-check.yml -- one light check on a pull request into
main, and a leak gate that never runs in a private repository -- and, since
2026-10-16, precedent-branch-cleanup.yml, which runs only when someone
clicks Run workflow. An individual or shared source whose identity.json
declares `"github_ci_workflows": "disabled"` switches all three off (the old key `ci_workflows` is still read).
From 2026-09-15 to 2026-09-25 nothing declared meant disabled. The tool names
the reason in its output and in the project's own GETTING_STARTED.md. See
documentation/GITHUB_ACTIONS.md.

Exit 0 when the install completed and the lint of the written files passed;
exit 1 when it refused (already installed, not a git repository) or a step
failed; the message says which.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]      # the Precedent clone
sys.path.insert(0, str(ROOT / 'tools'))
import precedent_time  # noqa: E402  (practice: timestamps-carry-offset)
import precedent_identity  # noqa: E402
import precedent_vendor_engine  # noqa: E402
import precedent_branches  # noqa: E402
TEMPLATES = ROOT / 'templates'
UPSTREAM_URL = 'https://github.com/alex137/BestPractice'
UPSTREAM_DOCS = f'{UPSTREAM_URL}/blob/main'
UNIVERSAL_PATH = 'precedent/universal'
MAIN_TEST_KEY = precedent_vendor_engine.MAIN_TEST_KEY
# Mirrors precedent_update.CATALOGUE_COMPANIONS (asserted equal by
# check_installer_vendors_the_catalogue_companions); not imported, since
# precedent_update is a far heavier import than this list.
CATALOGUE_COMPANIONS = ('precedent-source.json', 'record/WITHDRAWN_FROM_UNIVERSAL.md',
                        'close_detect.json')

# What section 0 instantiates at the project root, and the template each
# comes from. GETTING_STARTED.md is a template that keeps a plain .md name
# on purpose (it doubles as the rendered sample).
ROOT_FILES = {
    'AGENTS.md': 'AGENTS.md.loader.template',
    # The repository's own text for its map and glossary: MAP.md and
    # GLOSSARY.md are generated from these by the sync, never hand-written
    # (spec/GENERATED_FILES_PLAN.md step 5; Morgan, 2026-10-03).
    'MAP.source.md': 'MAP.md.template',
    'TODO.md': 'TODO.md.template',
    'GLOSSARY.source.md': 'GLOSSARY.md.template',
    'GETTING_STARTED.md': 'GETTING_STARTED.md',
    # The one trap every install inherits, as a file in the catalogue
    # rather than an entry inlined into AGENTS.md: resident
    # environment-gotchas rules the catalogue out of the instructions file,
    # and the templates' old inline section taught every consumer the
    # opposite (very deep check 2026-09-21, B1; fixed 2026-09-28).
    'gotchas/gotcha-2026-09-01-a-stale-checkout-looks-complete-with-no-error.md':
        'gotchas/stale-checkout.md.template',
}
# This project's own voice and its own visual identity are repo-local
# PRACTICEs, not root documents -- see
# templates/local-practices/project-voice.md.template's and
# templates/local-practices/project-visual-identity.md.template's own
# headers for why. `name` is fixed to "local" by practice: source-naming,
# never chosen.
LOCAL_PRACTICE_FILES = {
    'local/practices/project-voice.md': 'local-practices/project-voice.md.template',
    'local/practices/project-visual-identity.md': 'local-practices/project-visual-identity.md.template',
}
MIRROR_WORDS = 'process/upstream'    # the section-1 layout this install does not have
# The installer wires the Claude Code adapter only. A project worked by
# another assistant needs that assistant's adapter as well, and until
# 2026-10-06 nothing said so: SETUP.md asked which assistant would work in
# the repository and no later step used the answer (very deep check,
# 2026-10-05, pass 1). Printed in every report, since the installer is not
# told the answer.
OTHER_ASSISTANTS_NOTE = (
    'only the Claude Code adapter was installed. If Codex, Gemini CLI or '
    'another assistant will work in this project, add its adapter too -- '
    f'{UPSTREAM_DOCS}/templates/harness/README.md lists them, and each '
    "adapter's own page says what to copy where (they reuse the "
    '.claude/hooks/ scripts installed here, so keep those).')


class InstallRefused(Exception):
    pass


def _run(args, cwd):
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)


def _git(dest, *args):
    r = _run(['git', *args], dest)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def _remote_owner_repo(dest):
    rc, url, _ = _git(dest, 'remote', 'get-url', 'origin')
    if rc != 0 or not url:
        return None, None
    m = re.search(r'[:/]([^/:]+)/([^/]+?)(?:\.git)?/?$', url)
    return (m.group(1), m.group(2)) if m else (None, None)


# The one copy of this helper, imported (2026-10-17): nine tools carried
# their own. precedent_check.py's `declared-base-branch` refuses a new one.
from declared_base_branch import declared_base_branch as _declared_base_branch  # noqa: E402


def _base_branch(dest, declared):
    """The branch the project's work is measured against. A DECLARED value
    wins outright -- the --base-branch flag, then a precedent.json already on
    disk (a --force reinstall); origin/HEAD answers a different question
    (what GitHub shows first) and is only the fallback for a project that
    declared nothing. The value is then written into precedent.json so no
    later tool has to infer it again."""
    if declared:
        return declared, 'declared with --base-branch'
    already = _declared_base_branch(dest)
    if already:
        return already, 'declared in the existing precedent.json'
    rc, ref, _ = _git(dest, 'symbolic-ref', '-q', 'refs/remotes/origin/HEAD')
    if rc == 0 and ref.startswith('refs/remotes/origin/'):
        return ref[len('refs/remotes/origin/'):], "inferred from origin's default branch"
    # origin/HEAD is unset after `git remote add origin` and a push, which is
    # how a new project gets its origin -- and the current branch is then
    # often a feature branch, which became the base branch (very deep check,
    # 2026-10-17). So ask origin itself, then look for its main, before
    # falling back to the branch checked out.
    has_origin = _git(dest, 'remote', 'get-url', 'origin')[0] == 0
    if has_origin:
        try:
            r = subprocess.run(['git', 'ls-remote', '--symref', 'origin', 'HEAD'],
                               cwd=str(dest), capture_output=True, text=True, timeout=20,
                               env={**os.environ, 'GIT_TERMINAL_PROMPT': '0'})
            m = re.search(r'^ref: refs/heads/(\S+)\s+HEAD$', r.stdout, re.M)
        except (OSError, subprocess.TimeoutExpired):
            m = None
        if m:
            return m.group(1), "inferred from origin's default branch (asked origin)"
        if _git(dest, 'rev-parse', '--verify', '-q', 'refs/remotes/origin/main')[0] == 0:
            return 'main', "inferred from origin's main (origin names no default branch)"
    rc, cur, _ = _git(dest, 'rev-parse', '--abbrev-ref', 'HEAD')
    if rc == 0 and cur and cur != 'HEAD':
        return cur, ('inferred from the branch checked out now (origin named no '
                     'default branch and has no main)' if has_origin else
                     'inferred from the branch checked out now (no origin)')
    return 'main', 'assumed; the repository has no branch yet'


def _visibility(dest, given):
    """-> (visibility, how). Given with --visibility wins; then a
    precedent.json already on disk (a --force reinstall); then what GitHub
    says about the origin; and when none of those can be read, PUBLIC.

    Public is the direction a wrong answer can be undone from: a private
    repository installed as public only leaves its private-level practices
    out of the tracked AGENTS.md, while a public one installed as private
    publishes them on its first push. Until 2026-10-17 an absent flag meant
    private, silently, though precedent.json's own comment says an absent
    key counts as public for exactly that reason (very deep check)."""
    if given:
        return given, 'given with --visibility'
    try:
        v = json.loads((pathlib.Path(dest) / 'precedent.json')
                       .read_text(encoding='utf-8')).get('visibility')
        if v in ('public', 'private'):
            return v, 'declared in the existing precedent.json'
    except Exception:                                        # noqa: BLE001
        pass
    rc, url, _ = _git(dest, 'remote', 'get-url', 'origin')
    owner, repo = _remote_owner_repo(dest)
    if rc == 0 and owner and re.search(r'github\.com[:/]', url):
        try:
            import github_budget
            data, err = github_budget.call(f'repos/{owner}/{repo}', timeout=10)
        except Exception as e:                                # noqa: BLE001
            data, err = None, str(e)
        if isinstance(data, dict) and isinstance(data.get('private'), bool):
            vis = 'private' if data['private'] else 'public'
            return vis, f'read from GitHub: {owner}/{repo} is {vis}'
        why = f'GitHub did not say whether {owner}/{repo} is private ({err or "no answer"})'
    elif rc == 0:
        why = 'its origin is not on GitHub, so nothing could say'
    else:
        why = 'it has no origin yet, so nothing could say'
    return 'public', (f'{why}; public is the safe direction -- private-level '
                      f'practices stay out of the tracked AGENTS.md. Pass '
                      f'--visibility private if the repository is private')


def _vendor_catalogue(dest):
    target = dest / UNIVERSAL_PATH / 'practices'
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ROOT / 'practices', target)
    # The source's own files travel with its catalogue, the same list Update
    # Vendors copies (precedent_update.CATALOGUE_COMPANIONS): its manifest,
    # which a consumer's occasion-index cap sums (2026-09-29), its withdrawal
    # record, and its close_detect.json, without which "it notices and
    # offers a rule" did nothing on a fresh install (2026-10-17).
    for comp in CATALOGUE_COMPANIONS:
        if (ROOT / comp).is_file():
            (dest / UNIVERSAL_PATH / comp).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / comp, dest / UNIVERSAL_PATH / comp)
    # The same sync record Update Vendors writes, naming the commit this copy
    # came from -- only when that is true, i.e. this clone's practices/ is
    # exactly its HEAD. Without it a fresh install's every session start said
    # "freshness: NOT VERIFIED" and that the 180 practices just copied were
    # "absent this session" (2026-10-11 install rehearsal).
    head = _run(['git', 'rev-parse', 'HEAD'], ROOT)
    dirty = _run(['git', 'status', '--porcelain', '--', 'practices',
                  *CATALOGUE_COMPANIONS], ROOT)
    if head.returncode == 0 and dirty.returncode == 0 and not dirty.stdout.strip():
        (dest / UNIVERSAL_PATH / 'CATALOGUE_SYNC.json').write_text(json.dumps({
            'source_commit': head.stdout.strip(),
            'written_by': 'tools/precedent_install.py (install)',
            'why': 'the upstream commit practices/ here was copied from; '
                   'the first Update Vendors judges local edits against it'},
            indent=2) + '\n', encoding='utf-8')
    return sum(1 for _ in target.glob('*.md'))


def _tool_lines(r, summary_prefix, drop=()):
    """-> the lines of a child tool's output worth showing an adopter: its
    own summary line (the stdout line starting `summary_prefix`, else its
    last stdout line), then every distinct stderr line not starting with one
    of `drop`. Until 2026-09-28 the installer showed only the last line of
    stdout+stderr combined, so the sync's `OK` line -- the one INSTALL.md §0
    step 6 tells the reader to confirm -- was never shown, and one warning of
    two was."""
    out = [ln for ln in r.stdout.splitlines() if ln.strip()]
    summary = next((ln for ln in out if ln.startswith(summary_prefix)),
                   out[-1] if out else '')
    lines = [summary] if summary else []
    seen = set()
    for ln in r.stderr.splitlines():
        if not ln.strip() or ln in seen or ln.startswith(drop):
            continue
        seen.add(ln)
        lines.append(ln)
    return lines


def _seed_engine(dest):
    r = _run([sys.executable, str(ROOT / 'tools' / 'precedent_vendor_engine.py'),
              'seed', str(dest), '--kind', 'consumer'], ROOT)
    if r.returncode != 0:
        raise InstallRefused(f'the engine seed failed:\n{r.stdout}{r.stderr}')
    # The hook NOTE is always true at seed time and never actionable: the
    # harness step below writes the hooks it names.
    return _tool_lines(r, 'SEEDED', drop=('NOTE: precedent_vendor_engine:',))


def _write_precedent_json(dest, base_branch, visibility, output_paths, teams, force,
                          content_paths=None, no_terminal=False):
    path = dest / 'precedent.json'
    if path.exists() and not force:
        raise InstallRefused(f'{path} already exists -- this project looks '
                             f'installed. Pass --force to overwrite it.')
    sources = [{'level': 'universal', 'name': 'precedent', 'path': UNIVERSAL_PATH}]
    for name, p in teams:
        sources.append({'level': 'shared', 'name': name, 'path': p})
    # repo-local: holds local/practices/project-voice.md and
    # local/practices/project-visual-identity.md, instantiated below. name
    # and path are both fixed to "local" -- practice: source-naming.
    sources.append({'level': 'repo-local', 'name': 'local', 'path': 'local'})
    doc = {
        'format_version': 1,
        'base_branch': base_branch,
        '_base_branch_comment': [
            'The branch this project\'s work is measured against -- what',
            '"changed files" means, and which branch generated links point at.',
            'Written by tools/precedent_install.py; change it here, never in a tool.',
        ],
        'visibility': visibility,
        '_visibility_comment': [
            'public: this repository\'s tracked files are a publication, so the',
            'generated loader block leaves out every PRIVATE-level source (team,',
            'individual). private: they are rendered in. Omitting the key counts',
            'as public, the safe direction (a wrong "public" only leaves those',
            'out; a wrong "private" publishes them) -- and it is always written',
            'explicitly here.',
        ],
        'sources': sources,
    }
    # AN ASSISTANT WITH NO TERMINAL GETS ITS CHECK ON GITHUB (2026-10-17). A
    # private repository's light check runs on a pull request only from a
    # branch Promote named, so off the ladder it ran on none, and an
    # assistant that cannot run the local check got no check anywhere --
    # though SETUP.md's fifth question says that workflow is the only place
    # one can run for it. "always" tests every push to main from any route,
    # once, after it lands (precedent_vendor_engine.render_ci_workflow).
    if no_terminal:
        doc[MAIN_TEST_KEY] = 'always'
        doc['_' + MAIN_TEST_KEY + '_comment'] = [
            'The assistant working here has no terminal, so the local check never',
            'runs; GitHub tests every push to main instead, once it lands, in a',
            'private repository too. Written by tools/precedent_install.py',
            '(--no-terminal). "individual" hands the choice back to Promote.',
        ]
    # The tiered default only when the person installing is on the ladder
    # (spec/LADDER_OPT_IN_PLAN.md D3): for anyone else a repository has its
    # main branch, and its precedent.json says nothing about tiers.
    if precedent_branches.ladder_in_force(path.parent) is not False:
        _landing, _comment = precedent_branches.repo_landing_default(path.parent)
        doc[precedent_branches.LANDING_SETTING] = _landing
        doc['_' + precedent_branches.LANDING_SETTING + '_comment'] = _comment
    if output_paths:
        doc['output_paths'] = output_paths
        doc['_output_paths_comment'] = [
            'The paths this project PUBLISHES; everything else is the project',
            'managing itself. Read by tools/title_case.py and the deliverable',
            'checks. Without it every heading in the tree reads as published.',
        ]
    if content_paths:
        doc['content_paths'] = content_paths
        doc['_content_paths_comment'] = [
            'The person\'s own material kept here -- a personal to-do list,',
            'notes, a manuscript. The checks about session work skip it: an',
            'unchecked box with no (needs: ...) and an unglossed acronym are',
            'theirs to leave. Read by tools/precedent_resolve.py; a "/" ending',
            'covers a directory.',
        ]
    path.write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    return path


def _ci_preference(dest):
    """(enabled: bool, note: str) -- whether precedent_install.py should
    write the GitHub Actions workflow, and a one-line reason for the log.
    practice: declared-default-is-applied -- nothing here asks; absent
    resolves to the engine's own default, which is enabled since 2026-09-25
    (the light check on pull requests into main, and on pushes to main in a
    public repository)."""
    try:
        pref = precedent_identity.ci_preference(dest)
    except precedent_identity.NoDeclaredIdentity:
        return True, ('no individual source declares github_ci_workflows -- '
                      "enabled by default (GITHUB_ACTIONS.md)")
    if pref['enabled']:
        shown = pref['value'] or 'enabled by default'
        return True, f"github_ci_workflows: {shown} ({pref['source']})"
    shown = pref['value'] or '(absent)'
    return False, f"github_ci_workflows: {shown} ({pref['source']})"


_HTML_COMMENT = re.compile(r'<!--.*?-->', re.S)


def _substitute(text, subs, outside_comments=False):
    """Replace each placeholder. With outside_comments, text inside an
    HTML comment is left as written: a template's comment that NAMES a
    placeholder ("`<upstream-docs>` IS ONE OF THOSE PLACEHOLDERS") is
    explaining itself to the installer, and filled in it read as nonsense
    (very deep check, 2026-10-17)."""
    if outside_comments:
        parts, last = [], 0
        for m in _HTML_COMMENT.finditer(text):
            parts.append(_substitute(text[last:m.start()], subs))
            parts.append(m.group(0))
            last = m.end()
        parts.append(_substitute(text[last:], subs))
        return ''.join(parts)
    for old, new in subs.items():
        text = text.replace(old, new)
    return text


def _blank_comments(text):
    """-> `text` with every HTML comment's content blanked, line breaks
    kept, so a line number still points at the same line."""
    return _HTML_COMMENT.sub(lambda m: re.sub(r'[^\n]', ' ', m.group(0)), text)


_CI_PARAGRAPH_ON = (
    "- **Before anything reaches `main`, GitHub checks it once** (the GitHub\n"
    "  Actions workflow `light-check.yml`, on the pull request into `main`). In a\n"
    "  public repository it checks again after a push to `main` that brings\n"
    "  anything it has not already passed. Every other push is checked on your own machine before it leaves. In a\n"
    "  public repository a leak check (`leak-gate.yml`) also runs on every pull\n"
    "  request, and the same check runs on your own machine before every push,\n"
    "  refusing anything that would publish something private. Neither needs\n"
    "  maintenance. If they don't appear on a pull request's checks, GitHub\n"
    "  Actions may be disabled for this repository — an administrator can turn\n"
    "  it on at repository **Settings → Actions**.\n"
    + precedent_vendor_engine.CI_DISCLOSURES['branch-cleanup.yml.template'] +
    "- **Your writing is checked before it is saved, not after.** A formatting\n"
    "  check runs on every commit, so a broken link or a malformed heading is\n"
    "  caught while you are still working rather than once it is shared. This\n"
    "  one is not a GitHub check and needs nothing switched on."
)


def _ci_paragraph_off():
    # practice: github-setup-disclosed -- the workflow this install did NOT
    # write is exactly the kind of GitHub-specific fact this section exists
    # to name, not just log internally.
    return (
        "- **No GitHub Actions workflow was installed.** Precedent's CI\n"
        "  workflows were switched off for this install by the `github_ci_workflows`\n"
        "  setting of the individual or shared source it resolves — GitHub Actions\n"
        "  minutes are metered per private repository and billed in whole-minute\n"
        "  increments per JOB. Turn them on by\n"
        "  declaring `\"github_ci_workflows\": \"enabled\"` in the individual or team\n"
        "  source this project resolves, then re-run the installer with `--force`\n"
        "  — or copy a template in by hand any time. Note that the Markdown\n"
        "  lint is deliberately NOT among them: it runs before every commit\n"
        "  instead. Details:\n"
        f"  [GITHUB_ACTIONS.md]({UPSTREAM_DOCS}/documentation/GITHUB_ACTIONS.md)."
    )


def per_file_substitutions(ci_enabled=True):
    """-> {root file: {text: replacement}}: what an install writes into a
    template beyond its `<placeholder>`s, file by file. One table, read by
    _instantiate_root_files and by precedent_update.py, which re-renders an
    older template the same way to tell an install's untouched copy from
    one the repository edited (2026-10-17)."""
    return {
        # The classic model's manifest bookkeeping has no place here; what a
        # loader install does instead is the standing `Update Vendors` run.
        'TODO.md': {
            "- [ ] **Precedent check-in:** review `diverged` entries in\n"
            "  `process/manifest.json` and the vendored tree's accumulated changes;\n"
            "  propose upstream per `process/upstream/INSTALL.md` §4 (scrub audit first).":
            "- [ ] **Update Vendors:** take the current Precedent catalogue and engine\n"
            f"  when it suits the project (say `Update Vendors` to an assistant;\n"
            f"  the procedure is [{UPSTREAM_DOCS}/INSTALL.md]({UPSTREAM_DOCS}/INSTALL.md) §2).",
        },
        'MAP.source.md': {
            "| `process/` | Practice layer (vendored Precedent + manifest + blocklist) — see [AGENTS.md](AGENTS.md) \"Practice export\". |":
            f"| `{UNIVERSAL_PATH}/` | The vendored Precedent practice catalogue — never hand-edited; refreshed by `Update Vendors`. The engine that reads it is in `tools/`. |",
        },
        'GETTING_STARTED.md': {} if ci_enabled else {_CI_PARAGRAPH_ON: _ci_paragraph_off()},
    }


def _instantiate_root_files(dest, project, owner_repo, admin, base_branch, ci_enabled, force):
    written, skipped = [], []
    today = precedent_time.today(ROOT)  # practice: timestamps-carry-offset
    common = {
        '<project name>': project,
        '<OWNER/REPOSITORY>': owner_repo or '<OWNER/REPOSITORY>',
        '<administrator contact>': f'@{admin}' if admin else '<administrator contact>',
        '<install date>': today,
        '<upstream-docs>': UPSTREAM_DOCS,
        '<precedent upstream URL>': UPSTREAM_URL,
        '<default-branch>': base_branch,
    }
    per_file = per_file_substitutions(ci_enabled)
    for name, tmpl in ROOT_FILES.items():
        target = dest / name
        if target.exists() and not force:
            skipped.append(name)
            continue
        text = (TEMPLATES / tmpl).read_text(encoding='utf-8')
        text = _substitute(text, common, outside_comments=True)
        text = _substitute(text, per_file.get(name, {}))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        written.append(name)
    return written, skipped


def _instantiate_local_practices(dest, force):
    """local/practices/project-voice.md and
    local/practices/project-visual-identity.md -- repo-local PRACTICEs, not
    root documents, so they are instantiated separately from
    _instantiate_root_files and their target directory is created rather
    than assumed to exist."""
    written, skipped = [], []
    today = precedent_time.today(ROOT)  # practice: timestamps-carry-offset
    for rel, tmpl in LOCAL_PRACTICE_FILES.items():
        target = dest / rel
        if target.exists() and not force:
            skipped.append(rel)
            continue
        text = (TEMPLATES / tmpl).read_text(encoding='utf-8')
        text = _substitute(text, {'<install date>': today})
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
        written.append(rel)
    return written, skipped


def _readme(dest, project, about):
    block = (TEMPLATES / 'README_AGENT_ENTRY.md.template').read_text(encoding='utf-8')
    block = block[block.index('<!-- bestpractice-agent-entry:start -->'):]
    readme = dest / 'README.md'
    if readme.exists():
        text = readme.read_text(encoding='utf-8')
        if 'bestpractice-agent-entry:start' in text:
            return 'README.md already carries the entry block'
        lines = text.splitlines(keepends=True)
        # After the first heading and the paragraph under it, so a reader
        # learns what the project is before how it is maintained
        # (practice: lead-with-what-it-is). No heading: at the top.
        # The blank line under the title is skipped first: stopping at it
        # put the block between a title and its description, the common
        # shape of a README (2026-10-17, install rehearsal). A second
        # heading right under the title has no paragraph to wait for.
        insert_at = 0
        if lines and lines[0].startswith('#'):
            insert_at = 1
            while insert_at < len(lines) and not lines[insert_at].strip():
                insert_at += 1
            if insert_at < len(lines) and lines[insert_at].startswith('#'):
                insert_at = 1
            while insert_at < len(lines) and lines[insert_at].strip() \
                    and not lines[insert_at].startswith('#'):
                insert_at += 1
        new = ''.join(lines[:insert_at]) + '\n' + block + '\n' + ''.join(lines[insert_at:])
        readme.write_text(new, encoding='utf-8')
        return 'README.md: entry block inserted after the opening'
    opening = f'# {project}\n\n{about or "<one paragraph: what this project is and does>"}\n\n'
    readme.write_text(opening + block, encoding='utf-8')
    return 'README.md: written (no README existed)' + ('' if about else
                                                        ' -- its opening is a placeholder')


def merge_gitignore(target, tmpl, header):
    """Write templates/gitignore.template's text `tmpl` to `target` when it
    does not exist, else append, under the comment `header`, each of its
    non-comment lines `target` lacks. Additive only: nothing already there is
    changed or removed. -> None when written whole, else [lines appended].

    Shared with precedent_update.py: the template gains lines after a repo is
    installed (.claude/worktrees/, 2026-09-28), and a file written once is
    never looked at again unless the update does it."""
    if not target.exists():
        target.write_text(tmpl, encoding='utf-8')
        return None
    have = target.read_text(encoding='utf-8')
    lines = set(have.splitlines())
    missing = list(dict.fromkeys(l for l in tmpl.splitlines()
                                 if l.strip() and not l.startswith('#')
                                 and l not in lines))
    if missing:
        target.write_text(have.rstrip('\n') + f'\n\n# {header}\n'
                          + '\n'.join(missing) + '\n', encoding='utf-8')
    return missing


def _gitignore(dest):
    tmpl = (TEMPLATES / 'gitignore.template').read_text(encoding='utf-8')
    added = merge_gitignore(dest / '.gitignore', tmpl, 'Added by Precedent\'s installer')
    if added is None:
        return '.gitignore: written'
    if added:
        return f'.gitignore: {len(added)} line(s) appended'
    return '.gitignore: already complete'


def _harness(dest, base_branch, force):
    """The Claude Code adapter: settings.json with the base branch substituted
    into every guard command and the classic-layout allowlist entries
    dropped, plus exactly the hook scripts that settings.json wires."""
    src = TEMPLATES / 'harness' / 'claude-code'
    claude = dest / '.claude'
    hooks_dir = claude / 'hooks'
    hooks_dir.mkdir(parents=True, exist_ok=True)
    settings = json.loads((src / 'settings.json').read_text(encoding='utf-8'))
    wired = []
    for group in settings.get('hooks', {}).values():
        for entry in group:
            for h in entry.get('hooks', []):
                cmd = h.get('command', '')
                if 'freshness-guard.sh' in cmd:
                    parts = cmd.split()
                    parts[-1] = base_branch
                    h['command'] = ' '.join(parts)
                m = re.search(r'hooks/([\w.-]+\.sh)', h.get('command', ''))
                if m:
                    wired.append(m.group(1))
    allow = settings.get('permissions', {}).get('allow')
    if isinstance(allow, list):
        settings['permissions']['allow'] = [a for a in allow if MIRROR_WORDS not in a]
    target = claude / 'settings.json'
    if target.exists() and not force:
        note = '.claude/settings.json: kept (exists); hooks copied'
    else:
        target.write_text(json.dumps(settings, indent=2) + '\n', encoding='utf-8')
        note = f'.claude/settings.json: written, base branch {base_branch!r} in every guard command'
    for name in sorted(set(wired)):
        s = src / 'hooks' / name
        if s.is_file():
            shutil.copy2(s, hooks_dir / name)
            os.chmod(hooks_dir / name, 0o755)
    for name in ('CLAUDE.md',):
        if not (dest / name).exists() or force:
            shutil.copy2(src / name, dest / name)
    return note, sorted(set(wired))


def _record_hooks(dest):
    """Record the hooks _harness() just wired in ENGINE_MANIFEST.json's
    `hook_files`/`hooks_sha256`, through the engine's own _write_hook_files,
    so a refresh tracks them from the first update on.

    seed() runs before _harness(), when no settings.json wires anything, so
    it records no hook at all -- and until 2026-09-28 nothing recorded them
    after: a fresh install's hooks were untracked, and a later refresh could
    neither tell a hand-edit from the stock file nor deliver an upstream
    fix to one. The engine's own copy writes the same bytes _harness() just
    copied from the same templates, then hashes them; its notes about hooks
    this kind does not wire are for a refresh reader, not an installer's."""
    import contextlib
    import io
    with contextlib.redirect_stderr(io.StringIO()):
        written = precedent_vendor_engine._write_hook_files(
            dest, TEMPLATES / 'harness' / 'claude-code' / 'hooks')
    return (f'hooks tracked in tools/ENGINE_MANIFEST.json: {len(written)}'
            if written else 'hooks tracked: none wired')


def _individual_hook(dest):
    """Write and wire the individual-set bootstrap hook the way a refresh
    does (precedent_vendor_engine._apply_individual_hook), before the sync,
    so the sync judges a wired hook rather than warning about an unwired one.

    Until 2026-10-08 nothing in an install did: the sync brought the hook
    file in with the individual set's harness adapter and left it unwired,
    so a fresh install's first full check failed the individual set's own
    check for it ("no SessionStart hook entry ... references it"), and no
    session ran the hook until a later Update Vendors wired it. Add-only,
    and a no-op for a person with no individual set."""
    rc, commit, _ = _git(ROOT, 'rev-parse', 'HEAD')
    if rc != 0:
        return None
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        written = precedent_vendor_engine._apply_individual_hook(
            dest, 'consumer', ROOT, commit)
    if not written:
        return None
    return ('individual-set bootstrap hook: wired first in SessionStart '
            '(the person running this has an individual set)')


def _bootstrap_and_ci(dest, ci_enabled, ci_note, force):
    out = []
    tools = dest / 'tools'
    tools.mkdir(exist_ok=True)
    b = tools / 'bootstrap.sh'
    if not b.exists() or force:
        shutil.copy2(TEMPLATES / 'bootstrap.sh', b)
        os.chmod(b, 0o755)
        out.append('tools/bootstrap.sh: written')
    (dest / '.github').mkdir(exist_ok=True)
    # Loops CI_WORKFLOW_TEMPLATES['consumer'] rather than naming
    # doc-lint.yml.template alone (as this did before leak-gate.yml.template
    # joined it, 2026-09-20, spec/CI_MINUTES_PLAN.md item 12) -- one gate,
    # one loop, so a future consumer-kind template needs no second copy of
    # this block to be written at all.
    # The light check is in that list too since 2026-09-27: the engine owns
    # it, tracks it in the manifest below, and the next refresh replaces a
    # hand-made copy this install found already there
    # (precedent_vendor_engine.CI_CONVERGES_KINDS).
    for _wf_template, _wf_rel in precedent_vendor_engine.CI_WORKFLOW_TEMPLATES['consumer']:
        wf = dest / _wf_rel
        if ci_enabled:
            wf.parent.mkdir(parents=True, exist_ok=True)
            if not wf.exists() or force:
                wf.write_bytes(precedent_vendor_engine.render_ci_workflow(
                    dest, (TEMPLATES / 'github-actions' / _wf_template).read_bytes()))
                out.append(f'{_wf_rel}: written ({ci_note})')
        else:
            out.append(f'{_wf_rel}: NOT written -- {ci_note}')
    pr = dest / '.github' / 'pull_request_template.md'
    if not pr.exists() or force:
        text = (TEMPLATES / 'pull_request_template.md.template').read_text(encoding='utf-8')
        text = text.replace(f'top-level docs vs {MIRROR_WORDS}/.',
                            f'top-level docs vs the vendored {UNIVERSAL_PATH}/ tree.')
        pr.write_text(text, encoding='utf-8')
        out.append('.github/pull_request_template.md: written')
    # Record each installed CI workflow's vendored hash into
    # ENGINE_MANIFEST.json
    # (ci_workflow_files/ci_workflows_sha256) -- AFTER the write above, so
    # what gets hashed is whatever actually landed on disk this call,
    # whether just written or already there from an earlier install. Called
    # unconditionally rather than only inside the `if ci_enabled:` branch
    # above: it merely records whatever is currently on disk, so a repo
    # where CI was disabled (nothing written, nothing to record) is a
    # harmless no-op here, same as _ci_workflow_drift never complaining
    # about a file that is correctly absent. See
    # precedent_vendor_engine.record_ci_workflow_files's own docstring for
    # why this runs after seed(), not before.
    precedent_vendor_engine.record_ci_workflow_files(dest, 'consumer')
    # Same for tools/bootstrap.sh: a baseline recorded now is what lets a
    # later refresh tell the stock file from a locally edited one
    # (precedent_vendor_engine.TEMPLATE_INSTANCES).
    precedent_vendor_engine.record_template_instances(dest, 'consumer',
                                                      TEMPLATES.parent)
    # And for each section AGENTS.md took from its template, which a later
    # refresh brings up to date only while it carries no local edits
    # (precedent_vendor_engine.AGENTS_MD_TEMPLATES).
    precedent_vendor_engine.record_agents_md_sections(dest, 'consumer',
                                                      TEMPLATES.parent)
    return out


_PLACEHOLDER = re.compile(r'<[A-Za-z][^<>\n]{0,70}>')
# An explicit tag list: a lowercase `<word ...>` is far more often a
# template placeholder (`<name them>`, `<path>`) than markup, and treating
# every one as a tag hid a dozen real placeholders from the report
# (very deep check, 2026-09-28).
_HTML_LIKE = re.compile(r'^</?(a|b|br|code|details|div|em|hr|i|img|kbd|li|ol|p|'
                        r'pre|span|strong|sub|summary|sup|table|td|th|tr|ul)'
                        r'(\s|>|/)|^<!--|^-->')


def _placeholders_left(dest, names):
    left = []
    for name in names:
        p = dest / name
        if not p.is_file():
            continue
        # Not inside a comment: a comment that names a placeholder
        # ("Replace <angle-bracket> placeholders ...") renders nowhere and
        # is not one to adapt (2026-10-17).
        for n, line in enumerate(_blank_comments(p.read_text(encoding='utf-8')).splitlines(), 1):
            for m in _PLACEHOLDER.finditer(line):
                tok = m.group(0)
                if _HTML_LIKE.match(tok) or tok in ('<undecided>',):
                    continue
                left.append(f'{name}:{n}: {tok}')
    return left


def _mirror_words_left(dest, names):
    """Lines a READER follows that still name the classic layout. A mention
    inside an HTML comment is a template explaining its own history to the
    installer and renders nowhere; the section-0 grep counts those, which is
    why its list was longer than the real problem."""
    hits = []
    for name in names:
        p = dest / name
        if not p.is_file():
            continue
        in_comment = False
        for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
            if '<!--' in line:
                in_comment = '-->' not in line.split('<!--', 1)[1]
                continue
            if in_comment:
                if '-->' in line:
                    in_comment = False
                continue
            if MIRROR_WORDS in line:
                hits.append(f'{name}:{n}')
    return hits


_UNLINKED_LINE = re.compile(r'^\s+(\S+?):(\d+): `[^`]+` is not a link$')


def _unlinked_outside_generated(dest, lint_out):
    """-> the lint's unlinked-file-name warnings ('FILE:LINE: ...') that
    fall OUTSIDE a generated block, i.e. in text a template wrote.

    The lint reports them as warnings and exits 0, so until 2026-10-06 this
    installer said the light check passed over 18 of them, and INSTALL.md
    section 0 step 8's lint of the same files listed every one (very deep
    check, 2026-10-05, pass 1). A fresh install is the one tree whose text
    is entirely the templates', so here a warning is a template defect and
    is counted. Lines inside a generated block are left out: the generator
    writes those, and the catalogue's own lint judges the practice text it
    carries. A truncated list ("... and N more") cannot be placed line by
    line, so its count is reported whole."""
    import generated_blocks
    masks, found = {}, []
    for line in lint_out.splitlines():
        m = _UNLINKED_LINE.match(line)
        if not m:
            more = re.match(r'^\s+\u2026 and (\d+) more$', line)
            if more:
                found.append(f'{more.group(1)} more, not listed by the lint')
            continue
        rel, n = m.group(1), int(m.group(2))
        if rel not in masks:
            try:
                masks[rel] = generated_blocks.mask(
                    (dest / rel).read_text(encoding='utf-8'))
            except OSError:
                masks[rel] = []
        mask = masks[rel]
        if n - 1 < len(mask) and mask[n - 1]:
            continue
        found.append(line.strip())
    return found


def _tiers(dest):
    """Give the new repository staging on origin when it can (pre-staging
    too until 2026-10-14, when it was retired for everyone)
    (Morgan, 2026-09-27: these branches are essential to the process, so a
    missing one is made, never only reported). A repository installed before
    it has an origin, or before origin has its main, gets them from its first
    Update Vendors instead -- which is said."""
    later = ('the first Update Vendors makes them once origin has main '
             '(or: python3 tools/precedent_branches.py --ensure-tiers --apply)')
    if _run(['git', 'remote', 'get-url', 'origin'], dest).returncode != 0:
        return f'branch tiers: no origin yet -- {later}'
    heads = _run(['git', 'ls-remote', '--heads', 'origin', 'main'], dest)
    if heads.returncode == 0 and not heads.stdout.strip():
        # A brand-new repository: nothing to open a pull request into, so
        # the install lands straight on main and the tiers follow it
        # (Morgan, 2026-10-08).
        return ('branch tiers: not made yet -- origin has no main, so this is a '
                'first landing: commit, push straight to main, then make the '
                'tiers, as INSTALL.md section 0 "The first landing" says')
    lines = []
    try:
        rc = precedent_branches.ensure_tiers(dest, apply=True, say=lines.append,
                                             new_install=True)
    except Exception as e:                                     # noqa: BLE001
        rc, lines = 1, [f'{type(e).__name__}: {e}']
    if rc != 0:
        return f'branch tiers: not made yet ({" ".join(lines)[-200:]}) -- {later}'
    made = [l for l in lines if l.startswith(('created ', 'wrote '))]
    if not made and not lines:
        # Nothing was asked of the tiers: the person installing is not on
        # the ladder, so this repository has its main branch and no more.
        return ''
    return 'branch tiers: ' + ('; '.join(made) if made
                               else 'staging and main both present')


def install(dest, project, about=None, base_branch=None, visibility=None,
            output_paths=None, admin=None, teams=(), force=False, quiet=False,
            content_paths=None, no_terminal=False):
    dest = pathlib.Path(dest).resolve()
    say = (lambda *a: None) if quiet else print
    rc, top, _ = _git(dest, 'rev-parse', '--show-toplevel')
    if rc != 0 or pathlib.Path(top).resolve() != dest:
        raise InstallRefused(f'{dest} is not the root of a git repository. '
                             f'`git init` it first; Precedent lives in the '
                             f'project\'s own history.')
    if (dest / 'tools' / 'ENGINE_MANIFEST.json').exists() and not force:
        raise InstallRefused(f'{dest}/tools/ENGINE_MANIFEST.json exists -- the '
                             f'engine is already vendored here. This is an '
                             f'UPDATE, not an install: INSTALL.md §2. Pass '
                             f'--force to reinstall over it anyway.')
    # A shared set that is not on disk makes the sync refuse AFTER everything
    # else is written, and the engine it just seeded makes a re-run refuse
    # as "already installed" -- so check before writing anything.
    for name, tp in teams:
        if not ((dest / tp).resolve() / 'practices').is_dir():
            raise InstallRefused(f'--team {name}={tp}: no practices/ at '
                                 f'{(dest / tp).resolve()}. Clone that set '
                                 f'there first. Nothing was written.')
    branch, how = _base_branch(dest, base_branch)
    owner, repo = _remote_owner_repo(dest)
    owner_repo = f'{owner}/{repo}' if owner else None
    admin_named = admin
    admin = admin or owner
    ci_enabled, ci_note = _ci_preference(dest)

    say(f'installing Precedent into {dest}')
    say(f'  base branch: {branch} ({how})')
    visibility, vis_how = _visibility(dest, visibility)
    say(f'  visibility: {visibility} ({vis_how})'
        + ('' if visibility == 'private' else ' -- private-level practices will NOT render into AGENTS.md'))
    n = _vendor_catalogue(dest)
    say(f'  vendored {n} practice(s) to {UNIVERSAL_PATH}/practices/')
    for line in _seed_engine(dest):
        say(f'  {line}')
    _write_precedent_json(dest, branch, visibility, output_paths, teams, force,
                          content_paths=content_paths, no_terminal=no_terminal)
    say('  wrote precedent.json')
    if no_terminal:
        say(f'  main\'s GitHub test: always ({MAIN_TEST_KEY}) -- the assistant here has no '
            f'terminal, so GitHub checks every push to main once it lands'
            + ('' if ci_enabled else f'; but no workflow is written ({ci_note}), so '
               f'nothing will run until a source enables them'))
    # Its code owners, from who can edit it now (Morgan, 2026-10-06): a
    # starting default, never rewritten once set.
    try:
        import precedent_vendor_engine as _pve
        _owners, _how = _pve.seed_maintainers(
            dest, fallback=[admin_named.lstrip('@')] if admin_named else None)
    except Exception as e:                                    # noqa: BLE001
        _owners, _how = [], f'could not work it out ({e})'
    say(f'  code owners: ' + (f'named {", ".join("@" + o for o in _owners)} in '
                              f'precedent.json\'s maintainers ({_how})'
                              if _owners else f'none written: {_how}'))
    # The administrator is the account running this (SETUP.md, question 1),
    # so --admin also says who "you" are in this clone. Kept in its git
    # config, never in a tracked file, so it names nobody else's clone; an
    # answer already kept there wins (2026-10-17: with no individual set,
    # nothing else told the engine, and the code-owner practices stayed
    # hidden from the administrator who had just installed them).
    if admin_named:
        try:
            import precedent_audience as _pa
            if _pa.remember_login(dest, admin_named,
                                  'named as the administrator at install (--admin)'):
                say(f'  you: @{admin_named.lstrip("@")}, kept in this clone\'s git '
                    f'config ({_pa.LOGIN_CONFIG_KEY}) so its sessions know who you are')
        except Exception:                                     # noqa: BLE001
            pass
    # The owner's own zone for what runs where no identity reaches, offered
    # and never written (2026-10-08; precedent_vendor_engine.timezone_offer).
    try:
        _offer = _pve.timezone_offer(dest)
    except Exception:                                         # noqa: BLE001
        _offer = None
    if _offer:
        say(f'  time zone, an offer: {_offer}')
    written, skipped = _instantiate_root_files(dest, project, owner_repo, admin, branch, ci_enabled, force)
    say(f'  instantiated: {", ".join(written)}' + (f' (kept existing: {", ".join(skipped)})' if skipped else ''))
    lp_written, lp_skipped = _instantiate_local_practices(dest, force)
    say(f'  instantiated: {", ".join(lp_written)}' + (f' (kept existing: {", ".join(lp_skipped)})' if lp_skipped else ''))
    say(f'  {_readme(dest, project, about)}')
    say(f'  {_gitignore(dest)}')
    note, wired = _harness(dest, branch, force)
    say(f'  {note}; hooks: {", ".join(wired)}')
    say(f'  {_record_hooks(dest)}')
    for line in _bootstrap_and_ci(dest, ci_enabled, ci_note, force):
        say(f'  {line}')
    _tier_note = _tiers(dest)
    if _tier_note:
        say(f'  {_tier_note}')

    _hook_note = _individual_hook(dest)
    if _hook_note:
        say(f'  {_hook_note}')

    r = _run([sys.executable, 'tools/precedent_sync_views.py', '--repo', '.'], dest)
    if r.returncode != 0:
        raise InstallRefused(f'the sync failed:\n{r.stdout}{r.stderr}')
    for line in _tool_lines(r, 'precedent_sync_views OK'):
        say(f'  {line}')
    # The repository's own list of generated files, so its commits rebuild
    # MAP.md and GLOSSARY.md and its checks judge them from the first push.
    _run([sys.executable, 'tools/precedent_migrate_views.py', '--repo', '.'], dest)

    all_instantiated = list(ROOT_FILES) + list(LOCAL_PRACTICE_FILES)
    md = all_instantiated + ['README.md']
    lint = _run([sys.executable, 'tools/doc_lint.py', *md], dest)
    unlinked = _unlinked_outside_generated(dest, lint.stdout)
    lint_ok = lint.returncode == 0 and not unlinked

    say('')
    say('DONE. What is left is judgment, not steps:')
    left = _placeholders_left(dest, all_instantiated)
    if left:
        say(f'  {len(left)} placeholder(s) to adapt with this project\'s own subject matter:')
        for l in left:
            say(f'    {l}')
    else:
        say('  no placeholders left in the instantiated files')
    hits = _mirror_words_left(dest, all_instantiated + ['.github/pull_request_template.md',
                                                        '.claude/settings.json'])
    if hits:
        say(f'  {len(hits)} line(s) still name {MIRROR_WORDS!r}, a layout this project does '
            f'not have -- reword or drop each: {", ".join(hits)}')
    say('  the light check on the written files: ' + ('OK' if lint_ok else 'FAILED -- read below'))
    if lint.returncode != 0:
        say((lint.stdout + lint.stderr).strip())
    elif unlinked:
        say(f'  {len(unlinked)} file name(s) the templates wrote without a link, '
            f'which the doc-references-are-links convention asks for -- a '
            f'template defect, so fix it upstream in templates/:')
        for u in unlinked:
            say(f'    {u}')
    if _run(['git', 'remote', 'get-url', 'origin'], dest).returncode == 0:
        say('  then: review the tree and commit it on a branch.')
    else:
        say('  then: review the tree, commit on a branch, and give the repository an '
            '`origin` before the first session works in it (the freshness guard '
            'refuses the first write while it cannot reach one).')
    say('  still a conversation, not a step: does the team or the person have a '
        'practices repo to wire in? (INSTALL.md section 0 step 3)')
    say(f'  {OTHER_ASSISTANTS_NOTE}')
    return lint_ok


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0
    dest = argv[0]
    opts = {'--project-name': None, '--about': None, '--base-branch': None,
            '--visibility': None, '--output-paths': None, '--admin': None,
            '--content-paths': None}
    teams, force, no_terminal = [], False, False
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '--force':
            force = True
        elif a == '--no-terminal':
            no_terminal = True
        elif a == '--team':
            i += 1
            name, _, path = argv[i].partition('=')
            if not path:
                print('precedent_install FAIL: --team takes NAME=PATH', file=sys.stderr)
                return 1
            teams.append((name, path))
        elif a in opts:
            i += 1
            opts[a] = argv[i]
        else:
            print(f'precedent_install FAIL: unknown argument {a!r}', file=sys.stderr)
            return 1
        i += 1
    if not opts['--project-name']:
        print('precedent_install FAIL: --project-name is required (it names the '
              'Getting Started page and the README opening)', file=sys.stderr)
        return 1
    if opts['--visibility'] not in (None, 'public', 'private'):
        print('precedent_install FAIL: --visibility is public or private', file=sys.stderr)
        return 1
    paths = [p.strip() for p in (opts['--output-paths'] or '').split(',') if p.strip()]
    content = [p.strip() for p in (opts['--content-paths'] or '').split(',') if p.strip()]
    try:
        ok = install(dest, opts['--project-name'], about=opts['--about'],
                     base_branch=opts['--base-branch'], visibility=opts['--visibility'],
                     output_paths=paths or None, admin=opts['--admin'],
                     teams=teams, force=force, content_paths=content or None,
                     no_terminal=no_terminal)
    except InstallRefused as e:
        print(f'precedent_install FAIL: {e}', file=sys.stderr)
        return 1
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
