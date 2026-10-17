#!/usr/bin/env python3
"""precedent_python.py -- one Python per repository (practice: one-python).

    python3 tools/precedent_python.py setup    install and point python3 at it
    python3 tools/precedent_python.py check    say whether python3 is the one
    python3 tools/precedent_python.py bin      print the directory setup puts on PATH

A repository declares the Python its code runs on, and the packages that
code imports, in precedent.json:

    "python": {"version": "3.12", "packages": ["numpy", "scipy"]}

Both keys are optional: the version defaults to DEFAULT_VERSION, the one
GitHub's tests run on (.github/workflows/*.yml, python-version), and
BASE_PACKAGES are always installed, because the engine's own tools import
them.

`setup` is for a hosted session (session start calls it; a person's own
machine manages its own Pythons and is only checked). It

  1. finds the declared interpreter (python3.12 for "3.12") on PATH;
  2. installs the packages with THAT interpreter's pip (`python3.12 -m pip`),
     never a bare `pip`, which belongs to whichever Python it happens to;
  3. makes `python3`, `python`, `pip3` and `pip` mean that interpreter for
     the rest of the session: a small directory of links goes first on
     PATH, through the file Claude Code gives session-start hooks for
     environment that later commands inherit ($CLAUDE_ENV_FILE). Without
     that file (another harness) it prints the line to add instead.

THE INCIDENT (2026-10-13, a consumer). The container had Pythons 3.10 to
3.13 and `python3` was 3.11, with the packages the startup script had
installed through a bare `pip`; python3.12 had none of them. Models
written since the day before used syntax only 3.12 reads. The push check
then failed under python3 (three models "could not be parsed") and under
python3.12 (two models' imports failed: no numpy), and on 2026-10-14 the
lander, which ran its checks as `python3` by name, failed a landing the
same way. Nothing was wrong with the change being checked either time.

Exit 0 ready (or nothing to do); 1 the declared Python is not the one
`python3` runs, or could not be found or set up; 2 usage.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys

DEFAULT_VERSION = '3.12'
BASE_PACKAGES = ['cmarkgfm', 'markdown']
ROOT = pathlib.Path(__file__).resolve().parent.parent


def declared(root=ROOT):
    """-> (version, packages) this repository declares, defaults filled in."""
    try:
        data = json.loads((pathlib.Path(root) / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        data = {}
    py = data.get('python') or {}
    version = str(py.get('version') or DEFAULT_VERSION)
    packages = list(BASE_PACKAGES)
    for p in py.get('packages') or []:
        if p not in packages:
            packages.append(p)
    return version, packages


def interpreter(version):
    """-> the path of pythonX.Y on PATH, or None."""
    return shutil.which(f'python{version}')


def running_version(exe='python3'):
    """-> 'X.Y' of the Python `exe` names, or None."""
    try:
        out = subprocess.run([exe, '-c', 'import sys; print("%d.%d" % sys.version_info[:2])'],
                             capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None
    return out or None


def missing(exe, packages):
    """-> the packages `exe` cannot import (by their import names)."""
    names = {'python-docx': 'docx', 'pyyaml': 'yaml', 'pillow': 'PIL',
             'beautifulsoup4': 'bs4', 'scikit-learn': 'sklearn'}
    out = []
    for p in packages:
        mod = names.get(p.lower(), p.replace('-', '_'))
        r = subprocess.run([exe, '-c', f'import {mod}'], capture_output=True)
        if r.returncode:
            out.append(p)
    return out


def pip_install(exe, packages):
    """`exe -m pip install --quiet packages` -> the CompletedProcess.

    THE ONE INSTALL CALL every engine tool that installs a package makes.
    A distribution's Python marks itself managed by apt (PEP 668), and pip
    refuses outright; in a throwaway container that is the Python we mean
    to use, so the refusal is retried with --break-system-packages. The
    push check's own installer made the plain call and stopped on that
    refusal in a cloud container (2026-10-15) -- a second copy of an
    install line is a second place to forget it."""
    cmd = [exe, '-m', 'pip', 'install', '--quiet', *packages]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode and 'externally-managed' in (r.stderr + r.stdout):
        r = subprocess.run(cmd + ['--break-system-packages'], capture_output=True, text=True)
    return r


def install(exe, packages):
    """Install `packages` into `exe` with its own pip. -> '' or why not."""
    need = missing(exe, packages)
    if not need:
        return ''
    r = pip_install(exe, need)
    if r.returncode:
        tail = (r.stderr or r.stdout).strip().splitlines()[-1:] or ['']
        return f'{exe} -m pip install {" ".join(need)} failed: {tail[0]}'
    still = missing(exe, need)
    return f'installed, but {exe} still cannot import {", ".join(still)}' if still else ''


def shim_dir(version):
    base = pathlib.Path(os.environ.get('XDG_CACHE_HOME') or pathlib.Path.home() / '.cache')
    return base / 'precedent' / f'python{version}' / 'bin'


def make_shims(exe, version):
    """A directory where python3, python, pip3 and pip mean `exe`."""
    d = shim_dir(version)
    d.mkdir(parents=True, exist_ok=True)
    for name in ('python3', 'python'):
        link = d / name
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(exe)
    for name in ('pip3', 'pip'):
        (d / name).write_text(f'#!/bin/sh\nexec "{exe}" -m pip "$@"\n', encoding='utf-8')
        (d / name).chmod(0o755)
    return d


def export_path(d):
    """Put `d` first on PATH for the rest of the session. -> what was done."""
    line = f'export PATH="{d}:$PATH"\n'
    env_file = os.environ.get('CLAUDE_ENV_FILE')
    if not env_file:
        return f'no session environment file here: add `{line.strip()}` to this harness\'s session setup'
    try:
        have = pathlib.Path(env_file).read_text(encoding='utf-8') if os.path.exists(env_file) else ''
        if line not in have:
            with open(env_file, 'a', encoding='utf-8') as f:
                f.write(line)
    except OSError as e:
        return f'could not write {env_file}: {e}'
    return ''


def link_for_hooks(d, root=ROOT):
    """Link `d` at <root>/.precedent/python-bin for the hooks. -> '' or why not.

    The session file reaches the Bash tool's commands only; Claude Code
    starts every hook with its own PATH (2026-10-16). Each hook script in
    tools/ puts this link first on PATH before its first python3, so the
    gates run the declared Python with every declared package, not just the
    engine's own (practice: one-python). Per checkout, under the gitignored .precedent/, because
    two repositories in one container may declare different versions."""
    link = pathlib.Path(root) / '.precedent' / 'python-bin'
    try:
        link.parent.mkdir(exist_ok=True)
        if link.is_symlink() or link.exists():
            if link.is_symlink() and os.readlink(link) == str(d):
                return ''
            link.unlink()
        link.symlink_to(d, target_is_directory=True)
    except OSError as e:
        return f'could not link {link} for the hooks: {e}'
    return ''


def setup(root=ROOT):
    version, packages = declared(root)
    exe = interpreter(version)
    if not exe:
        print(f'precedent_python: WARN -- this repository declares Python {version}, and there '
              f'is no python{version} on PATH; python3 here is {running_version() or "missing"}. '
              'Install it, or change "python" in precedent.json.', file=sys.stderr)
        return 1
    shims = make_shims(exe, version)
    problems = [p for p in (install(exe, packages), export_path(shims),
                            link_for_hooks(shims, root), hook_install(exe)) if p]
    for p in problems:
        print(f'precedent_python: WARN -- {p}', file=sys.stderr)
    if not problems:
        print(f'precedent_python: python3 is Python {version} ({exe}) for this session, '
              f'with {", ".join(packages)}.')
    return 1 if problems else 0


def hook_install(exe, running=sys.executable):
    """Give the Python hooks run the packages the gates import. -> '' or why not.

    THE GAP (2026-10-16, a consumer). The session file reaches the Bash
    tool's commands only. Claude Code starts every hook with its own PATH,
    where `python3` is still the image's default (3.13 beside a declared
    3.12), so the prompt gate, run as a hook, found cmarkgfm and markdown
    missing a minute after this setup reported them installed. Setup runs
    from the session-start hook before the PATH line, so the Python running
    it is the one the hooks get; when that is not the declared one, the
    engine's own packages go there too. Only BASE_PACKAGES: a hook runs
    engine tools, and the push check installs what else it needs itself
    (practice: one-python). Since link_for_hooks the hooks start the
    declared Python whenever setup has run; this stays for the hooks that
    run before it ever has, the first session start's own."""
    if not running or os.path.realpath(running) == os.path.realpath(exe):
        return ''
    why = install(running, BASE_PACKAGES)
    return f'for the Python hooks run ({running}): {why}' if why else ''


def check(root=ROOT):
    version, packages = declared(root)
    have = running_version()
    if have != version:
        print(f'precedent_python: python3 here is {have or "missing"}, and this repository '
              f'runs on {version}: run `python{version}`, or `python3 tools/precedent_python.py setup` '
              'in a hosted session.', file=sys.stderr)
        return 1
    gone = missing('python3', packages)
    if gone:
        print(f'precedent_python: python3 ({version}) cannot import {", ".join(gone)}.', file=sys.stderr)
        return 1
    print(f'precedent_python: python3 is {version}, with {", ".join(packages)}.')
    return 0


def main(argv):
    if argv[1:] == ['setup']:
        return setup()
    if argv[1:] == ['check']:
        return check()
    if argv[1:2] in (['--help'], ['-h']):
        print(__doc__)
        return 0
    if argv[1:] == ['bin']:
        print(shim_dir(declared()[0]))
        return 0
    print(__doc__.split('\n\n')[0], file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
