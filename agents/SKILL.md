---
name: changelog-release-notes
description: Community-driven release notes, PR review, and development direction intelligence for any GitHub repository. Orchestrates 6 specialized sub-agents based on user intent: generates changelogs (3 templates), reviews PRs with structured feedback, analyzes community signals to recommend development priorities, or produces project health reports. Fetches real GitHub REST API + GraphQL data including commits, issues, discussions, PR diffs, and comments.
compatibility: Write, Read, Glob, webfetch
---

# Community Intelligence for GitHub Projects

**Architecture**: Branch-based orchestrator with 6 sub-agents. The AI reads this file and follows the workflow matching the user's request.

## When to Use This Skill

Trigger when the user asks to:
- "Generate release notes / changelog for [repo]"
- "Review PR #[number]"
- "What should we build next?" / "Analyze community feedback"
- "How healthy is this project?" / "Project health report"
- "What changed between [ref] and [ref]"

---

## Architecture Overview

```
User says "generate changelog" / "review PR #42" / "what should we build next" / "how's the project"
                              │
                              ▼
                      ┌───────────────┐
                      │  PARSE_INPUT   │  ← Extract owner/repo/mode/refs/prNumber/template
                      └───────┬───────┘
                              │
                              ▼
                      ┌───────────────┐
                      │  COLLECT_DATA  │  ← Fetch only what the current mode needs
                      └───────┬───────┘
                              │
              ┌───────────────┼───────────────┬────────────────┐
              ▼               ▼               ▼                ▼
       ┌──────────┐   ┌──────────┐   ┌─────────────┐   ┌───────────┐
       │ ANALYZE  │   │REVIEW_PR │   │PLAN_DIRECTION│   │ (health)  │
       │(changelog│   │(Agent 3) │   │ (Agent 4)   │   │ ANALYZE   │
       │  mode)   │   │          │   │             │   │ (same as  │
       │(Agent 2) │   │          │   │             │   │ changelog)│
       └─────┬────┘   └────┬─────┘   └──────┬──────┘   └─────┬─────┘
             │             │                │                │
             ▼             ▼                ▼                ▼
       ┌─────────────────────────────────────────────────────────┐
       │                  GENERATE_REPORT (Agent 5)               │
       │   changelog.md / PR review / direction plan / health     │
       └──────────────────────────┬──────────────────────────────┘
                                  ▼
                         ┌──────────────┐
                         │ QUALITY_CHECK │
                         │  (Agent 6)    │
                         └───────┬──────┘
                              ▼
                           DONE / ERROR
```

---

## Step 1: Parse User Input (State: PARSE_INPUT)

Collect from user and determine mode:

| Field | Required | Default | Notes |
|-------|----------|---------|-------|
| **Repo** | ✅ Yes | — | `owner/repo` or full GitHub URL |
| **Mode** | Auto-detected | `changelog` | Inferred from request |
| **From Ref** | For changelog | Previous tag | Git tag, branch, or SHA |
| **To Ref** | For changelog | `HEAD` | Target ref |
| **PR Number** | For pr_review | — | From "review PR #42" |
| **Template** | For changelog | `community` | `community`, `technical`, `marketing` |

**Mode detection from natural language:**
```
"generate release notes" / "changelog" / "what changed" → mode = changelog
"review PR" / "check PR" / "review this" → mode = pr_review
"what to build" / "next direction" / "community feedback" → mode = direction
"project health" / "how is the project" / "health report" → mode = health
```

Write to `references/orchestrator_state.json`:
```json
{
  "state": "PARSE_INPUT",
  "mode": "changelog",
  "owner": "vercel",
  "repo": "next.js",
  "fromRef": "v14.0.0",
  "toRef": "v14.1.0",
  "template": "community"
}
```

---

## Step 2: Collect Data (State: COLLECT_DATA)

Read `references/orchestrator_state.json`. Determine what to fetch based on `mode`:

### For `changelog` mode:
Fetch commits comparison + open issues + closed issues (see `agents/data_collector.md`)

### For `pr_review` mode:
Fetch PR metadata + files + diffs + review comments + timeline comments (see `agents/data_collector.md`)

### For `direction` mode:
Fetch open/closed issues + top issue comments + open PRs + optional GraphQL discussions (see `agents/data_collector.md`)

### For `health` mode:
Fetch issues flow + PR flow + commit activity stats + contributors (see `agents/data_collector.md`)

**Dispatch**:
```typescript
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/data_collector.md and references/orchestrator_state.json.
Mode is ${mode}. Owner=${owner}, Repo=${repo}.
Fetch only the data needed for ${mode} mode. See data_collector.md for endpoint list.
Handle errors gracefully — set error flags, don't crash.
Write CollectorOutput JSON to references/collector_output.json.`
)
```

**On success**: Read `references/collector_output.json`. Check error flags for the mode's required data.
**On failure**: Go to ERROR state with appropriate message.

---

## Step 3: Branch Based on Mode

### Mode A: `changelog` → State: ANALYZE

Dispatch Community Analyst + Writer:

```typescript
// Step 3a: Analyze
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/community_analyst.md and references/collector_output.json.
Parse conventional commits, compute community scores, health metrics,
sentiment from reactions, trending topics.
Write CommunityMetrics JSON to references/community_metrics.json.
Template: ${template}.`
)

// Step 3b: Generate changelog text
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/writer.md and references/community_metrics.json.
Generate changelog sections using ${template} template.
Use AI to write content. If AI unavailable, use buildFallback* functions.
Write WriterOutput JSON to references/writer_output.json.`
)

// Then → GENERATE_REPORT
```

### Mode B: `pr_review` → State: REVIEW_PR

```typescript
// Extract PR data from collector_output, then dispatch PR Reviewer
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/pr_reviewer.md and references/collector_output.json.
PR #${prNumber} in ${owner}/${repo}.
Review the PR: check diff, find issues, produce structured output.
Write PRReviewOutput JSON to references/pr_review_output.json.`
)

// Then → GENERATE_REPORT
```

### Mode C: `direction` → State: PLAN_DIRECTION

```typescript
// Step 3a: First analyze community
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/community_analyst.md and references/collector_output.json.
Compute community metrics, scores, sentiment, trending topics.
Write CommunityMetrics JSON to references/community_metrics.json.`
)

// Step 3b: Then plan direction
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/direction_planner.md and references/community_metrics.json.
Also read references/previous_analysis.json if it exists.
Rank features, bugs, quick wins. Assess community mood and health.
Write DirectionRecommendation JSON to references/direction_output.json.`
)

// Then → GENERATE_REPORT
```

### Mode D: `health` → State: ANALYZE

Same as changelog's ANALYZE step, but output focuses on health metrics instead of changelog.

```typescript
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/community_analyst.md and references/collector_output.json.
Compute community metrics with focus on health: response times,
contributor trends, PR merge rates, bus factor, sentiment.
Write CommunityMetrics JSON to references/community_metrics.json.`
)

// Then → GENERATE_REPORT
```

---

## Step 4: Generate Report (State: GENERATE_REPORT)

Dispatch Formatter to assemble the final output for the current mode:

```typescript
// Generic dispatch — formatter adapts to mode
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/formatter.md.
Mode is ${mode}. Build output based on mode:

- changelog: read references/writer_output.json → markdown changelog
- pr_review: read references/pr_review_output.json → structured PR review
- direction: read references/direction_output.json → direction recommendations
- health: read references/community_metrics.json → health report

Write FormatterInput JSON (with rawMarkdown) to references/formatted_output.json.`
)
```

---

## Step 5: Quality Check (State: QUALITY_CHECK)

```typescript
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/quality_checker.md and references/formatted_output.json.
Validate mode-appropriate output. Inject fallbacks if sections missing.
Write QualityReport JSON to references/quality_report.json.`
)
```

**On success**: Check `passed`. If true → DONE. If false with fallbacks → present with warning.

---

## Step 6: Output + Write-Back (State: DONE)

Present the final result. Then **ask the user if they want to write back to GitHub**:

### For changelog mode:
```
Output ready. Options:
- Copy / save to CHANGELOG.md
- Change template (community/technical/marketing)
```

### For PR review mode:
```
Output ready. Would you like me to:
1. Post this review as a PR comment on GitHub?
2. Adjust focus and re-review?
```

**If user confirms write-back (option 1):**
```typescript
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/data_collector.md.
User confirmed posting PR review for ${owner}/${repo} PR #${prNumber}.

Post a PR review comment:
POST /repos/${owner}/${repo}/pulls/${prNumber}/comments
Body: ${prReviewOutput.summary} (full review markdown)

Set commit_id from collector_output pullRequest.commits[last].sha,
path and line from first issue's file and line.

Report the result URL to the user.`
)
```

### For direction mode:
```
Output ready. Would you like me to:
1. Create tracking issues for the top recommendations?
2. Export as markdown?
```

**If user confirms write-back (option 1):**
```typescript
task(
  load_skills=[],
  run_in_background=false,
  prompt=`Read agents/data_collector.md.
User confirmed creating tracking issues for direction recommendations.
For each item in topFeatures, topBugs, quickWins:
  POST /repos/${owner}/${repo}/issues
  Body: Create issue with title and body describing the recommendation.
         Add label "direction" and the effort level label.
  Report each created issue's URL.

If some already have existing issues (issueNumber > 0), skip those.`
)
```

### For health mode:
```
Output ready. Compare with previous report or export as markdown.
```

### Save snapshot for trend tracking:

After user decides on write-back, write `references/previous_analysis.json`:

```typescript
{
  "createdAt": new Date().toISOString(),
  "snapshotRef": toRef ?? "HEAD",
  "healthScore": communityMetrics.health.score,
  "sentimentScore": communityMetrics.sentiment.overallScore,
  "totalOpenIssues": collectorOutput.issues.filter(i => i.state === "open").length,
  "totalOpenPRs": collectorOutput.pullRequests?.filter(p => p.state === "open").length ?? 0,
  "prMergeRate": communityMetrics.health.prMergeRate,
  "activeContributors30d": communityMetrics.health.activeContributors30d,
  "topics": communityMetrics.trendingTopics.map(t => ({ topic: t.topic, frequency: t.frequency, totalReactions: t.totalReactions })),
  "recommendedIssueNumbers": directionOutput ? [...directionOutput.topFeatures.map(f => f.issueNumber), ...directionOutput.topBugs.map(b => b.issueNumber)] : [],
  "recommendedFeatureNumbers": directionOutput?.topFeatures.map(f => f.issueNumber) ?? [],
  "recommendedBugNumbers": directionOutput?.topBugs.map(b => b.issueNumber) ?? []
}
```

---

## Error Recovery (State: ERROR)

| Failure | Message |
|---------|---------|
| All data collection failed | "Could not fetch data from GitHub. Verify the repo exists and is public." |
| PR not found | "PR #{number} not found in {owner}/{repo}." |
| No commits in range | "No commits found between {fromRef} and {toRef}." |
| GraphQL discussions failed | "Discussions data unavailable (GraphQL). Continuing with issues data." |
| Quality check unrecoverable | Return output with issues documented |

---

## File Structure

```
changelog-release-notes/
├── SKILL.md                    ← Orchestrator (this file)
├── agents/
│   ├── data_collector.md       ← GitHub data fetching (all modes)
│   ├── community_analyst.md    ← Metrics, scores, sentiment, topics
│   ├── pr_reviewer.md          ← PR review with diff analysis
│   ├── direction_planner.md    ← Community direction recommendations
│   ├── writer.md               ← Changelog text generation
│   ├── formatter.md            ← Output assembly (all modes)
│   └── quality_checker.md      ← Validation + fallbacks
├── references/
│   ├── handoff_schemas.md      ← 9 data contracts
│   ├── orchestrator_state.json ← Runtime state (auto-generated)
│   ├── collector_output.json   ← All fetched data (auto-generated)
│   ├── community_metrics.json  ← Analysis results (auto-generated)
│   ├── pr_review_output.json   ← PR review (auto-generated)
│   ├── direction_output.json   ← Direction plan (auto-generated)
│   ├── writer_output.json      ← Changelog text (auto-generated)
│   ├── formatted_output.json   ← Final assembly (auto-generated)
│   ├── quality_report.json     ← Validation (auto-generated)
│   └── previous_analysis.json  ← Trend data (auto-generated)
└── prompts/
    ├── community.md            ← Community template
    ├── technical.md            ← Technical template
    └── marketing.md            ← Marketing template
```

## Important Notes

1. **Lazy data collection** — Only fetch what the current mode needs. Don't waste API calls.
2. **GraphQL for Discussions** — For `direction` mode, optionally fetch Discussions via GraphQL POST. If it fails, skip gracefully.
3. **Rate limits**: 5000/hr authenticated. Use `If-None-Match` for conditional requests. Token is user-provided.
4. **Trend tracking** — Write `previous_analysis.json` after each health/direction run so next run can compare.
5. **All agents use task()** — Do NOT do agent work yourself. Each agent file has complete instructions.
6. **Checkpoint via filesystem** — Each agent writes to `references/*.json`. Read to verify completion.
