# Writer Agent

## Role
Generates changelog sections from structured analysis data. Produces categorized content, community highlights, and roadmap items. Includes fallback generation for when AI-powered writing is unavailable.

## Inputs
Reads from `references/community_metrics.json` (produced by Community Analyst agent, conforming to `CommunityMetrics` schema).

## Outputs
Writes to `references/writer_output.json` conforming to `WriterOutput` schema (see `references/handoff_schemas.md`).

## Input Parameters
- `template` (string): `"community"` | `"technical"` | `"marketing"`

---

## Workflow

### Step 1: Build the Prompt Context

Construct the prompt for the AI based on the template style:

**Community style** (warm, contributor-focused):

```
You are a Developer Relations engineer writing release notes.

Repo: {owner}/{repo} ({fromRef} → {toRef})
Summary: {totalCommits} commits across {filesChanged} files, +{additions}/-{deletions} lines
Date range: {dateRange}
Contributors: {contributors}
Top contributor: {topContributor}

Commit breakdown:
- Features: {feat}
- Bug fixes: {fix}
- Performance: {perf}
- Chores: {chore}
- Documentation: {docs}
- Refactors: {refactor}
- Others: {other}
- Breaking changes: {breaking}

Generate a JSON output with:
1. 3-5 community highlights with community impact
2. 2-6 categorized change sections
3. 3-5 roadmap items with predictions
```

**Technical style** (precise, migration-ready):

```
You are a senior engineer documenting a release.

Repo: {owner}/{repo} ({fromRef} → {toRef})
Summary: {totalCommits} commits across {filesChanged} files, +{additions}/-{deletions} lines
Date range: {dateRange}
Contributors: {contributors}

Commit breakdown:
- Features: {feat}
- Bug fixes: {fix}
- Performance: {perf}
- Chores: {chore}
- Documentation: {docs}
- Refactors: {refactor}
- Others: {other}
- Breaking changes: {breaking}

Generate a JSON output with:
1. Breaking changes FIRST (with migration steps)
2. Features with exact API signatures
3. Bug fixes with root causes
4. Performance with benchmarks
```

**Marketing style** (punchy, benefit-driven):

```
You are a marketing writer crafting release announcements.

Repo: {owner}/{repo} ({fromRef} → {toRef})
Summary: {totalCommits} commits across {filesChanged} files, +{additions}/-{deletions} lines
Date range: {dateRange}
Contributors: {contributors}

Commit breakdown:
- Features: {feat}
- Bug fixes: {fix}
- Performance: {perf}
- Chores: {chore}
- Documentation: {docs}
- Refactors: {refactor}
- Others: {other}
- Breaking changes: {breaking}

Generate a JSON output with:
1. 2-3 biggest community highlights with "You can now..." framing
2. Benefit-driven categories
3. Teaser roadmap with predictions
```

---

### Step 2: Generate Each Section

#### A. Community Highlights

Select from `topCommunityIssues` (sorted by `communityScore`). Use the top 3-5 items:

```typescript
function buildHighlights(issues: EnrichedIssue[]): CommunityHighlight[] {
  return issues.slice(0, 5).map(i => ({
    title: i.title,
    issueNumber: i.number,
    url: i.url,
    reactions: i.reactions,
    description: i.body || "No description provided.",
    type: i.typeHint ?? "improvement",
    comments: i.comments,
    requestedBy: i.author,
    communityImpact: "This was one of the most-requested features."
  }));
}
```

#### B. Categorized Changes

Group enriched commits by type, preserving the template-specific section organization:

```typescript
function buildCategories(
  commits: EnrichedCommit[],
  template: string
): CategorySection[] {
  const groupMap: Record<string, EnrichedCommit[]> = {};
  for (const c of commits) {
    if (!groupMap[c.type]) groupMap[c.type] = [];
    groupMap[c.type].push(c);
  }

  const sections: CategorySection[] = [];

  if (groupMap.breaking?.length) {
    sections.push({
      title: template === "technical" ? "Breaking Changes" :
             template === "marketing" ? "⚠️ Breaking Changes" : "重大变更",
      emoji: "⚠️",
      items: groupMap.breaking.map(c => ({
        description: c.message.split("\n")[0],
        userBenefit: "",
        author: c.author,
        url: c.url
      }))
    });
  }

  // Features
  if (groupMap.feat?.length) {
    sections.push({
      title: template === "technical" ? "New Features" :
             template === "marketing" ? "✨ What's New" : "新功能",
      emoji: "✨",
      items: groupMap.feat.map(c => ({
        description: c.message.split("\n")[0],
        userBenefit: "",
        issueOrPR: c.referencedIssues[0],
        author: c.author,
        url: c.url
      }))
    });
  }

  // Bug Fixes
  if (groupMap.fix?.length) {
    sections.push({
      title: template === "technical" ? "Bug Fixes" :
             template === "marketing" ? "🛠️ Bug Fixes" : "问题修复",
      emoji: "🛠️",
      items: groupMap.fix.map(c => ({
        description: c.message.split("\n")[0],
        userBenefit: "",
        issueOrPR: c.referencedIssues[0],
        author: c.author,
        url: c.url
      }))
    });
  }

  // Performance
  if (groupMap.perf?.length) {
    sections.push({
      title: "Performance",
      emoji: "⚡",
      items: groupMap.perf.map(c => ({
        description: c.message.split("\n")[0],
        userBenefit: "",
        author: c.author,
        url: c.url
      }))
    });
  }

  // Chore + Docs + Refactor + Test all go to "Other Changes" / "Other Improvements"
  const otherTypes = ["chore", "docs", "refactor", "test", "other"];
  const otherCommits = commits.filter(c => otherTypes.includes(c.type));
  if (otherCommits.length) {
    sections.push({
      title: template === "technical" ? "Other Improvements" :
             template === "marketing" ? "🔧 Other Improvements" : "其他改进",
      emoji: "🔧",
      items: otherCommits.map(c => ({
        description: c.message.split("\n")[0],
        author: c.author,
        url: c.url
      }))
    });
  }

  return sections;
}
```

#### C. Roadmap

Select from `openIssues` sorted by reaction count descending:

```typescript
function buildRoadmap(openIssues: OpenIssueData[]): RoadmapItem[] {
  return openIssues.slice(0, 5).map(i => ({
    title: i.title,
    issueNumber: i.number,
    reactions: i.reactions,
    likelihood: i.reactions > 20 ? "high" : i.reactions > 5 ? "medium" : "low",
    url: i.url,
    prediction: "" // AI-generated if API available, empty if fallback
  }));
}
```

---

## Fallback Generation (No AI Required)

When the orchestrator indicates AI writing is unavailable (no API key), use these fallback functions ported from the original `ai.ts`:

### Fallback: Build Highlights

```typescript
function buildFallbackHighlights(
  enriched: EnrichedIssue[],
  typeHint: "feature" | "bug" | "improvement"
): CommunityHighlight[] {
  return enriched
    .filter(i => i.typeHint === typeHint || !typeHint)
    .slice(0, 5)
    .map(i => ({
      title: i.title,
      issueNumber: i.number,
      url: i.url,
      reactions: i.reactions,
      description: extractIssueSummary(i.body, i.title),
      type: i.typeHint ?? "improvement",
      comments: i.comments,
      requestedBy: i.author,
      communityImpact: ""
    }));
}
```

### Fallback: Build Categories

```typescript
function buildFallbackCategories(
  commits: EnrichedCommit[],
  template: string
): CategorySection[] {
  const sections: CategorySection[] = [];
  const typeGroups = ["feat", "fix", "perf", "chore", "docs", "refactor"];

  for (const type of typeGroups) {
    const group = commits.filter(c => c.type === type);
    if (group.length === 0) continue;

    const label = {
      feat: "Features", fix: "Bug Fixes", perf: "Performance",
      chore: "Chores", docs: "Documentation", refactor: "Refactors"
    }[type] || "Other";

    const emoji = {
      feat: "✨", fix: "🛠", perf: "⚡",
      chore: "🔧", docs: "📚", refactor: "♻️"
    }[type] || "🔧";

    sections.push({
      title: label,
      emoji,
      items: group.slice(0, 10).map(c => ({
        description: c.message.split("\n")[0],
        author: c.author,
        url: c.url
      }))
    });
  }
  return sections;
}
```

### Fallback: Build Roadmap

```typescript
function buildFallbackRoadmap(
  openIssues: OpenIssueData[]
): RoadmapItem[] {
  return openIssues
    .sort((a, b) => b.reactions - a.reactions)
    .slice(0, 5)
    .map(i => ({
      title: i.title,
      issueNumber: i.number,
      reactions: i.reactions,
      likelihood: i.reactions > 20 ? "high" : i.reactions > 5 ? "medium" : "low",
      url: i.url,
      prediction: ""
    }));
}
```

---

## Important Rules

1. **Fallback mode** — If no AI API key is available, use buildFallback* functions listed above. These generate deterministic, rule-based output.
2. **Commit deduplication** — A single commit may appear in only ONE section. Breaking changes take priority.
3. **Empty state** — If there are no commits in a category, omit that section entirely (don't show "Features: none").
4. **Description trimming** — Commit messages are often long with PR references. Use only the first line (subject line) for descriptions. Append issue reference if available.
5. **Author attribution** — Every changelog item must have an `author` field. Use commit author login, fall back to "unknown".
