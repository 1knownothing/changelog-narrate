# narrate

**One-command release notes from git history.**

```
pip install changelog-narrate
narrate ohmyzsh/ohmyzsh --from v1.0 --to v2.0
```

`narrate` fetches your commits and issues from GitHub, analyzes the changes, and generates structured markdown release notes — with or without AI. Stdlib only, zero external dependencies.

## Quick start

```bash
# Template mode — no API key needed
narrate ohmyzsh/ohmyzsh --from HEAD~10 --to HEAD

# Pick a template style
narrate vercel/next.js --from v14.0 --to v15.0 --template technical

# AI-powered mode — richer storytelling
export DEEPSEEK_API_KEY=sk-xxx
narrate facebook/react --from HEAD~20 --to HEAD --template community

# Use with your own model (OpenAI, Ollama, any OpenAI-compatible API)
export AI_API_KEY=sk-xxx
narrate facebook/react --from HEAD~10 --to HEAD \
  --ai-model gpt-4o \
  --ai-endpoint https://api.openai.com/v1/chat/completions

# Local AI with Ollama (no API key needed!)
narrate facebook/react --from HEAD~10 --to HEAD \
  --ai-model llama3 \
  --ai-endpoint http://localhost:11434/v1/chat/completions

# Feed raw data to your coding tool's AI (opencode, Cursor, Claude Code, etc.)
narrate ohmyzsh/ohmyzsh --from HEAD~4 --to HEAD --json-only
```

## Three ways to use `narrate`

| Mode | Needs API key? | How it works |
|------|---------------|--------------|
| **Template** (default) | None | Rule-based categorization + markdown formatting |
| **AI-powered** (terminal) | `AI_API_KEY` or `DEEPSEEK_API_KEY` | Send data to any OpenAI-compatible model for richer writing |
| **Coding tool** (--json-only) | None | Output raw JSON → your tool's AI (opencode, Cursor, Claude Code, etc.) writes the changelog |

### Template mode (zero config)

Works out of the box. Categorizes commits (features, fixes, breaking changes), highlights community issues, and generates a roadmap from open issues.

```bash
narrate ohmyzsh/ohmyzsh --from HEAD~4 --to HEAD
narrate facebook/react --from v18.0 --to v19.0 --template technical
```

### AI-powered mode (bring your own model)

Narrate supports any OpenAI-compatible chat API. Set `AI_API_KEY` (or the legacy `DEEPSEEK_API_KEY`), optionally configure model and endpoint.

```bash
# DeepSeek (default)
export DEEPSEEK_API_KEY=sk-xxx
narrate facebook/react --from HEAD~10 --to HEAD

# OpenAI
export AI_API_KEY=sk-xxx
narrate facebook/react --from HEAD~10 --to HEAD \
  --ai-model gpt-4o \
  --ai-endpoint https://api.openai.com/v1/chat/completions

# Local Ollama (run locally, no internet, no API key)
# First: ollama pull llama3
# Then:
export AI_API_KEY=ollama  # Ollama ignores the key, value can be anything
narrate facebook/react --from HEAD~5 --to HEAD \
  --ai-model llama3 \
  --ai-endpoint http://localhost:11434/v1/chat/completions

# Any OpenAI-compatible provider
export AI_API_KEY=sk-xxx
narrate owner/repo --from HEAD~10 --to HEAD \
  --ai-model claude-sonnet-4 \
  --ai-endpoint https://api.anthropic.com/v1/chat/completions  # if Anthropic supports OpenAI format
```

### Coding tool mode (use your tool's AI)

No API key needed. Narrate acts as a pure data collector — fetches commits/issues from GitHub, outputs structured JSON to stdout. Your coding tool's built-in AI writes the changelog.

**Works identically in all of these tools:**

- **opencode** — `narrate owner/repo --from HEAD~4 --to HEAD --json-only`
- **Claude Code** — same command
- **Cursor (Composer)** — same command
- **Codex CLI** — same command
- **Workbuddy / Windsurf / any AI coding tool** — same command

The pattern is always: pipe JSON → let AI write prose. No environment variables needed.

```bash
# Equivalent in any tool: narrate collects, tool's AI writes
narrate ohmyzsh/ohmyzsh --from HEAD~4 --to HEAD --json-only
```

Outputs roughly 300+ lines of structured JSON to stdout — commits (with types, authors, SHAs), open/closed issues, community highlights, cross-references. Your coding tool's AI reads this and generates polished release notes.

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
pip install changelog-narrate
```

Python 3.10+ required. No external dependencies (stdlib only).

Or run directly from source:

```bash
git clone https://github.com/1knownothing/changelog-narrate.git
cd changelog-narrate
python -m narrate --help
```

## Options

```
usage: narrate [-h] --from FROM_REF --to TO_REF [--template {community,technical,marketing}]
               [--output OUTPUT] [--skip-quality] [--print] [--json-only]
               [--ai-model AI_MODEL] [--ai-endpoint AI_ENDPOINT]
               repo

positional arguments:
  repo                  owner/name (e.g., ohmyzsh/ohmyzsh)

options:
  --from FROM_REF       base ref (HEAD~4, v1.0, master@{7day})
  --to TO_REF           target ref (HEAD, master, v2.0)
  --template TEMPLATE   output style: community (default), technical, marketing
  --output, -o          output directory (default: references/)
  --skip-quality        skip quality validation
  --print               print markdown to stdout
  --json-only           stop at ANALYZE, output JSON for your coding tool's AI to write the changelog
  --ai-model AI_MODEL   AI model name (default: deepseek-chat).
                        Used only when AI_API_KEY or DEEPSEEK_API_KEY is set.
  --ai-endpoint AI_ENDPOINT
                        OpenAI-compatible endpoint URL.
                        Default: https://api.deepseek.com/v1/chat/completions
                        Examples:
                          https://api.openai.com/v1/chat/completions
                          http://localhost:11434/v1/chat/completions (Ollama)
```

### Environment variables

| Variable | Purpose |
|----------|---------|
| `GITHUB_TOKEN` / `GH_TOKEN` | Higher API rate limit (5,000 req/h vs 60) |
| `AI_API_KEY` | API key for any OpenAI-compatible AI provider |
| `DEEPSEEK_API_KEY` | Legacy alias for AI_API_KEY (used if AI_API_KEY is not set) |

## How it works

```
PARSE_INPUT  →  COLLECT_DATA  →  ANALYZE  →  WRITER  →  FORMATTER  →  QUALITY_CHECK
  (refs)       (GitHub API)    (classify)   (template/AI)  (markdown)   (validate)
```

Each step writes its output to the references directory, so you can inspect or resume from any stage.

### Pipeline details

1. **PARSE_INPUT** — Validates refs, saves orchestrator state
2. **COLLECT_DATA** — Fetches comparison, commits, open/closed issues from GitHub REST API
3. **ANALYZE** — Enriches commits (conventional commit parsing), cross-references issues, scores community impact. This is where `--json-only` stops.
4. **WRITER** — Runs template writer (rule-based) or AI writer (if `AI_API_KEY` set). AI writer falls back to template on failure.
5. **FORMATTER** — Assembles markdown from structured data
6. **QUALITY_CHECK** — Validates output completeness, flags missing sections, placeholder text

### Write-back to GitHub Release

You can pipe the formatted markdown and post it via GitHub CLI:

```bash
narrate owner/repo --from v1.0 --to v2.0 --print > release.md
gh release create v2.0 --notes-file release.md
```

## Roadmap

- [x] PyPI release
- [ ] GitHub Action — auto-generate release notes on tag push
- [ ] Write-back to GitHub Release body
- [ ] Multi-repo support

## Why narrate?

Good release notes build community. They turn a list of commits into a story that makes users feel informed and contributors feel appreciated. `narrate` handles the mechanical part — data fetching, categorization, formatting — so you can focus on the part that matters: understanding what your users need to know.

## License

MIT
