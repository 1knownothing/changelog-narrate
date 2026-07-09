# Direction Planner Agent

## Role
Aggregates all community signals to recommend the next development directions. Analyzes what the community is asking for, what's broken, and what would have the highest impact.

## Inputs
Reads `references/community_metrics.json` (produced by Community Analyst). Optionally reads `references/collector_output.json` for raw discussions/comments.

## Outputs
Writes `references/direction_output.json` conforming to `DirectionRecommendation` schema.

---

## Analysis Pipeline

### Step 1: Identify Top Features (Community Demand)

From enriched open issues, filter and rank by:

```typescript
function rankFeatures(issues: EnrichedIssue[]): PriorityItem[] {
  return issues
    .filter(i => i.typeHint === "feature" || i.labels.some(l =>
      ["feature", "enhancement", "feat", "request"].includes(l.toLowerCase())))
    .sort((a, b) => b.priorityScore - a.priorityScore)
    .slice(0, 10)
    .map(i => ({
      title: i.title,
      issueNumber: i.number,
      url: i.url,
      priorityScore: i.priorityScore,
      reasoning: generateReasoning(i),
      effort: estimateEffort(i),
      communityDemand: `${i.reactions} reactions, ${i.comments} comments`
    }));
}
```

### Step 2: Identify Top Bugs (User Impact)

```typescript
function rankBugs(issues: EnrichedIssue[]): PriorityItem[] {
  return issues
    .filter(i => i.typeHint === "bug" || i.labels.some(l =>
      ["bug", "bugfix", "regression", "critical"].includes(l.toLowerCase())))
    .sort((a, b) => b.priorityScore - a.priorityScore)
    .slice(0, 10)
    .map(i => ({
      title: i.title,
      issueNumber: i.number,
      url: i.url,
      priorityScore: i.priorityScore,
      reasoning: `Affects ${i.reactions} users. ${i.comments} comments indicate reproduction details available.`,
      effort: estimateEffort(i),
      communityDemand: `${i.reactions} reactions, ${i.comments} comments`
    }));
}
```

### Step 3: Identify Quick Wins

Low-effort, high-impact items:

```typescript
function findQuickWins(features: PriorityItem[], bugs: PriorityItem[]): PriorityItem[] {
  // Features/bugs with high priority score but low implementation complexity
  const allItems = [...features, ...bugs];
  return allItems
    .filter(i => i.effort === "low")
    .sort((a, b) => b.priorityScore - a.priorityScore)
    .slice(0, 5);
}
```

### Step 4: Trend Analysis + Resolution Tracking (if previous snapshot exists)

Read `references/previous_analysis.json` if it exists. Compare:

```
Rising topics: frequency increased > 20% vs previous snapshot
Falling topics: frequency decreased > 20%
New topics: appeared since last snapshot
```

**Resolution tracking**: Check which previously recommended issues are now resolved:

```typescript
function trackResolution(
  previous: PreviousAnalysis,
  currentIssues: EnrichedIssue[]
): ResolvedItem[] {
  const prevRecommendations = [
    ...previous.recommendedFeatureNumbers,
    ...previous.recommendedBugNumbers,
    ...previous.recommendedIssueNumbers,
  ];

  const currentIssueMap = new Map(currentIssues.map(i => [i.number, i]));

  return prevRecommendations.map(num => {
    const current = currentIssueMap.get(num);
    if (!current) return { issueNumber: num, status: "not_found" };
    if (current.state === "closed") return { issueNumber: num, status: "resolved" };
    return { issueNumber: num, status: "still_open" };
  });
}
```

Attach to the output as `previousResolution: ResolvedItem[]`. This appears in the formatter output so users see "✅ 3 of 5 previous recommendations are now resolved."

### Step 5: Health Context

```typescript
function buildHealthContext(metrics: CommunityMetrics) {
  return {
    currentHealth: metrics.health.score >= 70 ? "Healthy" :
                   metrics.health.score >= 40 ? "Needs attention" : "At risk",
    trend: metrics.health.trend,
    keyRisks: []
  };
  // Add risks:
  if (metrics.health.prMergeRate < 0.3) risks.push("Low PR merge rate — PRs may be stalled");
  if (metrics.health.newContributors30d < 2) risks.push("Few new contributors — community growth may be slowing");
  if (metrics.health.issueResponseTimeP50 > 72) risks.push("Issue response time > 72h — contributors may feel ignored");
}
```

### Step 6: Community Mood

```typescript
function assessMood(metrics: CommunityMetrics): string {
  const s = metrics.sentiment;
  if (s.overallScore > 0.3) return "Positive — the community is engaged and appreciative";
  if (s.overallScore > 0) return "Mixed — some enthusiasm, some frustrations";
  if (s.overallScore > -0.3) return "Cautious — users are encountering issues";
  return "Negative — significant community frustration detected";
}
```

### Step 7: Strategic Direction

Generate a narrative that connects the data points:

```
If feature requests > bugs:
  "The community is most excited about [top feature]. 
   This aligns with [trending topic] which has [N] mentions across issues and discussions."

If bugs > feature requests:
  "Community sentiment is currently driven by stability concerns. 
   [Top bug] affects [N] users and should be the top priority."

If trending topic "docs" is rising:
  "Documentation gaps are a recurring theme — users are asking for [specific examples]."
```

---

## Effort Estimation Heuristic

```typescript
function estimateEffort(issue: EnrichedIssue): "low" | "medium" | "high" {
  const labels = issue.labels.map(l => l.toLowerCase());

  if (labels.some(l => ["good first issue", "easy", "tiny", "docs"].includes(l))) return "low";
  if (labels.some(l => ["epic", "large", "major", "massive"].includes(l))) return "high";
  if (labels.some(l => ["medium", "moderate"].includes(l))) return "medium";

  // Body length heuristic
  const bodyLen = issue.body?.length ?? 0;
  if (bodyLen > 2000) return "high";
  if (bodyLen > 500) return "medium";
  return "low"; // Very short body = probably simple
}
```

---

## Output Format

```json
{
  "owner": "vercel",
  "repo": "next.js",
  "topFeatures": [
    {
      "title": "Add support for React Server Components streaming",
      "issueNumber": 12345,
      "url": "https://github.com/vercel/next.js/issues/12345",
      "priorityScore": 85,
      "reasoning": "42 reactions, 15 comments. This is the #1 requested feature.",
      "effort": "high",
      "communityDemand": "42 reactions, 15 comments, 3 related discussions"
    }
  ],
  "topBugs": [
    {
      "title": "CSS modules break with SWC minification",
      "issueNumber": 12346,
      "url": "https://github.com/vercel/next.js/issues/12346",
      "priorityScore": 72,
      "reasoning": "24 reactions indicating broad impact. Labeled as regression.",
      "effort": "medium",
      "communityDemand": "24 reactions, 8 comments"
    }
  ],
  "quickWins": [
    {
      "title": "Add TypeScript strict mode example to docs",
      "issueNumber": 12347,
      "url": "https://github.com/vercel/next.js/issues/12347",
      "priorityScore": 35,
      "reasoning": "Labeled 'good first issue'. Short description indicates contained change.",
      "effort": "low",
      "communityDemand": "5 reactions, 2 comments"
    }
  ],
  "strategicDirection": "Community focus is shifting toward streaming and server-side rendering performance. Feature requests outweigh bugs 2:1. Consider investing in the streaming architecture as the next major theme.",
  "healthContext": {
    "currentHealth": "Healthy",
    "trend": "stable",
    "keyRisks": []
  },
  "communityMood": "Positive — the community is engaged and appreciative",
  "previousResolution": [
    { "issueNumber": 12340, "status": "resolved" },
    { "issueNumber": 12341, "status": "still_open" }
  ]
}
```

---

## Important Rules

1. **Data-driven, not speculative** — Every recommendation must cite specific issue numbers and community signals. No "the community might want X."
2. **Balance feature requests vs bugs** — If bugs dominate sentiment, bugs should appear before features in the output.
3. **Quick wins matter** — Even low-priority issues can be quick wins that build community goodwill. Always include them.
4. **Track resolution** — If an issue from a previous recommendation is now closed, note it as "resolved" rather than repeating it.
5. **No false precision** — Priority scores are relative rankings, not absolute measurements. Round to nearest 5.
6. **Use previous snapshot** — Read `references/previous_analysis.json` if it exists for trend comparison. Don't require it.
