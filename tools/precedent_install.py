#!/usr/bin/env python3
"""precedent_install.py -- install Precedent into a project in one command.

Run from a clone of Precedent (this repository), pointed at the project:

  python3 tools/precedent_install.py <project path> --project-name "Recipe Book" \\
      [--about "one sentence, used only if the project has no README yet"] \\
      [--base-branch main] [--visibility private|public] \\
      [--output-paths docs,site] [--admin github-handle] \\
      [--team NAME=PATH ...] [--force]

It performs INSTALL.md section 0 -- the loader install -- mechanically: it
vendors the practice catalogue and the engine, writes precedent.json,
instantiates every template section 0 names with the placeholders this
tool can know filled in, runs the sync, lints the files it wrote, and then
prints exactly what it could NOT decide: the placeholders left for a person
or an assistant to adapt, and any wording that still names a layout this
project does not have. It never commits, never pushes, never asks.

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
It does not wire a team or individual source beyond what --team declares;
the team/individual question is a conversation with the administrator
(INSTALL.md section 1 step 9). It does not commit: a person reviews the tree
first. And it does not run the freshness guard or any session hook -- those
run in the project's own sessions from then on.

IT DOES NOT INSTALL THE GITHUB ACTIONS WORKFLOW EITHER, unless the
individual or team source it resolves declares `"ci_workflows": "enabled"`
in identity.json (2026-09-15, reversing the previous unconditional
install). GitHub Actions minutes are metered per PRIVATE repository and
billed per run, rounded up to the minute; installing the workflow into
every dependent repo by default charges an adopter who vendors Precedent
into many private repos for checks they never asked to run. Nothing
declared resolves to disabled -- the tool still names the reason in its
output and in the project's own GETTING_STARTED.md. See GITHUB_ACTIONS.md.

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
TEMPLATES = ROOT / 'templates'
UPSTREAM_URL = 'https://github.com/alex137/BestPractice'
UPSTREAM_DOCS = f'{UPSTREAM_URL}/blob/main'
UNIVERSAL_PATH = 'precedent/universal'

# What section 0 instantiates at the project root, and the template each
# comes from. GETTING_STARTED.md is a template that keeps a plain .md name
# on purpose (it doubles as the rendered sample).
ROOT_FILES = {
    'AGENTS.md': 'AGENTS.md.loader.template',
    'MAP.md': 'MAP.md.template',
    'TODO.md': 'TODO.md.template',
    'GLOSSARY.md': 'GLOSSARY.md.template',
    'GETTING_STARTED.md': 'GETTING_STARTED.md',
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


def _declared_base_branch(root):
    """precedent.json's `base_branch`, or None -- the same helper every other
    resolver in the engine carries, so the `declared-base-branch` check sees
    the declaration read before any inference below."""
    try:
        v = json.loads((pathlib.Path(root) / 'precedent.json')
                       .read_text(encoding='utf-8')).get('base_branch')
        return v if isinstance(v, str) and v.strip() else None
    except Exception:
        return None


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
        return ref.rsplit('/', 1)[1], "inferred from origin's default branch"
    rc, cur, _ = _git(dest, 'rev-parse', '--abbrev-ref', 'HEAD')
    if rc == 0 and cur and cur != 'HEAD':
        return cur, 'inferred from the branch checked out now (no origin)'
    return 'main', 'assumed; the repository has no branch yet'


def _vendor_catalogue(dest):
    target = dest / UNIVERSAL_PATH / 'practices'
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(ROOT / 'practices', target)
    return sum(1 for _ in target.glob('*.md'))


def _seed_engine(dest):
    r = _run([sys.executable, str(ROOT / 'tools' / 'precedent_vendor_engine.py'),
              'seed', str(dest), '--kind', 'consumer'], ROOT)
    if r.returncode != 0:
        raise InstallRefused(f'the engine seed failed:\n{r.stdout}{r.stderr}')
    return (r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else ''


def _write_precedent_json(dest, base_branch, visibility, output_paths, teams, force):
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
            'as public, which is the direction that cannot be undone -- so it is',
            'always written explicitly here.',
        ],
        'sources': sources,
    }
    if output_paths:
        doc['output_paths'] = output_paths
        doc['_output_paths_comment'] = [
            'The paths this project PUBLISHES; everything else is the project',
            'managing itself. Read by tools/title_case.py and the deliverable',
            'checks. Without it every heading in the tree reads as published.',
        ]
    path.write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
    return path


def _ci_preference(dest):
    """(enabled: bool, note: str) -- whether precedent_install.py should
    write the GitHub Actions workflow, and a one-line reason for the log.
    practice: declared-default-is-applied -- nothing here asks; absent
    resolves to the engine's own default, which is enabled since 2026-09-25
    (the light check on pull requests into main only)."""
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


def _substitute(text, subs):
    for old, new in subs.items():
        text = text.replace(old, new)
    return text


_CI_PARAGRAPH_ON = (
    "- **Before anything reaches `main`, GitHub checks it once** (the GitHub\n"
    "  Actions workflow `light-check.yml`, on the pull request into `main`).\n"
    "  Every other push is checked on your own machine before it leaves. In a\n"
    "  public repository a leak check (`leak-gate.yml`) also runs on every push\n"
    "  and refuses anything that would publish something private. Neither needs\n"
    "  maintenance. If they don't appear on a pull request's checks, GitHub\n"
    "  Actions may be disabled for this repository — an administrator can turn\n"
    "  it on at repository **Settings → Actions**.\n"
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
        "  setting of the individual or team source it resolves — GitHub Actions\n"
        "  minutes are metered per private repository and billed in whole-minute\n"
        "  increments per JOB. Turn them on by\n"
        "  declaring `\"github_ci_workflows\": \"enabled\"` in the individual or team\n"
        "  source this project resolves, then re-run the installer with `--force`\n"
        "  — or copy a template in by hand any time. Note that the Markdown\n"
        "  lint is deliberately NOT among them: it runs before every commit\n"
        "  instead. Details:\n"
        f"  [GITHUB_ACTIONS.md]({UPSTREAM_DOCS}/documentation/GITHUB_ACTIONS.md)."
    )


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
    per_file = {
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
        'MAP.md': {
            "| `process/` | Practice layer (vendored Precedent + manifest + blocklist) — see [AGENTS.md](AGENTS.md) \"Practice export\". |":
            f"| `{UNIVERSAL_PATH}/` | The vendored Precedent practice catalogue — never hand-edited; refreshed by `Update Vendors`. The engine that reads it is in `tools/`. |",
        },
        'GETTING_STARTED.md': {} if ci_enabled else {_CI_PARAGRAPH_ON: _ci_paragraph_off()},
    }
    for name, tmpl in ROOT_FILES.items():
        target = dest / name
        if target.exists() and not force:
            skipped.append(name)
            continue
        text = (TEMPLATES / tmpl).read_text(encoding='utf-8')
        text = _substitute(text, common)
        text = _substitute(text, per_file.get(name, {}))
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
        insert_at = 0
        if lines and lines[0].startswith('#'):
            insert_at = 1
            while insert_at < len(lines) and lines[insert_at].strip():
                insert_at += 1
        new = ''.join(lines[:insert_at]) + '\n' + block + '\n' + ''.join(lines[insert_at:])
        readme.write_text(new, encoding='utf-8')
        return 'README.md: entry block inserted after the opening'
    opening = f'# {project}\n\n{about or "<one paragraph: what this project is and does>"}\n\n'
    readme.write_text(opening + block, encoding='utf-8')
    return 'README.md: written (no README existed)' + ('' if about else
                                                        ' -- its opening is a placeholder')


def _gitignore(dest):
    tmpl = (TEMPLATES / 'gitignore.template').read_text(encoding='utf-8')
    target = dest / '.gitignore'
    if not target.exists():
        target.write_text(tmpl, encoding='utf-8')
        return '.gitignore: written'
    have = target.read_text(encoding='utf-8')
    missing = [l for l in tmpl.splitlines()
               if l.strip() and not l.startswith('#') and l not in have.splitlines()]
    if missing:
        target.write_text(have.rstrip('\n') + '\n\n# Added by Precedent\'s installer\n'
                          + '\n'.join(missing) + '\n', encoding='utf-8')
        return f'.gitignore: {len(missing)} line(s) appended'
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


def _approve_installed_workflow(dest, rel, template):
    """Record an install-only workflow in precedent.json's
    github_ci_approved, pinned to what was just written. The manifest does
    not track these (no refresh ever touches them), so without this a fresh
    install's first push would fail ci-workflow-approved over a file the
    installer itself wrote. The entry names the template rather than
    quoting anyone: installing is the person's act, and any later edit
    changes the hash and needs their words (practice: ci-workflow-approved).
    """
    import hashlib
    path = dest / 'precedent.json'
    try:
        cfg = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return
    approved = cfg.setdefault('github_ci_approved', {})
    approved[rel] = {
        'sha256': hashlib.sha256((dest / rel).read_bytes()).hexdigest(),
        'approved_by': (f'installed by precedent_install.py, '
                        f'{precedent_time.today(ROOT)}'),
        'template': template,
    }
    path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + '\n',
                    encoding='utf-8')


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
    # The light check (CI_INSTALL_ONLY_TEMPLATES) is written only where no
    # light-check.yml exists, --force or not: an existing one is somebody's
    # own check, running their own command.
    for _wf_template, _wf_rel in (
            *precedent_vendor_engine.CI_WORKFLOW_TEMPLATES['consumer'],
            *precedent_vendor_engine.CI_INSTALL_ONLY_TEMPLATES['consumer']):
        wf = dest / _wf_rel
        _install_only = (_wf_template, _wf_rel) in \
            precedent_vendor_engine.CI_INSTALL_ONLY_TEMPLATES['consumer']
        if ci_enabled:
            wf.parent.mkdir(parents=True, exist_ok=True)
            if not wf.exists() or (force and not _install_only):
                shutil.copy2(TEMPLATES / 'github-actions' / _wf_template, wf)
                out.append(f'{_wf_rel}: written ({ci_note})')
                if _install_only:
                    _approve_installed_workflow(dest, _wf_rel, _wf_template)
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
_HTML_LIKE = re.compile(r'^</?[a-z]+(\s|>|/)|^<!--|^-->')


def _placeholders_left(dest, names):
    left = []
    for name in names:
        p = dest / name
        if not p.is_file():
            continue
        for n, line in enumerate(p.read_text(encoding='utf-8').splitlines(), 1):
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


def install(dest, project, about=None, base_branch=None, visibility='private',
            output_paths=None, admin=None, teams=(), force=False, quiet=False):
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
    branch, how = _base_branch(dest, base_branch)
    owner, repo = _remote_owner_repo(dest)
    owner_repo = f'{owner}/{repo}' if owner else None
    admin = admin or owner
    ci_enabled, ci_note = _ci_preference(dest)

    say(f'installing Precedent into {dest}')
    say(f'  base branch: {branch} ({how})')
    say(f'  visibility: {visibility}'
        + ('' if visibility == 'private' else ' -- private-level practices will NOT render into AGENTS.md'))
    n = _vendor_catalogue(dest)
    say(f'  vendored {n} practice(s) to {UNIVERSAL_PATH}/practices/')
    say(f'  {_seed_engine(dest)}')
    _write_precedent_json(dest, branch, visibility, output_paths, teams, force)
    say('  wrote precedent.json')
    written, skipped = _instantiate_root_files(dest, project, owner_repo, admin, branch, ci_enabled, force)
    say(f'  instantiated: {", ".join(written)}' + (f' (kept existing: {", ".join(skipped)})' if skipped else ''))
    lp_written, lp_skipped = _instantiate_local_practices(dest, force)
    say(f'  instantiated: {", ".join(lp_written)}' + (f' (kept existing: {", ".join(lp_skipped)})' if lp_skipped else ''))
    say(f'  {_readme(dest, project, about)}')
    say(f'  {_gitignore(dest)}')
    note, wired = _harness(dest, branch, force)
    say(f'  {note}; hooks: {", ".join(wired)}')
    for line in _bootstrap_and_ci(dest, ci_enabled, ci_note, force):
        say(f'  {line}')

    r = _run([sys.executable, 'tools/precedent_sync_views.py', '--repo', '.'], dest)
    if r.returncode != 0:
        raise InstallRefused(f'the sync failed:\n{r.stdout}{r.stderr}')
    say(f'  {(r.stdout + r.stderr).strip().splitlines()[-1]}')

    all_instantiated = list(ROOT_FILES) + list(LOCAL_PRACTICE_FILES)
    md = all_instantiated + ['README.md']
    lint = _run([sys.executable, 'tools/doc_lint.py', *md], dest)
    lint_ok = lint.returncode == 0

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
    if not lint_ok:
        say((lint.stdout + lint.stderr).strip())
    say('  then: review the tree, commit on a branch, and give the repository an `origin` '
        'before the first session works in it (the freshness guard refuses the first '
        'write while it cannot reach one).')
    say('  still a conversation, not a step: does the team or the person have a '
        'practices repo to wire in? (INSTALL.md §1 step 9)')
    return lint_ok


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0
    dest = argv[0]
    opts = {'--project-name': None, '--about': None, '--base-branch': None,
            '--visibility': 'private', '--output-paths': None, '--admin': None}
    teams, force = [], False
    i = 1
    while i < len(argv):
        a = argv[i]
        if a == '--force':
            force = True
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
    if opts['--visibility'] not in ('public', 'private'):
        print('precedent_install FAIL: --visibility is public or private', file=sys.stderr)
        return 1
    paths = [p.strip() for p in (opts['--output-paths'] or '').split(',') if p.strip()]
    try:
        ok = install(dest, opts['--project-name'], about=opts['--about'],
                     base_branch=opts['--base-branch'], visibility=opts['--visibility'],
                     output_paths=paths or None, admin=opts['--admin'],
                     teams=teams, force=force)
    except InstallRefused as e:
        print(f'precedent_install FAIL: {e}', file=sys.stderr)
        return 1
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
