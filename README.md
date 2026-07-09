# narrate

**One-command release notes from git history.**

```
pip install narrate
narrate ohmyzsh/ohmyzsh --from v1.0 --to v2.0
```

`narrate` fetches your commits and issues from GitHub, analyzes the changes, and generates structured markdown release notes — with or without AI.

## Quick start

```bash
# Template mode (no API key needed)
narrate ohmyzsh/ohmyzsh --from HEAD~10 --to HEAD

# Pick a template style
narrate vercel/next.js --from v14.0 --to v15.0 --template technical

# AI-powered mode (richer storytelling)
export DEEPSEEK_API_KEY=sk-xxx
narrate facebook/react --from HEAD~20 --to HEAD --template community
```

## Templates

| Style | Audience | Best for |
|-------|----------|----------|
| `community` | Contributors & users | Open-source projects where every contributor should feel seen |
| `technical` | Developers | Libraries, SDKs, infrastructure — precise, migration-aware |
| `marketing` | General audience | SaaS products, newsletters, social media announcements |

## Output

```markdown
# ohmyzsh master

**4** commits · **2** issues resolved · **4** contributors
2026-07-05 to 2026-07-07 · 6 files · +55 -3

### New: complete route rule actions
[#13848](https://github.com/ohmyzsh/ohmyzsh/pull/13848) by @ishaanlabs-gg

## What's Next

- **[High Priority]** XDG Base Directory support (#9543) — 39 reactions
- **[In Discussion]** Auto-update custom plugins (#9512) — 25 reactions
```

All intermediate JSON artifacts are written to `references/` for inspection and debugging.

## Installation

```bash
pip install narrate
```

Python 3.10+ required. No external dependencies (stdlib only).

Or run directly from source:

```bash
git clone https://github.com/1knownothing/narrate.git
cd narrate
python narrate --help
```

## Options

```
usage: narrate [-h] --from FROM_REF --to TO_REF [--template {community,technical,marketing}]
               [--output OUTPUT] [--skip-quality] [--print]

positional arguments:
  repo                  owner/name (e.g., ohmyzsh/ohmyzsh)

options:
  --from FROM_REF       base ref (HEAD~4, v1.0, master@{7day})
  --to TO_REF           target ref (HEAD, master, v2.0)
  --template TEMPLATE   output style: community (default), technical, marketing
  --output, -o          output directory (default: references/)
  --skip-quality        skip quality validation
  --print               print markdown to stdout
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` / `GH_TOKEN` | Higher API rate limit (5,000 req/h vs 60) |
| `DEEPSEEK_API_KEY` | Enables AI-powered writer for richer descriptions |

## How it works

```
PARSE_INPUT  →  COLLECT_DATA  →  ANALYZE  →  WRITER  →  FORMATTER  →  QUALITY_CHECK
  (refs)       (GitHub API)    (classify)   (template/AI)  (markdown)   (validate)
```

Each step writes its output to the references directory, so you can inspect or resume from any stage.

## Roadmap

- [ ] GitHub Action — auto-generate release notes on tag push
- [ ] PyPI release
- [ ] Write-back to GitHub Release body
- [ ] Multi-repo support

## Why narrate?

Good release notes build community. They turn a list of commits into a story that makes users feel informed and contributors feel appreciated. `narrate` handles the mechanical part — data fetching, categorization, formatting — so you can focus on the part that matters: understanding what your users need to know.

## License

MIT
