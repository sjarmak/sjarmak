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

# category -> [(owner, repo, what, result-when-shipped)]
CATEGORIES = [
    ("benchmarks + evals", [
        ("sjarmak", "codeprobe", "evals from merged PRs", "on pypi"),
        ("sourcegraph", "CodeScaleBench", "retrieval at repo scale", "275 tasks"),
        ("sjarmak", "EnterpriseBench", "enterprise-scale tasks", "112 tasks"),
        ("sjarmak", "migration-evals", "tiered-oracle migrations", "3 recipes"),
        ("sjarmak", "agent-diagnostics", "why agents fail", "12k trials"),
        ("sjarmak", "mg-ax", "AX of MCP tools", "shipped"),
    ]),
    ("gas city", [
        ("sjarmak", "gascity", "multi-agent orchestration", "upstream"),
        ("sjarmak", "gascity-packs", "opt-in agent packs", "upstream"),
        ("sjarmak", "gascity-dashboard", "operator dashboard", "upstream"),
    ]),
    ("research", [
        ("sjarmak", "agent-code-authorship", "who wrote the code", "72-89%"),
        ("sjarmak", "mem", "does memory help agents", "6.7k items"),
        ("sjarmak", "agent-oriented-architecture", "repo readiness for agents", "toolkit"),
        ("sjarmak", "GEO_public", "how LLMs see your product", "demo"),
    ]),
    ("agent tooling", [
        ("sjarmak", "livedocs", "docs-drift detection, MCP", "v0.2"),
        ("sjarmak", "tom-swe", "theory-of-mind for agents", "3-tier mem"),
        ("sjarmak", "coding-agent-workflows", "portable standards+skills", "rendered"),
        ("sjarmak", "brains", "agent warm-starts", "forkable"),
        ("sjarmak", "hvir", "view-first workbench", "shipped"),
        ("sjarmak", "code-intelligence-digest", "code-intel news digest", "weekly"),
    ]),
    ("scix + search", [
        ("sjarmak", "scix-agent", "32.4M-paper MCP server", "15 tools"),
        ("sjarmak", "nls-finetune-scix", "NL search for SciX", "shipped"),
    ]),
    ("play", [
        ("sjarmak", "website", "sjarmak.ai", "live"),
        ("sjarmak", "WheelOfFortune", "wheel practice app", "shipped"),
        ("sjarmak", "embertide", "browser deckbuilder", "playable"),
    ]),
]

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
TYPE_S = 0.031

# column content widths (chars); the full row is exactly 88 chars wide
COLS = {"task": 28, "what": 25, "util": 11, "status": 15}


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def repo_activity(owner, name):
    now = datetime.datetime.now(datetime.timezone.utc)
    meta = api(f"/repos/{owner}/{name}")
    pushed = datetime.datetime.fromisoformat(meta["pushed_at"].replace("Z", "+00:00"))
    since = (now - datetime.timedelta(days=UTIL_WINDOW_DAYS)).isoformat()
    commits = api(f"/repos/{owner}/{name}/commits?since={since}&per_page=100")
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


def cell(content, col):
    w = COLS[col]
    if len(content) > w:
        raise ValueError(f"cell overflows {col}({w}): {content!r} is {len(content)} chars")
    return content.ljust(w)


def build_svg(activity, total, archived):
    s = Svg()
    n_tasks = sum(len(rows) for _, rows in CATEGORIES)

    cmd1 = "codeprobe run --suite stephanie-jarmak --oracle tiered"
    s.line([("green", "$ "), ("bright", cmd1)], cls="type", dur=len(cmd1) * TYPE_S, nchars=len(cmd1) + 2)
    s.line([("muted", f"resolving suite ... {n_tasks} tasks in {len(CATEGORIES)} categories, "
                      f"{total} public repos")])
    s.skip()

    border = "+" + "+".join("-" * (w + 1) for w in COLS.values()) + "+"
    blank_cells = ("| " + cell("", "what") + "| " + cell("", "util") + "| "
                   + cell("", "status") + "|")
    s.line([("dim", border)], gap=0.5)
    s.line([("muted", "| " + cell("TASK", "task") + "| " + cell("WHAT", "what")
                      + "| " + cell("UTIL/14d", "util") + "| " + cell("STATUS", "status") + "|")], gap=0.5)
    shipped = 0
    for label, rows in CATEGORIES:
        s.line([("dim", border)], gap=0.4)
        s.line([("dim", "| "), ("cyan", cell(label, "task")), ("dim", blank_cells)], gap=0.5)
        for owner, name, what, result in rows:
            days_idle, commits = activity[(owner, name)]
            running = days_idle <= RUNNING_DAYS
            if not running:
                shipped += 1
            cells_n = min(8, commits) if commits else (1 if running else 0)
            bar = "#" * cells_n + "." * (8 - cells_n)
            status = "RUNNING" if running else f"PASS {result}"
            task = name if owner == OWNER else f"{name} ({owner})"
            s.line([
                ("dim", "| "), ("link", cell(task, "task")),
                ("dim", "| "), ("", cell(what, "what")),
                ("dim", "| "), ("green" if cells_n else "dim", bar), ("", " " * (COLS["util"] - 8)),
                ("dim", "| "), ("amber" if running else "green", cell(status, "status")), ("dim", "|"),
            ], gap=0.5)
    s.line([("dim", border)], gap=0.5)
    s.line([("green", f"suite result: {n_tasks}/{n_tasks} oracles green "
                      f"({n_tasks - shipped} running, {shipped} shipped)")])
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
        f"<text x='{PAD}' y='{s.y}' xml:space='preserve'><tspan class='green'>$ </tspan></text>")
    s.parts.append(
        f"<rect x='{PAD + 15}' y='{s.y - FS + 1}' width='7' height='{FS + 2}' class='cursor' "
        f"style='--t:{s.t:.2f}s'/>")
    s.y += LH

    H = s.y + 16
    head = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}' "
        f"font-family=\"'SF Mono', SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace\" "
        f"role='img' aria-label='Terminal session: codeprobe runs an eval suite named "
        f"stephanie-jarmak over my projects grouped by category, then git log --graph draws "
        f"the career: measurement on main, gas-city as an active branch'>"
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
    activity = {}
    for _, rows in CATEGORIES:
        for owner, name, _, _ in rows:
            activity[(owner, name)] = repo_activity(owner, name)
    total, archived = account_counts()
    svg = build_svg(activity, total, archived)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "readout.svg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(svg)
    n = sum(len(r) for _, r in CATEGORIES)
    print(f"wrote {out}: {n} tasks in {len(CATEGORIES)} categories, {total} public repos")


if __name__ == "__main__":
    main()
