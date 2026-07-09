# Handoff Schemas — Cross-Agent Data Contracts

This document defines every agent-to-agent data transfer in the community intelligence pipeline. All agents MUST produce and consume data conforming to these schemas.

---

## Schema Index

| # | Schema | Producer | Consumer(s) | Description |
|---|--------|----------|-------------|-------------|
| 0 | `OrchestratorState` | SKILL.md | All agents | Runtime state: params + mode |
| 1 | `CollectorOutput` | Data Collector | Community Analyst, PR Reviewer, Direction Planner | All GitHub data |
| 2 | `CommunityMetrics` | Community Analyst | Direction Planner, Writer | Computed scores, trends, topics |
| 3 | `PRReviewOutput` | PR Reviewer | Formatter | Structured review output |
| 4 | `DirectionRecommendation` | Direction Planner | Formatter | Priority-ranked suggestions |
| 5 | `WriterOutput` | Writer | Formatter | Generated changelog sections |
| 6 | `FormatterInput` | Formatter | Quality Checker | Full output with markdown (mode-wrapped) |
| 7 | `QualityReport` | Quality Checker | SKILL.md | Validation results |
| 8 | `PreviousAnalysis` | SKILL.md | Direction Planner, Community Analyst | Trend data snapshot |

---

## 0. OrchestratorState

**Producer**: SKILL.md (PARSE_INPUT state)
**Consumer(s)**: All agents (read from `references/`)

```typescript
interface OrchestratorState {
  /** State machine position */
  state: "PARSE_INPUT" | "COLLECT_DATA" | "ANALYZE" | "REVIEW_PR" | "PLAN_DIRECTION" | "GENERATE_REPORT" | "QUALITY_CHECK" | "DONE" | "ERROR";
  /** What the user asked for */
  mode: "changelog" | "pr_review" | "direction" | "health";
  /** Repository identity (separate for GitHub API calls) */
  owner: string;
  repo: string;
  /** Git refs (for changelog mode) */
  fromRef?: string;
  toRef?: string;
  /** PR number (for pr_review mode) */
  prNumber?: number;
  /** Template style (for changelog mode) */
  template?: "community" | "technical" | "marketing";
  /** Error info */
  error?: string;
}
```

---

## 1. CollectorOutput

**Producer**: `agents/data_collector.md`
**Consumer(s)**: `agents/community_analyst.md`, `agents/pr_reviewer.md` (partial), `agents/direction_planner.md`

```typescript
interface CollectorOutput {
  /** Repository identity */
  owner: string;
  repo: string;

  // ── Changelog data (commits + issues) ──
  comparison?: {
    totalCommits: number;
    commits: RawGitHubCommit[];
    stats: { filesChanged: number; additions: number; deletions: number };
    status: string;
    aheadBy: number;
    /** First commit's date (ISO) for filtering closed issues */
    firstCommitDate: string;
  };

  // ── All issues (for analysis, direction) ──
  issues: RawGitHubIssue[];

  // ── Comments on issues/PRs (for sentiment, direction) ──
  issueComments: IssueComment[];
  prComments: PRReviewComment[];

  // ── PR data (for PR review) ──
  pullRequests?: PullRequestData[];

  // ── Discussions (GraphQL, optional) ──
  discussions?: DiscussionData[];

  // ── Error flags ──
  errors: {
    comparisonFailed: boolean;
    issuesFailed: boolean;
    commentsFailed: boolean;
    prsFailed: boolean;
    discussionsFailed: boolean;
  };
}
```

### 1a. RawGitHubCommit
```typescript
interface RawGitHubCommit {
  sha: string;
  commit: { message: string; author: { name: string; date: string }; committer: { name: string; date: string } };
  author: { login: string; avatar_url: string; html_url: string } | null;
  html_url: string;
  parents: { sha: string }[];
}
```

### 1b. RawGitHubIssue
```typescript
interface RawGitHubIssue {
  number: number;
  title: string;
  body: string;
  state: "open" | "closed";
  html_url: string;
  user: { login: string };
  labels: { name: string; color: string }[];
  comments: number;
  created_at: string;
  closed_at: string | null;
  reactions?: { "+1": number; "-1": number; laugh: number; heart: number; hooray: number; rocket: number; eyes: number; total_count: number };
}
```

### 1c. IssueComment
```typescript
interface IssueComment {
  id: number;
  issueNumber: number;
  body: string;
  user: { login: string };
  created_at: string;
  updated_at: string;
  reactions?: { total_count: number };
  author_association: string;
}
```

### 1d. PRReviewComment
```typescript
interface PRReviewComment {
  id: number;
  pullNumber: number;
  body: string;
  path: string;
  line: number;
  commit_id: string;
  diff_hunk: string;
  user: { login: string };
  created_at: string;
  reactions?: { total_count: number };
}
```

### 1e. PullRequestData
```typescript
interface PullRequestData {
  number: number;
  title: string;
  body: string;
  state: "open" | "closed" | "merged";
  html_url: string;
  user: { login: string };
  created_at: string;
  merged_at: string | null;
  draft: boolean;
  labels: { name: string }[];
  files: PRFile[];
  reviews: PRReview[];
  /** Commits in the PR (for change progression analysis) */
  commits: { sha: string; message: string; author: string; date: string }[];
}

interface PRFile {
  filename: string;
  status: "added" | "modified" | "removed" | "renamed";
  additions: number;
  deletions: number;
  changes: number;
  patch?: string;
  contents_url?: string;
}

interface PRReview {
  id: number;
  user: { login: string };
  body: string;
  state: "APPROVED" | "CHANGES_REQUESTED" | "COMMENTED" | "PENDING" | "DISMISSED";
  submitted_at: string;
}
```

### 1f. DiscussionData
```typescript
interface DiscussionData {
  number: number;
  title: string;
  body: string;
  category: { id: string; name: string; emoji: string };
  author: { login: string };
  createdAt: string;
  isAnswered: boolean;
  answer?: { body: string; author: { login: string } };
  comments: DiscussionComment[];
}

interface DiscussionComment {
  id: string;
  body: string;
  author: { login: string };
  createdAt: string;
  replies?: { body: string; author: { login: string }; createdAt: string }[];
}
```

---

## 2. CommunityMetrics

**Producer**: `agents/community_analyst.md`
**Consumer(s)**: `agents/direction_planner.md`, `agents/writer.md`

```typescript
interface CommunityMetrics {
  owner: string;
  repo: string;

  commits: EnrichedCommit[];
  enrichedIssues: EnrichedIssue[];
  openIssues: OpenIssueSummary[];

  commitCounts: {
    breaking: number; feat: number; fix: number; perf: number;
    chore: number; docs: number; refactor: number; test: number; other: number;
  };

  summary: {
    totalCommits: number; totalPRs: number; totalIssues: number;
    contributors: string[]; topContributor: string; dateRange: string;
    filesChanged: number; additions: number; deletions: number;
  };

  health: CommunityHealth;
  sentiment: SentimentSummary;
  trendingTopics: TopicCluster[];
  topCommunityIssues: EnrichedIssue[];
  contributorStats: ContributorStats;
}
```

### 2a. EnrichedCommit
```typescript
interface EnrichedCommit {
  sha: string; message: string; author: string;
  date: string; url: string; referencedIssues: number[];
  isBreaking: boolean; scope: string; type: string;
}
```

### 2b. EnrichedIssue
```typescript
interface EnrichedIssue {
  number: number; title: string; url: string;
  reactions: number; comments: number; labels: string[];
  body: string; author: string; createdAt: string;
  communityScore: number;
  typeHint?: "feature" | "bug" | "improvement";
  sentiment: "positive" | "neutral" | "negative";
  priorityScore: number;
}
```

### 2c. OpenIssueSummary
```typescript
interface OpenIssueSummary {
  number: number; title: string; url: string;
  reactions: number; labels: string[]; author: string;
  createdAt: string; commentCount: number; priorityScore: number;
}
```

### 2d. CommunityHealth
```typescript
interface CommunityHealth {
  score: number; // 0-100
  trend: "improving" | "stable" | "declining";
  issueResponseTimeP50: number; prReviewTimeP50: number;
  prMergeRate: number;
  activeContributors30d: number; newContributors30d: number;
  busFactor: number;
}
```

### 2e. SentimentSummary
```typescript
interface SentimentSummary {
  overallScore: number; // -1.0 to 1.0
  reactions: { positive: number; negative: number; neutral: number; total: number };
  mostPositive: { number: number; title: string; score: number }[];
  mostNegative: { number: number; title: string; score: number }[];
}
```

### 2f. TopicCluster
```typescript
interface TopicCluster {
  topic: string;
  frequency: number;
  totalReactions: number;
  sentiment: number;
  trend: "rising" | "stable" | "falling";
  relatedIssueNumbers: number[];
}
```

### 2g. ContributorStats
```typescript
interface ContributorStats {
  totalUnique: number;
  commitAuthors: number;
  firstTimeContributors: string[];
  mostActive: { login: string; contributions: number }[];
  newContributorCount: number;
}
```

---

## 3. PRReviewOutput

**Producer**: `agents/pr_reviewer.md`
**Consumer(s)**: `agents/formatter.md`

```typescript
interface PRReviewOutput {
  owner: string; repo: string; prNumber: number;
  summary: string;
  walkthrough: FileReview[];
  issues: ReviewIssue[];
  suggestions: string[];
  securityCheck: { passed: boolean; issues: string[] };
  verdict: "approve" | "changes_requested" | "comment";
}

interface FileReview {
  filename: string; status: string;
  notes: string; concerns: string[]; highlights: string[];
}

interface ReviewIssue {
  severity: "critical" | "high" | "medium" | "low";
  file: string; line: number;
  title: string; description: string; suggestion: string;
}
```

---

## 4. DirectionRecommendation

**Producer**: `agents/direction_planner.md`
**Consumer(s)**: `agents/formatter.md`

```typescript
interface DirectionRecommendation {
  owner: string; repo: string;
  topFeatures: PriorityItem[];
  topBugs: PriorityItem[];
  quickWins: PriorityItem[];
  strategicDirection: string;
  healthContext: { currentHealth: string; trend: string; keyRisks: string[] };
  communityMood: string;
  /** Resolution tracking from previous snapshot */
  previousResolution?: ResolvedItem[];
}

interface PriorityItem {
  title: string; issueNumber: number; url: string;
  priorityScore: number; reasoning: string;
  effort: "low" | "medium" | "high";
  communityDemand: string;
}

interface ResolvedItem {
  issueNumber: number;
  status: "resolved" | "still_open" | "not_found";
}

---

## 5. WriterOutput

**Producer**: `agents/writer.md`
**Consumer(s)**: `agents/formatter.md`

```typescript
interface WriterOutput {
  repo: string; fromRef: string; toRef: string;
  template: "community" | "technical" | "marketing";
  summary: {
    totalCommits: number; totalPRs: number; totalIssues: number;
    contributors: string[]; topContributor: string; dateRange: string;
    filesChanged: number; additions: number; deletions: number;
  };
  communityHighlights: CommunityHighlight[];
  categories: CategorySection[];
  roadmap: RoadmapItem[];
}

interface CommunityHighlight {
  title: string; issueNumber: number; url: string;
  reactions: number; description: string;
  type: "feature" | "bug" | "improvement";
  comments: number; requestedBy: string;
  communityImpact: string;
}

interface CategorySection {
  title: string; emoji: string; items: ChangelogItem[];
}

interface ChangelogItem {
  description: string; userBenefit?: string;
  issueOrPR?: number; author?: string; url?: string;
}

interface RoadmapItem {
  title: string; issueNumber: number; reactions: number;
  likelihood: "high" | "medium" | "low";
  url: string; prediction: string;
}
```

---

## 6. FormatterInput

**Producer**: `agents/formatter.md`
**Consumer(s)**: `agents/quality_checker.md`

```typescript
interface FormatterInput {
  repo: string;
  mode: "changelog" | "pr_review" | "direction" | "health";
  writerOutput?: WriterOutput;
  prReviewOutput?: PRReviewOutput;
  directionOutput?: DirectionRecommendation;
  healthOutput?: CommunityMetrics;
  rawMarkdown: string;
}
```

---

## 7. QualityReport

**Producer**: `agents/quality_checker.md`
**Consumer(s)**: SKILL.md

```typescript
interface QualityReport {
  passed: boolean;
  sections: {
    summary: { present: boolean; issues: string[] };
    content: { present: boolean; issues: string[] };
    markdown: { present: boolean; issues: string[] };
  };
  correctedOutput: FormatterInput;
  summary: string;
}
```

---

## 8. PreviousAnalysis

**Producer**: SKILL.md (DONE state, written to `references/previous_analysis.json`)
**Consumer(s)**: `agents/direction_planner.md`, `agents/community_analyst.md`

```typescript
interface PreviousAnalysis {
  /** Snapshot timestamp */
  createdAt: string;
  /** Commit SHA or tag at time of snapshot */
  snapshotRef?: string;

  // ── Metrics snapshot ──
  healthScore: number;
  sentimentScore: number;
  totalOpenIssues: number;
  totalOpenPRs: number;
  prMergeRate: number;
  activeContributors30d: number;

  // ── Topic snapshot ──
  topics: { topic: string; frequency: number; totalReactions: number }[];

  // ── Previous recommendations (for tracking resolution) ──
  recommendedIssueNumbers: number[];
  recommendedFeatureNumbers: number[];
  recommendedBugNumbers: number[];
}
```

---

## Validation Rules

| Schema | Rule | Action |
|--------|------|--------|
| `CollectorOutput` | At least one data source must succeed | Return error if ALL fail |
| `CommunityMetrics` | `summary.totalCommits == commits.length` | Re-count |
| `PRReviewOutput` | At least 1 file review item | Minimal placeholder |
| `DirectionRecommendation` | At least 3 total priority items | Inject fallback |
| `FormatterInput.rawMarkdown` | Non-empty string | Build minimal fallback |
