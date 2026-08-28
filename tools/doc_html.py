#!/usr/bin/env python3
"""doc_html -- the ONE sortable-table HTML renderer for repo documents
(practice 44).

Convention: any document whose tables have multiple columns a reader might
want to sort ships an HTML render built from the .md by THIS module -- the
.md stays the source of record (doc_sync keeps its generated tables live,
practice 33), the .html is the committed reading product. Table behavior
(multi-column sort, pinned sort columns, sticky headers, numeric-aware sort
keys) lives HERE and only here, so a functionality change upgrades every
table in the repo at once: edit CSS/JS below, run `python3 tools/doc_html.py`
(no args = rebuild everything in DOCS), commit the renders.

    python3 tools/doc_html.py                # rebuild all registered docs
    python3 tools/doc_html.py path/to/doc.md # render one (registered or not)
    python3 tools/doc_html.py --list         # show the registry

Behavior contract (the full spec is practice 44's numbered list; this
module is its reference implementation): multi-column sort (click; shift-
click or Multi-sort adds keys; re-click reverses; header marks show key
order) with numeric-aware keys (approximation marks, currency, thousands
separators, k/M suffixes, units; em-dash empties last); per-column value-
filter dropdowns (2-60 distinct values; MULTI-select -- each opens a
checkbox panel, any checked subset keeps its rows, none checked = All,
the button shows the selection); sorted and filtered columns pin
where they sit and stay visible under horizontal scroll, with sticky
headers -- column movement is user-driven only (drag a header); one Reset
clearing sorts AND
filters and restoring row/column order; a live "N of M rows" count; a
frontier-only toggle where a Frontier column exists (practice 45); header
cells link their definition notes with mouse-over tooltips, and each
note's return link lands back on the header cell it defines; the build
timestamp renders in the page header (the .html is the versioned product;
the source carries none); includes expanded, relative repo links
rewritten to the hosted view, wide tables scrolling in their own
container.

Host configuration: fill DOCS with (repo-relative .md, title) pairs. Link
rewriting targets the repo's own hosted-view URL, detected from the git
remote; override LINK_BASE if detection does not fit your host.

Per-document build scripts may keep documented entry points, but as thin
wrappers importing render() from here -- never as forks of the CSS/JS.

Requires: pip install markdown.
"""

import html as html_mod  # noqa: F401  (kept for extensions that escape text)
import re
import sys
from pathlib import Path

import markdown

import subprocess
import datetime


def find_root(start):
    """Git toplevel containing this file (the renderer lives in the repo it
    serves)."""
    r = subprocess.run(["git", "-C", str(start), "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    return Path(r.stdout.strip()) if r.returncode == 0 else Path(start).parents[1]


ROOT = find_root(Path(__file__).resolve().parent)


def _link_base():
    """Hosted-view base URL for rewriting relative repo links, from the git
    remote (GitHub-shaped hosts); override LINK_BASE for others."""
    r = subprocess.run(["git", "-C", str(ROOT), "remote", "get-url", "origin"],
                       capture_output=True, text=True)
    url = r.stdout.strip()
    if url.startswith("git@"):
        url = url.replace(":", "/", 1).replace("git@", "https://", 1)
    if url.endswith(".git"):
        url = url[:-4]
    return f"{url}/blob/master/" if url else ""


LINK_BASE = _link_base()

# Registry: (repo-relative source .md, page title). Output = same stem, .html.
# Host repos fill this in.
DOCS = []

CSS = """
.renderstamp { color: var(--muted); font-size: 12px; margin: -0.6rem 0 1.6rem; }
.filterrow .fbtn { width: 100%; max-width: 160px; font-size: 11px; color: var(--muted); background: var(--surface); border: 1px solid var(--hairline); border-radius: 4px; cursor: pointer; padding: 1px 5px; text-align: left; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.filterrow .fbtn.on { color: var(--accent, #2563eb); border-color: var(--accent, #2563eb); }
.filterrow td { padding: 2px 4px; background: var(--head-bg); }
.fpanel { position: fixed; z-index: 60; background: var(--surface); border: 1px solid var(--hairline); border-radius: 6px; box-shadow: 0 4px 14px rgba(0,0,0,.18); padding: 6px 8px; max-height: 260px; overflow-y: auto; font-size: 12px; min-width: 150px; max-width: 320px; }
.fpanel label { display: block; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer; padding: 1px 2px; }
.fpanel label.fall { border-bottom: 1px solid var(--hairline); margin-bottom: 4px; padding-bottom: 3px; }
.fpanel input { margin-right: 6px; }
.rowcount { color: var(--muted); margin-left: 0.5rem; }
:root {
  --ground: #F7F6F2; --surface: #FFFFFF; --ink: #22262B; --muted: #66707A;
  --accent: #2A5E8C; --hairline: #DCD9D1; --stripe: rgba(42, 94, 140, 0.05);
  --head-bg: #EEECE5; --hover: rgba(42, 94, 140, 0.12);
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --ground: #15181B; --surface: #1C2024; --ink: #E7E4DD; --muted: #9AA3AC;
    --accent: #7FB2DE; --hairline: #2E343A; --stripe: rgba(127, 178, 222, 0.06);
    --head-bg: #22272C; --hover: rgba(127, 178, 222, 0.16);
  }
}
:root[data-theme="dark"] {
  --ground: #15181B; --surface: #1C2024; --ink: #E7E4DD; --muted: #9AA3AC;
  --accent: #7FB2DE; --hairline: #2E343A; --stripe: rgba(127, 178, 222, 0.06);
  --head-bg: #22272C; --hover: rgba(127, 178, 222, 0.16);
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--ground); color: var(--ink);
  font: 16px/1.55 "Source Sans 3", "Segoe UI", system-ui, sans-serif;
}
main { max-width: 1500px; margin: 0 auto; padding: 2rem 1.5rem 4rem; }
h1, h2, h3 {
  font-family: "Barlow Semi Condensed", "Arial Narrow", system-ui, sans-serif;
  font-weight: 600; line-height: 1.15; text-wrap: balance; color: var(--ink);
}
h1 { font-size: 2.3rem; margin: 0.4rem 0 0.2rem; }
h2 { font-size: 1.55rem; margin: 2.4rem 0 0.6rem; border-bottom: 2px solid var(--accent); padding-bottom: 0.25rem; }
h3 { font-size: 1.2rem; margin: 1.8rem 0 0.5rem; }
p, ul, ol { max-width: 72ch; }
li { margin: 0.3rem 0; }
a { color: var(--accent); }
code { font: 0.86em ui-monospace, "Cascadia Mono", Menlo, monospace;
       background: var(--stripe); padding: 0.08em 0.3em; border-radius: 3px; }
hr { border: 0; border-top: 1px solid var(--hairline); margin: 2.5rem 0 1.5rem; }
.tablewrap { overflow-x: auto; margin: 1rem 0 0.5rem; }
table {
  border-collapse: collapse; background: var(--surface);
  font-size: 0.8rem; line-height: 1.35;
  font-variant-numeric: tabular-nums;
  border: 1px solid var(--hairline);
}
th, td { padding: 0.32rem 0.55rem; border: 1px solid var(--hairline);
         text-align: left; vertical-align: top; }
tbody tr:nth-child(even) { background: var(--stripe); }
thead th {
  position: sticky; top: 0; z-index: 2;
  background: var(--head-bg); color: var(--ink);
  font-family: "Barlow Semi Condensed", "Arial Narrow", sans-serif;
  font-size: 0.78rem; letter-spacing: 0.02em;
  cursor: pointer; user-select: none; white-space: normal; min-width: 4.5rem;
}
thead th:hover { background: var(--hover); }
thead th .sortmark { color: var(--accent); font-size: 0.7rem; white-space: nowrap; }
td.pinned, th.pinned { position: sticky; background: var(--head-bg); }
td.pinned { z-index: 1; }
th.pinned { z-index: 3; }
td.pinned { box-shadow: 1px 0 0 var(--hairline); }
.sortbar { display: flex; gap: 0.6rem; align-items: center;
  font-size: 0.75rem; color: var(--muted); margin: 0.9rem 0 -0.5rem; }
.sortbar button {
  font: inherit; color: var(--ink); background: var(--surface);
  border: 1px solid var(--hairline); border-radius: 4px;
  padding: 0.1rem 0.55rem; cursor: pointer; }
.sortbar button[aria-pressed="true"] {
  background: var(--accent); color: var(--ground); border-color: var(--accent); }
.sortbar button:hover { border-color: var(--accent); }
caption, .tablehint {
  font-size: 0.78rem; color: var(--muted); text-align: left;
  max-width: 72ch; margin: 0.2rem 0 0;
}
/* narrow tables (requirements, launch means) read at prose width */
table.narrow { font-size: 0.9rem; }
:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { * { transition: none !important; } }
"""

JS = """
(function () {
  function keyOf(cell) {
    var t = cell.textContent.trim();
    if (t === "—" || t === "") return { n: -Infinity, s: "" };
    var kmatch = /\\$\\s*[\\d.,]+k/.test(t);
    var mmatch = /\\$\\s*[\\d.,]+\\s*M/.test(t);
    var m = t.replace(/[,≈≤≥]/g, "").match(/-?\\d+(?:\\.\\d+)?/);
    if (m) {
      var v = parseFloat(m[0]);
      if (kmatch) v *= 1000;
      if (mmatch) v *= 1000000;
      return { n: v, s: t.toLowerCase() };
    }
    return { n: null, s: t.toLowerCase() };
  }
  document.querySelectorAll("table").forEach(function (tbl) {
    var head = tbl.tHead;
    if (!head || !tbl.tBodies.length) return;
    var hrow = head.rows[0];
    var original = Array.prototype.slice.call(tbl.tBodies[0].rows);
    var ncols = hrow.cells.length;
    // Stamp every cell with its ORIGINAL column index; all later logic is
    // keyed on these, so physically reordering columns never confuses it.
    Array.prototype.forEach.call(hrow.cells, function (c, i) { c.dataset.col = i; });
    original.forEach(function (r) {
      Array.prototype.forEach.call(r.cells, function (c, i) { c.dataset.col = i; });
    });
    var baseOrder = [];
    for (var bi = 0; bi < ncols; bi++) baseOrder.push(bi);
    var sorts = [];   // [{col: original index, dir}]
    var multi = false, frontierOnly = false;

    var bar = document.createElement("div");
    bar.className = "sortbar";
    var multiBtn = document.createElement("button");
    multiBtn.textContent = "Multi-sort";
    multiBtn.setAttribute("aria-pressed", "false");
    multiBtn.title = "When on, each header click ADDS a sort key instead of replacing (same as shift-click)";
    multiBtn.addEventListener("click", function () {
      multi = !multi;
      multiBtn.setAttribute("aria-pressed", String(multi));
    });
    var resetBtn = document.createElement("button");
    resetBtn.textContent = "Reset";
    resetBtn.title = "Clear sorts and filters; restore the original row and column order";
    var label = document.createElement("span");
    label.textContent = "Sort: click a header · shift-click or Multi-sort adds keys · sorted/filtered columns pin in place while scrolling · drag a header to move a column";
    var count = document.createElement("span");
    count.className = "rowcount";
    bar.appendChild(multiBtn);
    bar.appendChild(resetBtn);
    bar.appendChild(label);
    var wrap = tbl.closest(".tablewrap") || tbl;
    wrap.parentNode.insertBefore(bar, wrap);

    // Multi-select value filters: a button per column opens a
    // checkbox panel; checked values keep their rows (none checked =
    // All). filterState maps column id -> {value: 1} set.
    var filterState = {};
    var openPanel = null;
    function closePanel() {
      if (openPanel) { openPanel.remove(); openPanel = null; }
    }
    document.addEventListener("click", function (e) {
      if (openPanel && !openPanel.contains(e.target)) closePanel();
    });
    window.addEventListener("resize", closePanel);
    var fr = head.insertRow(-1);
    fr.className = "filterrow";
    Array.prototype.forEach.call(hrow.cells, function (th, i) {
      var cell = fr.insertCell(-1);
      cell.dataset.col = th.dataset.col;
      var col = +th.dataset.col;
      var vals = {};
      original.forEach(function (r) {
        if (r.cells[i]) vals[r.cells[i].textContent.trim()] = 1;
      });
      var names = Object.keys(vals).sort(function (a, b) {
        var ka = keyOf({ textContent: a }), kb = keyOf({ textContent: b });
        if (ka.n !== null && kb.n !== null && ka.n !== kb.n) return ka.n - kb.n;
        return a < b ? -1 : a > b ? 1 : 0;
      });
      if (names.length < 2 || names.length > 60) return;
      var st = (filterState[col] = {});
      var btn = document.createElement("button");
      btn.type = "button";
      btn.className = "fbtn";
      btn.textContent = "All";
      btn.title = "Filter this column: check one or more values";
      btn._sync = function () {
        var picked = Object.keys(st);
        btn.textContent = picked.length === 0 ? "All"
          : picked.length === 1
            ? (picked[0].length > 30 ? picked[0].slice(0, 29) + "…" : picked[0])
            : picked.length + " of " + names.length;
        btn.classList.toggle("on", picked.length > 0);
      };
      btn.addEventListener("click", function (e) {
        e.stopPropagation();
        if (openPanel && openPanel._btn === btn) { closePanel(); return; }
        closePanel();
        var p = document.createElement("div");
        p.className = "fpanel";
        p._btn = btn;
        p.addEventListener("click", function (ev) { ev.stopPropagation(); });
        var boxes = [];
        function update() {
          btn._sync();
          allCb.checked = Object.keys(st).length === 0;
          refilter();
        }
        var allLab = document.createElement("label");
        allLab.className = "fall";
        var allCb = document.createElement("input");
        allCb.type = "checkbox";
        allCb.checked = Object.keys(st).length === 0;
        allCb.addEventListener("change", function () {
          Object.keys(st).forEach(function (k) { delete st[k]; });
          boxes.forEach(function (b) { b.checked = false; });
          update();
        });
        allLab.appendChild(allCb);
        allLab.appendChild(document.createTextNode("All"));
        p.appendChild(allLab);
        names.forEach(function (v) {
          var lab = document.createElement("label");
          lab.title = v;
          var cb = document.createElement("input");
          cb.type = "checkbox";
          cb.checked = !!st[v];
          cb.addEventListener("change", function () {
            if (cb.checked) st[v] = 1; else delete st[v];
            update();
          });
          boxes.push(cb);
          lab.appendChild(cb);
          lab.appendChild(document.createTextNode(v));
          p.appendChild(lab);
        });
        var r = btn.getBoundingClientRect();
        p.style.left = Math.max(4, Math.min(r.left, window.innerWidth - 330)) + "px";
        p.style.top = (r.bottom + 2) + "px";
        document.body.appendChild(p);
        openPanel = p;
      });
      cell.appendChild(btn);
    });

    function posMap() {
      var m = {};
      Array.prototype.forEach.call(hrow.cells, function (c) { m[+c.dataset.col] = c.cellIndex; });
      return m;
    }
    function activePositions() {
      // Visual positions (cellIndex) of sorted or filtered columns, left
      // to right. Columns are never moved automatically -- the user
      // drags them where wanted; active ones just pin where they sit.
      var sortSet = {};
      sorts.forEach(function (s) { sortSet[s.col] = 1; });
      var pos = [];
      Array.prototype.forEach.call(hrow.cells, function (th, i) {
        var st = filterState[+th.dataset.col];
        var filtered = st && Object.keys(st).length > 0;
        if (sortSet[+th.dataset.col] || filtered) pos.push(i);
      });
      return pos;
    }
    function pin() {
      tbl.querySelectorAll(".pinned").forEach(function (c) {
        c.classList.remove("pinned"); c.style.left = "";
      });
      var left = 0;
      activePositions().forEach(function (i) {
        var w = hrow.cells[i].getBoundingClientRect().width;
        [hrow.cells[i], fr.cells[i]].concat(
          Array.prototype.map.call(tbl.tBodies[0].rows, function (r) { return r.cells[i]; })
        ).forEach(function (cell) {
          if (!cell) return;
          cell.classList.add("pinned");
          cell.style.left = left + "px";
        });
        left += w;
      });
    }
    function reorder() {
      // Apply the user-driven (drag) column order only; sorting and
      // filtering never move columns.
      [hrow, fr].concat(original).forEach(function (row) {
        baseOrder.forEach(function (c) {
          for (var k = 0; k < row.cells.length; k++) {
            if (+row.cells[k].dataset.col === c) { row.appendChild(row.cells[k]); break; }
          }
        });
      });
      pin();
    }
    function marks() {
      Array.prototype.forEach.call(hrow.cells, function (th) {
        var old = th.querySelector(".sortmark");
        if (old) old.remove();
        var idx = sorts.findIndex(function (s) { return s.col === +th.dataset.col; });
        if (idx >= 0) {
          var mark = document.createElement("span");
          mark.className = "sortmark";
          mark.textContent = " " + (sorts[idx].dir > 0 ? "▲" : "▼")
            + (sorts.length > 1 ? String(idx + 1) : "");
          th.appendChild(mark);
        }
      });
    }
    function passes(row) {
      if (frontierOnly) {
        for (var i = 0; i < hrow.cells.length; i++) {
          if (/^frontier/i.test(hrow.cells[i].textContent.trim())) {
            var t = row.cells[i].textContent.trim();
            if (t === "" || t === "—") return false;
            break;
          }
        }
      }
      for (var c = 0; c < fr.cells.length; c++) {
        var st = filterState[+fr.cells[c].dataset.col];
        if (st && Object.keys(st).length && row.cells[c] &&
            !st[row.cells[c].textContent.trim()]) return false;
      }
      return true;
    }
    function refilter() {
      var shown = 0;
      Array.prototype.forEach.call(tbl.tBodies[0].rows, function (r) {
        var ok = passes(r);
        r.style.display = ok ? "" : "none";
        if (ok) shown++;
      });
      count.textContent = shown + " of " + original.length + " rows";
      pin();
    }
    function apply() {
      var body = tbl.tBodies[0];
      var rows = Array.prototype.slice.call(body.rows);
      var m = posMap();
      rows.sort(function (a, b) {
        for (var i = 0; i < sorts.length; i++) {
          var c = m[sorts[i].col], d = sorts[i].dir;
          var ka = keyOf(a.cells[c]), kb = keyOf(b.cells[c]), r = 0;
          if (ka.n !== null && kb.n !== null) r = ka.n - kb.n;
          else r = ka.s < kb.s ? -1 : ka.s > kb.s ? 1 : 0;
          if (r) return r * d;
        }
        return 0;
      });
      rows.forEach(function (r) { body.appendChild(r); });
      marks(); refilter();
    }
    resetBtn.addEventListener("click", function () {
      sorts = [];
      closePanel();
      Object.keys(filterState).forEach(function (col) {
        var st = filterState[col];
        Object.keys(st).forEach(function (k) { delete st[k]; });
      });
      Array.prototype.forEach.call(fr.cells, function (c) {
        if (c.firstChild && c.firstChild._sync) c.firstChild._sync();
      });
      baseOrder = [];
      for (var i = 0; i < ncols; i++) baseOrder.push(i);
      var body = tbl.tBodies[0];
      original.forEach(function (r) { body.appendChild(r); });
      marks(); reorder(); refilter();
    });
    var fscan = -1;
    Array.prototype.forEach.call(hrow.cells, function (th, i) {
      if (fscan < 0 && /^frontier/i.test(th.textContent.trim())) fscan = i;
    });
    if (fscan >= 0) {
      frontierOnly = true;
      var frBtn = document.createElement("button");
      frBtn.textContent = "Frontier only";
      frBtn.setAttribute("aria-pressed", "true");
      frBtn.title = "Toggle between the frontier rows and all rows";
      frBtn.addEventListener("click", function () {
        frontierOnly = !frontierOnly;
        frBtn.setAttribute("aria-pressed", String(frontierOnly));
        frBtn.textContent = frontierOnly ? "Frontier only" : "All rows";
        refilter();
      });
      bar.insertBefore(frBtn, multiBtn);
    }
    bar.appendChild(count);
    Array.prototype.forEach.call(hrow.cells, function (th) {
      th.tabIndex = 0;
      th.draggable = true;
      th.title = "Click to sort; shift-click (or Multi-sort) adds this as a secondary key · drag to move this column";
      function onSort(ev) {
        var col = +th.dataset.col;
        var found = sorts.findIndex(function (s) { return s.col === col; });
        if ((ev.shiftKey || multi) && sorts.length) {
          if (found >= 0) sorts[found].dir *= -1;
          else sorts.push({ col: col, dir: 1 });
        } else {
          sorts = [{ col: col, dir: found === 0 ? -sorts[0].dir : 1 }];
        }
        apply();
      }
      th.addEventListener("click", onSort);
      th.addEventListener("keydown", function (ev) {
        if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); onSort(ev); }
      });
      th.addEventListener("dragstart", function (ev) {
        ev.dataTransfer.setData("text/plain", String(th.dataset.col));
        ev.dataTransfer.effectAllowed = "move";
      });
      th.addEventListener("dragover", function (ev) { ev.preventDefault(); });
      th.addEventListener("drop", function (ev) {
        ev.preventDefault();
        var from = parseInt(ev.dataTransfer.getData("text/plain"), 10);
        var to = +th.dataset.col;
        if (isNaN(from) || from === to) return;
        var fi = baseOrder.indexOf(from), ti = baseOrder.indexOf(to);
        if (fi < 0 || ti < 0) return;
        baseOrder.splice(fi, 1);
        baseOrder.splice(ti, 0, from);
        reorder(); refilter();
      });
    });
    refilter();
  });
})();
"""

INCLUDE_RE = re.compile(r"<!--include:([\w./-]+)-->")


def expand_includes(md_text, src_dir):
    """Replace <!--include:file.md--> markers with the named file's markdown,
    headings demoted one level (its H1 becomes an H2 of the including
    document) and its Numbers-by footer kept."""
    def sub(m):
        inc = (src_dir / m.group(1)).read_text(encoding="utf-8")
        out = []
        for line in inc.splitlines():
            if line.startswith("#"):
                line = "#" + line
            out.append(line)
        return "\n".join(out)
    return INCLUDE_RE.sub(sub, md_text)


def rewrite_links(body, src_dir):
    """Relative .md/.py links -> GitHub master URLs (path-resolved)."""
    def sub(m):
        href = m.group(1)
        if href.startswith(("http://", "https://", "#", "mailto:")):
            return m.group(0)
        target = (src_dir / href).resolve()
        try:
            rel = target.relative_to(ROOT)
        except ValueError:
            return m.group(0)
        if not LINK_BASE:
            return m.group(0)
        return f'href="{LINK_BASE}{rel.as_posix()}"' 
    return re.sub(r'href="([^"]+)"', sub, body)


def _wire_note_backlinks(body):
    """Point each note's ↩ link back at the header cell it defines.

    Header cells link their notes ([Label](#note-x "tip")); the note's ↩
    return link, written in the markdown as a jump to the table section,
    is rewritten to land on the exact header cell: the FIRST th linking
    #note-x gains id th-note-x, and the ↩ following <a id="note-x"> is
    retargeted to it."""
    seen = set()

    def th_id(m):
        note = m.group(2)
        if note in seen:
            return m.group(0)
        seen.add(note)
        return f'<th id="th-{note}">{m.group(1)}'

    body = re.sub(r'<th>(<a href="#(note-[\w-]+)")', th_id, body)

    def back(m):
        note = m.group(2)
        if note not in seen:
            return m.group(0)
        return f'{m.group(1)}<a href="#th-{note}">{m.group(3)}</a>'

    return re.sub(
        r'(<a id="(note-[\w-]+)"></a>.*?)<a href="[^"]*">(↩[^<]*)</a>',
        back, body, flags=re.S)


def render(src, out_path, title):
    """Render one markdown document to its sortable-table HTML product."""
    src, out_path = Path(src), Path(out_path)
    md_text = expand_includes(src.read_text(encoding="utf-8"), src.parent)
    body = markdown.markdown(md_text, extensions=["tables"])
    body = rewrite_links(body, src.parent)
    body = _wire_note_backlinks(body)
    # wide-table wrapper + prose-width class for the small tables
    body = body.replace("<table>", '<div class="tablewrap"><table>')
    body = body.replace("</table>", "</table></div>")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    body = body.replace(
        "</h1>", f'</h1>\n<div class="renderstamp">Built {stamp}</div>', 1)
    out = f"""<title>{title}</title>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet"
 href="https://fonts.googleapis.com/css2?family=Barlow+Semi+Condensed:wght@500;600&family=Source+Sans+3:ital,wght@0,400;0,600;1,400&display=swap">
<style>{CSS}</style>
<main>
{body}
</main>
<script>{JS}</script>
"""
    out_path.write_text(out, encoding="utf-8")
    n_tables = body.count("<table>")
    print(f"wrote {out_path.relative_to(ROOT) if out_path.is_absolute() else out_path}"
          f": {len(out):,} bytes, {n_tables} tables sortable")


def build_all():
    for rel, title in DOCS:
        src = ROOT / rel
        render(src, src.with_suffix(".html"), title)


if __name__ == "__main__":
    if "--list" in sys.argv:
        for rel, title in DOCS:
            print(f"  {rel}  ->  {Path(rel).with_suffix('.html')}  ({title})")
    elif len(sys.argv) > 1:
        src = Path(sys.argv[1]).resolve()
        rel = str(src.relative_to(ROOT))
        title = dict(DOCS).get(rel, src.stem.replace("_", " ").title())
        render(src, src.with_suffix(".html"), title)
    else:
        build_all()
