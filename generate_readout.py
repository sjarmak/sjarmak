#!/usr/bin/env python3
"""Render assets/readout.svg: an animated terminal session where my own eval
harness runs a suite named after me, followed by a git log --graph of the career.

Task statuses and utilization bars come from real GitHub activity. Run with
GITHUB_TOKEN set (the refresh workflow provides one; locally use `gh auth token`).
Styling and animation technique mirror jarmak-personal's readout SVG.
"""
import datetime
import json
import os
import urllib.request

OWNER = "sjarmak"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# (repo, oracle description, result shown when the task is shipped rather than running)
TASKS = [
    ("gascity", "orchestration SDK I maintain", "upstream"),
    ("codeprobe", "evals from your own merged PRs", "on pypi"),
    ("agent-code-authorship", "who really wrote the code", "72-89%"),
    ("mem", "does memory help agents", "6.7k items"),
    ("agent-diagnostics", "why agents fail, taxonomically", "12k trials"),
    ("scix-agent", "32.4M-paper MCP server", "15 tools"),
    ("livedocs", "docs-drift detection over MCP", "v0.2"),
    ("agent-workflows", "parallel agent workflows", "21 skills"),
]

# column content widths (chars); the full row is exactly 88 chars wide
COLS = {"task": 22, "oracle": 31, "util": 11, "status": 15}

GRAPH = [
    ("* ", "f9c1e2a", " (HEAD -> main) ", "agent evals + research: codeprobe, EnterpriseBench, mem"),
    ("| *", "b7a44d3", " (gas-city) ", "maintainer: gascity, beads, dashboard, packs"),
    ("|/", "", "", ""),
    ("* ", "8d05c1f", " ", "CodeScaleBench: 275 tasks, 20 suites"),
    ("* ", "3e6a9b2", " ", "sourcegraph: sales engineering, agent demos"),
    ("*  ", "c2d81f5", " ", "merge ads-scix: search meets software"),
    ("|\\", "", "", ""),
    ("| *", "5a9e0c4", " (ads-scix) ", "NASA ADS/SciX: 32.4M-paper search"),
    ("|/", "", "", ""),
    ("* ", "1f4b7a9", " ", "planetary science: Europa Clipper UVS"),
]

RUNNING_DAYS = 7
UTIL_WINDOW_DAYS = 14
W, LH, FS, PAD = 687, 17, 12, 22
CHROME = 34
TYPE_S = 0.031  # seconds per typed character


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def repo_activity(name):
    now = datetime.datetime.now(datetime.timezone.utc)
    meta = api(f"/repos/{OWNER}/{name}")
    pushed = datetime.datetime.fromisoformat(meta["pushed_at"].replace("Z", "+00:00"))
    since = (now - datetime.timedelta(days=UTIL_WINDOW_DAYS)).isoformat()
    commits = api(f"/repos/{OWNER}/{name}/commits?since={since}&per_page=100")
    return (now - pushed).days, len(commits)


def account_counts():
    # public-only so the numbers are identical under any token (Actions GITHUB_TOKEN or a PAT)
    q = ('query($c:String){user(login:"' + OWNER + '"){repositories(first:100,after:$c,'
         'ownerAffiliations:OWNER,privacy:PUBLIC){pageInfo{hasNextPage endCursor}nodes{isArchived}}}}')
    total = archived = 0
    cursor = None
    while True:
        body = json.dumps({"query": q, "variables": {"c": cursor}}).encode()
        req = urllib.request.Request("https://api.github.com/graphql", data=body)
        req.add_header("Authorization", f"Bearer {TOKEN}")
        with urllib.request.urlopen(req, timeout=30) as r:
            page = json.load(r)["data"]["user"]["repositories"]
        total += len(page["nodes"])
        archived += sum(1 for n in page["nodes"] if n["isArchived"])
        if not page["pageInfo"]["hasNextPage"]:
            break
        cursor = page["pageInfo"]["endCursor"]
    return total, archived


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Svg:
    def __init__(self):
        self.parts = []
        self.y = CHROME + 28
        self.t = 0.4

    def line(self, tspans, cls="fade", dur=None, nchars=None, gap=1.0):
        style = f"--t:{self.t:.2f}s"
        if cls == "type":
            style += f";--d:{dur:.2f}s;--n:{nchars}"
        body = "".join(f"<tspan class='{c}'>{esc(s)}</tspan>" if c else f"<tspan>{esc(s)}</tspan>"
                       for c, s in tspans)
        self.parts.append(
            f"<text x='{PAD}' y='{self.y}' class='{cls}' style='{style}' xml:space='preserve'>{body}</text>")
        self.y += LH
        self.t += (dur + 0.05) if cls == "type" else 0.09 * gap

    def skip(self, n=1):
        self.y += LH * n


def build_svg(rows, total, archived):
    s = Svg()

    cmd1 = "codeprobe run --suite stephanie-jarmak --oracle tiered"
    s.line([("green", "$ "), ("bright", cmd1)], cls="type", dur=len(cmd1) * TYPE_S, nchars=len(cmd1) + 2)
    s.line([("muted", f"resolving suite ... {total} public repos, {total - archived} active")])
    s.skip()

    def cell(content, col):
        w = COLS[col]
        if len(content) > w:
            raise ValueError(f"cell overflows {col}({w}): {content!r} is {len(content)} chars")
        return content.ljust(w)

    border = "+" + "+".join("-" * (w + 1) for w in COLS.values()) + "+"
    s.line([("dim", border)], gap=0.5)
    s.line([("muted", "| " + cell("TASK", "task") + "| " + cell("ORACLE", "oracle")
                      + "| " + cell("UTIL/14d", "util") + "| " + cell("STATUS", "status") + "|")], gap=0.5)
    s.line([("dim", border)], gap=0.5)
    shipped = 0
    for name, oracle, result, days_idle, commits in rows:
        running = days_idle <= RUNNING_DAYS
        if not running:
            shipped += 1
        cells = min(8, commits) if commits else (1 if running else 0)
        bar = "#" * cells + "." * (8 - cells)
        status = "RUNNING" if running else f"PASS {result}"
        s.line([
            ("dim", "| "), ("link", cell(name, "task")),
            ("dim", "| "), ("", cell(oracle, "oracle")),
            ("dim", "| "), ("green" if cells else "dim", bar), ("", " " * (COLS["util"] - 8)),
            ("dim", "| "), ("amber" if running else "green", cell(status, "status")), ("dim", "|"),
        ], gap=0.7)
    s.line([("dim", border)], gap=0.5)
    s.line([("green", f"suite result: {len(rows)}/{len(rows)} oracles green "
                      f"({len(rows) - shipped} running, {shipped} shipped)")])
    s.skip()

    s.t += 0.4
    cmd2 = "git log --graph --oneline career"
    s.line([("green", "$ "), ("bright", cmd2)], cls="type", dur=len(cmd2) * TYPE_S, nchars=len(cmd2) + 2)
    for glyphs, sha, ref, msg in GRAPH:
        spans = [("dim", glyphs + " ")]
        if sha:
            spans.append(("orange", sha))
        if ref:
            spans.append(("cyan", ref))
        if msg:
            spans.append(("", msg))
        s.line(spans, gap=0.8)
    s.skip()

    s.line([("muted", "readout auto-refreshed from real commit activity")])
    s.parts.append(
        f"<text x='{PAD}' y='{s.y}' xml:space='preserve'>"
        f"<tspan class='green'>$ </tspan></text>")
    s.parts.append(
        f"<rect x='{PAD + 15}' y='{s.y - FS + 1}' width='7' height='{FS + 2}' class='cursor' "
        f"style='--t:{s.t:.2f}s'/>")
    s.y += LH

    H = s.y + 16
    head = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}' "
        f"font-family=\"'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace\" "
        f"role='img' aria-label='Terminal session: codeprobe runs an eval suite named "
        f"stephanie-jarmak over my active projects, then git log --graph draws the career: "
        f"measurement on main, gas-city as an active branch'>"
        "<style>"
        f"text {{ font-size: {FS}px; fill: #d0d3da; }}"
        ".dim { fill: #5b5f6b; } .muted { fill: #9aa0ac; } .bright { fill: #eceef2; }"
        ".orange { fill: #d97757; } .green { fill: #3fb950; } .amber { fill: #d29922; }"
        ".link { fill: #79c0ff; } .cyan { fill: #56d4dd; }"
        ".fade { opacity: 0; animation: appear 0.01s linear var(--t) forwards; }"
        ".type { clip-path: inset(0 100% 0 0); animation: typing var(--d) steps(var(--n)) var(--t) forwards; }"
        ".cursor { fill: #3fb950; opacity: 0; animation: blink 1.1s step-end var(--t) infinite; }"
        "@keyframes appear { to { opacity: 1; } }"
        "@keyframes typing { to { clip-path: inset(0 -2% 0 0); } }"
        "@keyframes blink { 0% { opacity: 1; } 50% { opacity: 0; } }"
        "@media (prefers-reduced-motion: reduce) {"
        " .fade, .type, .cursor { animation: none; opacity: 1; clip-path: none; } }"
        "</style>"
        f"<rect width='{W}' height='{H}' rx='10' fill='#16171d' stroke='#2e303a'/>"
        f"<path d='M0 10 a10 10 0 0 1 10 -10 h{W - 20} a10 10 0 0 1 10 10 v24 h-{W} z' fill='#1f2027'/>"
        "<circle cx='22' cy='17' r='6' fill='#ff5f57'/>"
        "<circle cx='42' cy='17' r='6' fill='#febc2e'/>"
        "<circle cx='62' cy='17' r='6' fill='#28c840'/>"
        f"<text x='{W // 2}' y='21' text-anchor='middle' fill='#9aa0ac' font-size='11'>"
        "stephanie@jarmak: ~/projects</text>"
    )
    return head + "".join(s.parts) + "</svg>"


def main():
    rows = []
    for name, oracle, result in TASKS:
        days_idle, commits = repo_activity(name)
        rows.append((name, oracle, result, days_idle, commits))
    total, archived = account_counts()
    svg = build_svg(rows, total, archived)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "readout.svg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(svg)
    print(f"wrote {out}: {total} public repos, {archived} archived, {len(rows)} tasks")


if __name__ == "__main__":
    main()
