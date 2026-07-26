#!/usr/bin/env python3
"""Render assets/readout.svg: this profile as a codeprobe eval-harness run.

Task statuses and utilization bars come from real GitHub activity. Run with
GITHUB_TOKEN set (the refresh workflow provides one; locally use `gh auth token`).
"""
import datetime
import json
import os
import urllib.request

OWNER = "sjarmak"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

# (repo, oracle description, static result shown when the task is not RUNNING)
TASKS = [
    ("gascity", "multi-agent orchestration (maintainer)", "upstream"),
    ("codeprobe", "evals from your own merged PRs", "on pypi"),
    ("agent-code-authorship", "who really wrote the code", "72-89%"),
    ("mem", "does memory help agents", "6,691 items"),
    ("scix-agent", "32.4M-paper MCP server", "15 tools"),
    ("livedocs", "docs-drift detection over MCP", "v0.2"),
    ("EnterpriseBench", "112 enterprise-scale tasks", "112 tasks"),
]

RUNNING_DAYS = 7      # pushed within N days -> RUNNING
UTIL_WINDOW_DAYS = 14 # commit count window for the utilization bar


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r), r.headers


def repo_activity(name):
    now = datetime.datetime.now(datetime.timezone.utc)
    meta, _ = api(f"/repos/{OWNER}/{name}")
    pushed = datetime.datetime.fromisoformat(meta["pushed_at"].replace("Z", "+00:00"))
    since = (now - datetime.timedelta(days=UTIL_WINDOW_DAYS)).isoformat()
    commits, headers = api(f"/repos/{OWNER}/{name}/commits?since={since}&per_page=100")
    n = len(commits)
    return (now - pushed).days, n


def account_counts():
    # public-only so the numbers are identical under any token (Actions GITHUB_TOKEN or a PAT)
    q = 'query($c:String){user(login:"' + OWNER + '"){repositories(first:100,after:$c,ownerAffiliations:OWNER,privacy:PUBLIC){pageInfo{hasNextPage endCursor}nodes{isArchived}}}}'
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


ESC = {"&": "&amp;", "<": "&lt;", ">": "&gt;"}


def esc(s):
    return "".join(ESC.get(c, c) for c in s)


def build_svg(rows, total, archived):
    W, LH, FS = 760, 22, 13
    PAD, CHROME = 24, 38
    n_lines = 6 + len(rows) + 4
    H = CHROME + PAD + n_lines * LH + PAD
    FG, DIM, GREEN, AMBER, BLUE = "#c9d1d9", "#8b949e", "#3fb950", "#d29922", "#58a6ff"
    MONO = "font-family='SFMono-Regular,Consolas,Liberation Mono,Menlo,monospace'"

    def text(x, y, s, fill=FG, weight=""):
        w = " font-weight='600'" if weight else ""
        return f"<text x='{x}' y='{y}' font-size='{FS}' fill='{fill}' {MONO}{w}>{esc(s)}</text>"

    y = CHROME + PAD + FS
    parts = [
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{W}' height='{H}' viewBox='0 0 {W} {H}'>",
        f"<rect width='{W}' height='{H}' rx='10' fill='#161b22'/>",
        f"<rect width='{W}' height='{CHROME}' rx='10' fill='#21262d'/>",
        f"<rect y='{CHROME - 10}' width='{W}' height='10' fill='#21262d'/>",
        "<circle cx='22' cy='19' r='6' fill='#ff5f56'/><circle cx='42' cy='19' r='6' fill='#ffbd2e'/><circle cx='62' cy='19' r='6' fill='#27c93f'/>",
        f"<text x='{W // 2}' y='24' font-size='12' fill='{DIM}' {MONO} text-anchor='middle'>stephanie@jarmak: ~/benchmarks</text>",
    ]
    parts.append(text(PAD, y, "$", GREEN, "b"))
    parts.append(text(PAD + 16, y, "codeprobe run --suite stephanie-jarmak --oracle tiered"))
    y += LH
    parts.append(text(PAD, y, f"resolving suite ... {total} repos scanned, {total - archived} active, {archived} archived (finished, not abandoned)", DIM))
    y += LH * 2
    xs = {"task": PAD, "oracle": 236, "util": 508, "status": 628}
    parts.append(text(xs["task"], y, "TASK", DIM))
    parts.append(text(xs["oracle"], y, "ORACLE", DIM))
    parts.append(text(xs["util"], y, "UTIL/14d", DIM))
    parts.append(text(xs["status"], y, "STATUS", DIM))
    y += LH
    passed = 0
    for name, oracle, result, days_idle, commits in rows:
        running = days_idle <= RUNNING_DAYS
        if not running:
            passed += 1
        parts.append(text(xs["task"], y, name, BLUE))
        parts.append(text(xs["oracle"], y, oracle))
        cells = min(8, commits) if commits else (1 if running else 0)
        for i in range(8):
            fill = GREEN if i < cells else "#30363d"
            parts.append(f"<rect x='{xs['util'] + i * 12}' y='{y - FS + 2}' width='9' height='{FS}' rx='2' fill='{fill}'/>")
        status = ("RUNNING", AMBER) if running else (f"PASS {result}", GREEN)
        parts.append(text(xs["status"], y, status[0], status[1], "b"))
        y += LH
    y += LH
    parts.append(text(PAD, y, f"suite result: {len(rows)}/{len(rows)} oracles green ({len(rows) - passed} running, {passed} shipped)", GREEN, "b"))
    y += LH
    parts.append(text(PAD, y, "history: sourcegraph (SE, benchmarks) <- nasa ads/scix (search) <- planetary science (europa uvs)", DIM))
    y += LH
    parts.append(text(PAD, y, "auto-refreshed from real commit activity - sjarmak.ai", DIM))
    parts.append("</svg>")
    return "\n".join(parts)


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
    print(f"wrote {out}: {total} repos, {archived} archived, {len(rows)} tasks")


if __name__ == "__main__":
    main()
