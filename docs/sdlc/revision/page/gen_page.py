#!/usr/bin/env python3
"""Render docs/sdlc/revision/2026-09-10-step-review.md as a filterable HTML page."""
import html, re, json

import os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "2026-09-10-step-review.md")
OUT = os.environ.get("STEP_REVIEW_OUT", "/tmp/step-review.html")  # publish this file as the artifact
REPO = "https://github.com/luissiviero/lifecycle-axis-/blob/claude/project-feasibility-discussion-kx5f0g/"

text = open(SRC, encoding="utf-8").read().split("---", 2)[2]

def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", lambda m: "<code>%s</code>" % m.group(1), s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![\w*])\*(?!\*)([^*]+?)\*(?!\*)", r"<em>\1</em>", s)
    def link(m):
        href = m.group(2)
        if not href.startswith(("http", "#")):
            href = REPO + "docs/sdlc/revision/" + href
        return '<a href="%s">%s</a>' % (href, m.group(1))
    return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", link, s)

def verdict_key(cell):
    c = cell.strip().lower()
    if c.startswith("merge"): return "merge"
    if c.startswith("keep (note)"): return "note"
    for v in ("keep", "change", "fix", "build", "drop"):
        if c.startswith(v): return v
    return "other"

def split_row(line):
    line = line.strip()
    if line.startswith("|"): line = line[1:]
    if line.endswith("|"): line = line[:-1]
    cells, cur, i = [], "", 0
    while i < len(line):
        ch = line[i]
        if ch == "\\" and i + 1 < len(line) and line[i+1] == "|":
            cur += "|"; i += 2; continue
        if ch == "|":
            cells.append(cur); cur = ""; i += 1; continue
        cur += ch; i += 1
    cells.append(cur)
    return [c.strip() for c in cells]

def slug(t):
    return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

out, counts = [], {}
lines = text.splitlines()
i, lens, in_list, in_details = 0, None, None, False

def close_list():
    global in_list
    if in_list:
        out.append("</%s>" % in_list); in_list = None

while i < len(lines):
    ln = lines[i]
    if ln.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[-| ]+\|?$", lines[i+1].strip()):
        close_list()
        header = split_row(ln); rows = []; i += 2
        while i < len(lines) and lines[i].startswith("|"):
            rows.append(split_row(lines[i])); i += 1
        is_steps = header[0] == "#" and "Change" in header
        is_new = header[0] == "#" and header[1].startswith("New step")
        cls = "steps" if is_steps else ("newsteps" if is_new else "plain")
        out.append('<div class="tablewrap"><table class="%s"><thead><tr>%s</tr></thead><tbody>' % (
            cls, "".join("<th>%s</th>" % inline(h) for h in header)))
        for r in rows:
            r += [""] * (len(header) - len(r))
            if is_steps:
                vk = verdict_key(r[3]); counts[vk] = counts.get(vk, 0) + 1
                cells = []
                for j, c in enumerate(r):
                    if j == 0: cells.append('<td class="num">%s</td>' % inline(c))
                    elif j == 3: cells.append('<td><span class="pill pill-%s">%s</span></td>' % (vk, inline(c)))
                    else: cells.append("<td>%s</td>" % inline(c))
                out.append('<tr data-verdict="%s" data-lens="%s">%s</tr>' % (vk, lens, "".join(cells)))
            elif is_new:
                cells = ['<td class="num">%s</td>' % inline(r[0])] + ["<td>%s</td>" % inline(c) for c in r[1:]]
                out.append('<tr data-verdict="new" data-lens="new">%s</tr>' % "".join(cells))
            else:
                out.append("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r))
        out.append("</tbody></table></div>")
        continue
    m = re.match(r"^(#{1,3}) (.*)", ln)
    if m:
        close_list()
        level, title = len(m.group(1)), m.group(2)
        if level == 1:
            i += 1; continue
        if level == 2 and in_details:
            out.append("</details>"); in_details = False
        if title.startswith("Lens A"): lens = "A"
        elif title.startswith("Lens B"): lens = "B"
        elif title.startswith("Maintain"): lens = "M"
        if level == 2 and title.startswith("Appendix"):
            out.append('<details class="appendix" id="%s"><summary><h2>%s</h2></summary>' % (slug(title), inline(title)))
            in_details = True
        else:
            out.append('<h%d id="%s">%s</h%d>' % (level, slug(title), inline(title), level))
        i += 1; continue
    m = re.match(r"^- (.*)", ln)
    if m:
        if in_list != "ul": close_list(); out.append("<ul>"); in_list = "ul"
        item = m.group(1)
        while i + 1 < len(lines) and lines[i+1].startswith("  ") and not lines[i+1].lstrip().startswith("- "):
            i += 1; item += " " + lines[i].strip()
        out.append("<li>%s</li>" % inline(item)); i += 1; continue
    m = re.match(r"^(\d+)\. (.*)", ln)
    if m:
        if in_list != "ol": close_list(); out.append("<ol>"); in_list = "ol"
        item = m.group(2)
        while i + 1 < len(lines) and lines[i+1].startswith("   "):
            i += 1; item += " " + lines[i].strip()
        out.append("<li>%s</li>" % inline(item)); i += 1; continue
    if ln.strip() == "":
        close_list(); i += 1; continue
    para = [ln]
    while i + 1 < len(lines) and lines[i+1].strip() and not lines[i+1].startswith(("|", "#", "- ")) and not re.match(r"^\d+\. ", lines[i+1]):
        i += 1; para.append(lines[i])
    close_list()
    out.append("<p>%s</p>" % inline(" ".join(p.strip() for p in para)))
    i += 1
close_list()
if in_details: out.append("</details>")
body = "\n".join(out)

# Wrap the five findings and the stance list so the CSS can treat them as objects.
body = body.replace('<p><strong>Five findings that change the picture</strong>, before the rows:</p>\n<ol>',
                    '<section class="findings" id="findings"><h3>Five findings that change the picture</h3>\n<ol>', 1)
body = body.replace('</ol>\n<h2 id="1-existing-steps">', '</ol></section>\n<h2 id="1-existing-steps">', 1)
body = body.replace('<p><strong>The design stance behind the assessments.</strong>',
                    '<div class="stances" id="stances"><p><strong>The design stance behind the assessments.</strong>', 1)
body = body.replace('</ul>\n<section class="findings"', '</ul></div>\n<section class="findings"', 1)

page = open(os.path.join(HERE, "shell.html"), encoding="utf-8").read()
page = page.replace("{{BODY}}", body).replace("{{COUNTS}}", json.dumps(counts)).replace("{{TOTAL}}", str(sum(counts.values())))
open(OUT, "w", encoding="utf-8").write(page)
print(OUT, len(page), counts)
