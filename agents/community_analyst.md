# Community Analyst Agent

**Replaces**: `data_analyst.md`

## Role
Enriches raw GitHub data into structured insights: conventional commits, community scores, health metrics, sentiment analysis, and trending topics.

## Inputs
Reads `references/collector_output.json` (produced by Data Collector).

## Outputs
Writes `references/community_metrics.json` conforming to `CommunityMetrics` schema.

---

## Processing Pipeline

### Step 1: Parse Conventional Commits

For each commit, extract type, scope, breaking flag:

```
Pattern: ^(?<type>feat|fix|chore|docs|refactor|test|perf)(\((?<scope>[^)]+)\))?(?<breaking>!)?:\s+(?<subject>.+)$
```

Type mapping: `feat`→feat, `fix`→fix, `perf`→perf, `chore/build/ci`→chore, `docs`→docs, `refactor/style`→refactor, `test/revert`→test, no-match→other
Breaking: `BREAKING CHANGE:` in body OR `!` after type/scope

### Step 2: Build EnrichedCommits

```typescript
function enrichCommit(raw): EnrichedCommit {
  return {
    sha: raw.sha.substring(0, 7),
    message: raw.commit.message,
    author: raw.author?.login ?? raw.commit.author.name ?? "unknown",
    date: raw.commit.author.date,
    url: raw.html_url,
    referencedIssues: extractIssueRefs(raw.commit.message),
    isBreaking: raw.commit.message.includes("BREAKING CHANGE") || raw.commit.message.includes("BREAKING:"),
    scope: extractScope(raw.commit.message),
    type: extractType(raw.commit.message) || "other"
  };
}
```

Issue ref extraction — 5 regex patterns (port from original codebase):
```
/#(\d+)/g                    — plain ref
/close[sd]?\s+#(\d+)/gi      — "closes #123"
/fix(?:es|ed)?\s+#(\d+)/gi   — "fixes #123"
/resolve[sd]?\s+#(\d+)/gi    — "resolves #123"
/re\s+#(\d+)/gi              — "re #123"
```

### Step 3: Compute Community Scores

For each issue:

```typescript
const communityScore = (reactions?.["+1"] ?? 0) * 2
  + (reactions?.heart ?? 0) * 3
  + (reactions?.hooray ?? 0) * 2
  + (comments ?? 0)
  + (labels?.length ?? 0);
```

The formula weights: 👍=2, ❤️=3, 🎉=2, plus comments and label count.

### Step 4: Compute Sentiment from Reactions

```typescript
function computeSentiment(issue): "positive" | "neutral" | "negative" {
  const pos = (issue.reactions?.["+1"] ?? 0) + (issue.reactions?.heart ?? 0)
    + (issue.reactions?.hooray ?? 0) + (issue.reactions?.rocket ?? 0);
  const neg = (issue.reactions?.["-1"] ?? 0);
  if (pos > neg * 3) return "positive";
  if (neg > pos) return "negative";
  return "neutral";
}
```

### Step 5: Compute Priority Score

```typescript
function computePriorityScore(issue): number {
  let score = 0;
  // Reaction volume (max 30 points)
  score += Math.min((issue.reactions?.total_count ?? 0) * 3, 30);
  // Label signals
  const labels = (issue.labels ?? []).map(l => l.name.toLowerCase());
  if (labels.some(l => ["bug","security","critical","p0","regression"].includes(l))) score += 20;
  if (labels.some(l => ["feature","enhancement","feat"].includes(l))) score += 10;
  // Comment volume indicates engagement (max 20)
  score += Math.min((issue.comments ?? 0) * 2, 20);
  // Time decay for open issues
  if (issue.state === "open") {
    const daysOpen = (Date.now() - new Date(issue.created_at).getTime()) / 86400000;
    const decayPenalty = Math.min(daysOpen * 0.3, 15);
    if (labels.some(l => ["bug","security","critical"].includes(l))) {
      score += Math.min(daysOpen * 0.5, 15); // stale bugs = more urgent
    } else {
      score -= decayPenalty;
    }
  }
  return Math.max(0, Math.min(100, score));
}
```

### Step 6: Compute Health Metrics

```typescript
function computeHealth(
  issues: RawGitHubIssue[],
  pullRequests: PullRequestData[],
  comments: IssueComment[],
  commits: EnrichedCommit[]
): CommunityHealth {
  // Response time: time between issue creation and first comment
  const responseTimes = computeResponseTimes(issues, comments);
  // PR merge rate
  const closedPRs = (pullRequests ?? []).filter(p => p.state === "closed" || p.state === "merged");
  const mergedPRs = closedPRs.filter(p => p.state === "merged");
  const prMergeRate = closedPRs.length > 0 ? mergedPRs.length / closedPRs.length : 0;
  // Bus factor: unique authors needed for 50% of commits
  const busFactor = computeBusFactor(commits);

  return {
    score: computeHealthScore({ issueResponseTimeP50, prMergeRate, activeContributors30d, busFactor }),
    trend: determineTrend(/* compare with previous snapshot if available */),
    issueResponseTimeP50,
    prReviewTimeP50,
    prMergeRate,
    activeContributors30d,
    newContributors30d,
    busFactor
  };
}
```

### Step 7: Detect Trending Topics

Use keyword frequency across issue titles, bodies, and comments to identify clusters:

```typescript
function detectTopics(issues, comments, discussions): TopicCluster[] {
  // Simple keyword frequency approach:
  // 1. Tokenize all text (titles + bodies + comments)
  // 2. Count keyword frequency
  // 3. Group related keywords (e.g., "dark mode", "theme", "dark")
  // 4. For each cluster, compute frequency, reactions, sentiment
  // 5. Compare frequency vs. previous snapshot to determine trend
}
```

**Heuristic approach**: Extract common noun phrases from issue titles. Group by shared keywords. Compute aggregate reactions per group.

### Step 8: Build Summary Stats

```typescript
function buildSummary(commits, issues): Summary {
  const contributors = [...new Set(commits.map(c => c.author))];
  // ... date range, top contributor, etc.
}
```

### Step 9: Top Community Issues

Sort all issues by `communityScore` descending, take top 10.

### Step 10: Contributor Stats

Compute contributor intelligence from commits and issue/PR authors:

```typescript
function computeContributorStats(commits, issues, pullRequests): ContributorStats {
  const commitAuthors = [...new Set(commits.map(c => c.author))];
  const issueAuthors = [...new Set(issues.filter(i => i.user?.login).map(i => i.user.login))];
  const prAuthors = [...new Set((pullRequests ?? []).filter(p => p.user?.login).map(p => p.user.login))];

  // All unique contributors across all activities
  const allAuthors = [...new Set([...commitAuthors, ...issueAuthors, ...prAuthors])];

  // Identify first-time contributors (appear in issues/PRs but NOT in commits)
  const firstTimeContributors = issueAuthors.filter(a => !commitAuthors.includes(a));

  // Most active: count commits + issues + PRs per person
  const activityCounts = new Map<string, number>();
  for (const a of commitAuthors) activityCounts.set(a, (activityCounts.get(a) ?? 0) + 1);
  for (const a of issueAuthors) activityCounts.set(a, (activityCounts.get(a) ?? 0) + 1);
  for (const a of prAuthors) activityCounts.set(a, (activityCounts.get(a) ?? 0) + 1);

  const mostActive = [...activityCounts.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([login, count]) => ({ login, contributions: count }));

  return {
    totalUnique: allAuthors.length,
    commitAuthors: commitAuthors.length,
    firstTimeContributors,
    mostActive,
    newContributorCount: firstTimeContributors.length
  };
}
```

### Step 11: Attach ContributorStats to Output

Add `contributorStats` to the CommunityMetrics output:

```typescript
communityMetrics.contributorStats = computeContributorStats(commits, issues, pullRequests);
```

---

## Important Rules

1. **Rule-based deterministic analysis** — All metrics computed here are formulaic. No AI in this agent.
2. **Empty data handling** — If `commits` is empty, metrics are computed from available data with `0` for missing values.
3. **Score ties** — Sort by issue number descending (newer first) when scores are equal.
4. **Sentiment from reactions only** — Don't analyze comment text for sentiment (that's AI work).
5. **Trend requires history** — `health.trend` needs a previous snapshot from `references/previous_analysis.json`. If none exists, report `"stable"`.
