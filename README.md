# PREVIEW — composed profile README concept (top 5 brainstorm picks layered)

*This is a mockup demonstrating the shortlisted devices with your real content. Numbers and links are real; copy is draft.*

---

# Stephanie Jarmak

I build benchmarks and tooling for AI coding agents[^1], maintain the Gas City multi-agent orchestration ecosystem[^2], and hold that a claim about agents is worth exactly the evidence behind it. Previously Sourcegraph[^3]; before that, planetary science and NASA ADS search[^4].

[^1]: Six public benchmark suites; see the report below. Flagship: [codeprobe](https://github.com/sjarmak/codeprobe), on PyPI.
[^2]: [gastownhall](https://github.com/gastownhall): gascity, beads, dashboard, packs. Contributions stage in my forks before landing upstream.
[^3]: Sales engineering and the CodeContextBench family, now archived as work history.
[^4]: Europa Clipper UVS observation planning; the thread continues in [scix-agent](https://github.com/sjarmak/scix-agent) (32.4M papers, 299M citation edges, 15 MCP tools).

```mermaid
gitGraph
  commit id: "planetary science"
  commit id: "Europa Clipper UVS"
  branch ads-scix
  commit id: "NASA ADS search"
  commit id: "SciX relevance"
  checkout main
  merge ads-scix id: "search meets software"
  commit id: "Sourcegraph SE"
  commit id: "CodeContextBench"
  branch gas-city
  commit id: "gascity + beads"
  commit id: "maintainer" tag: "HEAD"
```

## Results: benchmarks & evaluation

| task | what it measures | result | evidence |
|---|---|---|---|
| codeprobe | your whole agent setup, against your own merged PRs | on PyPI | [repo](https://github.com/sjarmak/codeprobe) |
| EnterpriseBench | cross-repo enterprise tasks | 112 tasks, 10 types | [repo](https://github.com/sjarmak/EnterpriseBench) |
| migration-evals | batch-change diffs through tiered oracles | 3 recipes shipped | [repo](https://github.com/sjarmak/migration-evals) |
| agent-diagnostics | why agents fail, taxonomically | 11,995 labeled trials | [repo](https://github.com/sjarmak/agent-diagnostics) |

> [!IMPORTANT]
> Finding: across 151 popular repos, 72-89% of surviving 2024+ lines are agent-written. Commit trailers only admit to 14.5%.

```mermaid
xychart-beta
  title "Who wrote 2024+ surviving lines?"
  x-axis ["visible in trailers", "style estimate (low)", "style estimate (high)"]
  y-axis "% of lines" 0 --> 100
  bar [14.5, 72, 89]
```

## Try the work (one line each)

```bash
pipx run codeprobe --help          # PR-derived agent evals
brew install sjarmak/tap/livedocs  # docs-drift detection over MCP (next release)
npx tom-swe                        # theory-of-mind memory for Claude Code
```

## Project lifespans

Archived means finished, not abandoned. The record:

```mermaid
gantt
  dateFormat YYYY-MM
  section Astronomy
    Europa Clipper UVS tooling :done, 2023-01, 2023-10
  section Sourcegraph
    CodeContextBench family    :done, 2025-11, 2026-03
  section Current
    codeprobe                  :active, 2026-03, 2026-08
    Gas City maintainership    :active, 2026-04, 2026-08
```

---
*Preview ends. Full brainstorm: 30 ideas, 10 prior-art exclusion zones, ratings in `.brainstorm/profile-readme.md`.*
