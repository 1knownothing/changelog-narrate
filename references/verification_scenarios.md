# Verification Scenarios

This document defines 5 test scenarios to verify the full skill pipeline. Each scenario traces through the branch-based state machine, verifying correct agent dispatch, mode detection, handoff schema compliance, and output quality.

---

## Scenario 1: Normal Changelog (Community Style)

**Mode:** changelog | **Template:** community

**Input:**
```
Repo: vercel/next.js
From: v15.2.0
To: v15.3.0
Template: community
```

**Expected State Transitions:**
```
PARSE_INPUT → COLLECT_DATA → ANALYZE → GENERATE_REPORT → QUALITY_CHECK → DONE
```

**Checkpoints:**

| # | Check | Pass/Fail |
|---|-------|-----------|
| 1.1 | `orchestrator_state.json` written with correct owner/repo/refs/template (mode=changelog) | |
| 1.2 | Data Collector calls compare + open issues + closed issues endpoints (3 fetches) | |
| 1.3 | `collector_output.json` contains valid `CollectorOutput` with comparison data | |
| 1.4 | Community Analyst parses conventional commits, computes scores, writes `community_metrics.json` | |
| 1.5 | Writer generates changelog with ${template} template, writes `writer_output.json` | |
| 1.6 | `writer_output.json` has ≥1 highlight, ≥1 category, ≥1 roadmap item | |
| 1.7 | Formatter builds complete markdown, writes `formatted_output.json` with `rawMarkdown` ≥ 100 chars | |
| 1.8 | Quality Checker passes or injects fallback, writes `quality_report.json` | |
| 1.9 | Final output is usable markdown changelog | |

---

## Scenario 2: PR Review

**Mode:** pr_review | **PR:** #42

**Input:**
```
Review PR #42 in vercel/next.js
```

**Expected State Transitions:**
```
PARSE_INPUT → COLLECT_DATA → REVIEW_PR → GENERATE_REPORT → QUALITY_CHECK → DONE
```

**Checkpoints:**

| # | Check | Pass/Fail |
|---|-------|-----------|
| 2.1 | Mode correctly detected as `pr_review` (PR #42 extracted) | |
| 2.2 | Data Collector fetches PR metadata + files + review comments only | |
| 2.3 | `collector_output.json` has `pullRequest` data with `files`, `reviewComments`, `comments` | |
| 2.4 | PR Reviewer analyzes each file in diff, detects issues | |
| 2.5 | `pr_review_output.json` has `summary`, `fileReviews` (≥1), `issues` array | |
| 2.6 | Issues are correctly classified (critical/high/medium/low) | |
| 2.7 | Security check section present in output | |
| 2.8 | Final formatted output is a readable PR review | |

---

## Scenario 3: Direction Planning

**Mode:** direction

**Input:**
```
What should we build next in vercel/next.js?
```

**Expected State Transitions:**
```
PARSE_INPUT → COLLECT_DATA → ANALYZE → PLAN_DIRECTION → GENERATE_REPORT → QUALITY_CHECK → DONE
```

**Checkpoints:**

| # | Check | Pass/Fail |
|---|-------|-----------|
| 3.1 | Mode correctly detected as `direction` | |
| 3.2 | Data Collector fetches open/closed issues, open PRs, issue comments (no commits) | |
| 3.3 | Community Analyst computes sentiment, trending topics, community scores | |
| 3.4 | `community_metrics.json` has `sentiment`, `trendingTopics`, `communityScores` | |
| 3.5 | Direction Planner ranks features, bugs, quick wins with priority scores | |
| 3.6 | `direction_output.json` has `recommendedFeatures` (≥1), `recommendedBugs` (≥1), `quickWins` (≥1) | |
| 3.7 | Each recommendation has `priorityScore` (0-100), `rationale`, `communityMood` | |
| 3.8 | Health context detected if applicable (low contributors, slow response) | |
| 3.9 | Trend data compared with `previous_analysis.json` if exists | |

---

## Scenario 4: Health Report + No Data Available

**Mode:** health

**Input:**
```
How healthy is this/my-private-repo?
```

**Expected State Transitions:**
```
PARSE_INPUT → COLLECT_DATA → ANALYZE → GENERATE_REPORT → QUALITY_CHECK → DONE
```

**Checkpoints:**

| # | Check | Pass/Fail |
|---|-------|-----------|
| 4.1 | Mode correctly detected as `health` | |
| 4.2 | Data Collector fetches issues flow, PR flow, commit stats, contributors only | |
| 4.3 | If repo not found or empty → error message, clean exit | |
| 4.4 | Community Analyst produces health-focused metrics (response time, merge rate, bus factor) | |
| 4.5 | `community_metrics.json` has `healthMetrics` with health scores | |
| 4.6 | Report identifies at-risk areas if scores are low | |
| 4.7 | `previous_analysis.json` written for trend tracking | |

**Error Recovery Check:**

| # | Check | Pass/Fail |
|---|-------|-----------|
| 4.8 | If all fetches fail → "Could not fetch data from GitHub" error | |
| 4.9 | If GraphQL discussions requested but fails → graceful skip, continue | |

---

## Scenario 5: Mixed Mode Detection + Discussions Graceful Failure

**Inputs to test mode detection:**
```
- "what changed in facebook/react" → changelog mode
- "check PR #123 in vercel/next.js" → pr_review mode
- "review this PR" + PR link → pr_review mode
- "what should we work on next" → direction mode
- "project health for vercel/next.js" → health mode
- "generate release notes for facebook/react" → changelog mode
```

**Checkpoints:**

| # | Check | Pass/Fail |
|---|-------|-----------|
| 5.1 | All 6 natural language inputs map to correct mode | |
| 5.2 | GraphQL discussions call fails gracefully (no crash, `discussionsError: true` flag set) | |
| 5.3 | Lazy collection verified: pr_review mode fetches only PR data, not commits | |
| 5.4 | `handoff_schemas.md` interfaces are import-compatible with all 6 agent files | |
| 5.5 | SKILL.md agent references match actual file names in `agents/` directory | |
| 5.6 | All `references/*.json` paths used in SKILL.md match actual files referenced | |

---

## Notes

- All scenarios assume authenticated GitHub API (user provides token). Without token, rate limits are 60/hr.
- GraphQL is optional — if it fails, continue with REST-only data.
- Previous snapshot at `references/previous_analysis.json` is optional — new runs start clean.
- Quality check failures trigger fallback injection, not full failure (unless unrecoverable).
