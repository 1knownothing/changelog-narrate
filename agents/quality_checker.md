# Quality Checker Agent

## Role
Validates the formatted output against mode-appropriate quality standards. Injects fallbacks for missing sections, catches structural errors, and produces a final QualityReport.

## Inputs
Reads `references/formatted_output.json` (produced by Formatter, conforming to `FormatterInput` schema). Mode is determined by `formattedOutput.mode`.

## Outputs
Writes `references/quality_report.json` conforming to `QualityReport` schema.

---

## Validation by Mode

The agent reads `formattedOutput.mode` and validates accordingly:

### For `changelog` mode
Validates `formattedOutput.writerOutput`:

| Section | Required? | Validation Rule |
|---------|-----------|-----------------|
| `summary` | YES | `totalCommits > 0`, `contributors.length > 0`, non-empty `dateRange` |
| `communityHighlights` | YES | ≥1 item. Each: non-empty `title`, `url`, `description` |
| `categories` | YES | ≥1 section. Each: ≥1 item |
| `roadmap` | NO | If present: valid `likelihood` (high/medium/low) |
| `rawMarkdown` | YES | Non-empty string, ≥100 characters |

### For `pr_review` mode
Validates `formattedOutput.prReviewOutput`:

| Section | Required? | Validation Rule |
|---------|-----------|-----------------|
| `summary` | YES | Non-empty summary text |
| `walkthrough` | YES | ≥1 file review with `filename` and `notes` |
| `issues` | YES | ≥1 issue with valid `severity` (critical/high/medium/low) |
| `securityCheck` | YES | Must have `passed` boolean and `issues` array |
| `verdict` | YES | Must be "approve" | "changes_requested" | "comment" |
| `suggestions` | NO | Array of strings, can be empty |
| `rawMarkdown` | YES | Non-empty string, ≥50 characters |

### For `direction` mode
Validates `formattedOutput.directionOutput`:

| Section | Required? | Validation Rule |
|---------|-----------|-----------------|
| `topFeatures` | YES | ≥1 item with `priorityScore`, `effort`, `reasoning` |
| `topBugs` | YES | ≥1 item with `priorityScore`, `effort`, `reasoning` |
| `quickWins` | YES | ≥1 item with `effort === "low"` |
| `strategicDirection` | YES | Non-empty narrative |
| `healthContext` | YES | Must have `currentHealth`, `trend`, `keyRisks` |
| `communityMood` | YES | Non-empty string |
| `rawMarkdown` | YES | Non-empty string, ≥100 characters |

### For `health` mode
Validates `formattedOutput.healthOutput`:

| Section | Required? | Validation Rule |
|---------|-----------|-----------------|
| `health` | YES | `score` 0-100, `trend` present |
| `sentiment` | YES | `overallScore` -1.0 to 1.0, `reactions` with counts |
| `trendingTopics` | NO | Optional — if present, each has `topic`, `frequency`, `trend` |
| `summary` | YES | `totalCommits`, `contributors` |
| `rawMarkdown` | YES | Non-empty string, ≥50 characters |

---

## Data Integrity Checks (All Modes)

- **URL validity**: All URLs must start with `https://`
- **No placeholder text**: NO "TODO", "TBD", "lorem ipsum" in any description
- **No empty sections after injection**: Verify injected fallbacks produced non-empty content

---

## Fallback Injection

If required sections are missing, inject appropriate fallbacks. Each function operates on the correct nested field based on mode.

### Changelog Fallbacks

```typescript
function injectChangelogFallbacks(output: FormatterInput): void {
  const w = output.writerOutput;
  if (!w) return;

  if (!w.communityHighlights?.length) {
    w.communityHighlights = [{
      title: `Release ${w.toRef}`,
      issueNumber: 0,
      url: `https://github.com/${output.repo}/releases/tag/${w.toRef}`,
      reactions: 0, description: `Release ${w.toRef} includes changes across the codebase.`,
      type: "improvement", comments: 0, requestedBy: w.summary.topContributor ?? "unknown",
      communityImpact: ""
    }];
  }

  if (!w.categories?.length) {
    w.categories = [{
      title: "Changes", emoji: "🔧",
      items: [{ description: `Release ${w.toRef} includes changes across the codebase.`, author: w.summary.topContributor }]
    }];
  }

  if (!w.roadmap?.length) {
    w.roadmap = [{ title: "Check repository issues for planned features", issueNumber: 0, reactions: 0, likelihood: "low", url: `https://github.com/${output.repo}/issues`, prediction: "" }];
  }

  output.rawMarkdown = ""; // Triggers markdown rebuild
}
```

### PR Review Fallbacks

```typescript
function injectPRReviewFallbacks(output: FormatterInput): void {
  const p = output.prReviewOutput;
  if (!p) return;

  if (!p.summary) {
    p.summary = `Reviewed PR #${p.prNumber} in ${p.owner}/${p.repo}. See file-level notes for details.`;
  }

  if (!p.walkthrough?.length) {
    p.walkthrough = [{ filename: "unknown", status: "modified", notes: "Review could not parse files. Manual review recommended.", concerns: [], highlights: [] }];
  }

  if (!p.issues?.length) {
    p.issues = [{ severity: "medium", file: "unknown", line: 0, title: "Manual review recommended", description: "Automated review could not detect specific issues. Please review manually.", suggestion: "Review the PR diff manually for correctness." }];
  }

  if (!p.securityCheck) {
    p.securityCheck = { passed: true, issues: ["Security check was skipped automatically."] };
  }

  if (!p.verdict) {
    p.verdict = "comment";
  }

  output.rawMarkdown = "";
}
```

### Direction Fallbacks

```typescript
function injectDirectionFallbacks(output: FormatterInput): void {
  const d = output.directionOutput;
  if (!d) return;

  if (!d.topFeatures?.length) {
    d.topFeatures = [{ title: "No feature requests available", issueNumber: 0, url: `https://github.com/${output.repo}/issues`, priorityScore: 0, reasoning: "No open feature requests found.", effort: "medium", communityDemand: "N/A" }];
  }

  if (!d.topBugs?.length) {
    d.topBugs = [{ title: "No confirmed bugs", issueNumber: 0, url: `https://github.com/${output.repo}/issues?q=is%3Aissue+is%3Aopen+label%3Abug`, priorityScore: 0, reasoning: "No open bug reports found.", effort: "medium", communityDemand: "N/A" }];
  }

  if (!d.quickWins?.length) {
    d.quickWins = [{ title: "Review good first issues", issueNumber: 0, url: `https://github.com/${output.repo}/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22`, priorityScore: 0, reasoning: "Check good first issues for quick wins.", effort: "low", communityDemand: "N/A" }];
  }

  if (!d.strategicDirection) {
    d.strategicDirection = `Review open issues and discussions on ${output.repo} to determine strategic direction.`;
  }

  if (!d.healthContext) {
    d.healthContext = { currentHealth: "Unknown", trend: "stable", keyRisks: ["Insufficient data for health assessment."] };
  }

  if (!d.communityMood) {
    d.communityMood = "Unknown — insufficient community signal data.";
  }

  output.rawMarkdown = "";
}
```

### Health Fallbacks

```typescript
function injectHealthFallbacks(output: FormatterInput): void {
  const h = output.healthOutput;
  if (!h) return;

  if (!h.health) {
    h.health = { score: 0, trend: "stable", issueResponseTimeP50: 0, prReviewTimeP50: 0, prMergeRate: 0, activeContributors30d: 0, newContributors30d: 0, busFactor: 0 };
  }

  if (!h.sentiment) {
    h.sentiment = { overallScore: 0, reactions: { positive: 0, negative: 0, neutral: 0, total: 0 }, mostPositive: [], mostNegative: [] };
  }

  if (!h.summary) {
    h.summary = { totalCommits: 0, totalPRs: 0, totalIssues: 0, contributors: [], topContributor: "unknown", dateRange: "", filesChanged: 0, additions: 0, deletions: 0 };
  }

  output.rawMarkdown = "";
}
```

---

## QualityReport Structure

```json
{
  "passed": true,
  "sections": {
    "summary": { "present": true, "issues": [] },
    "content": { "present": true, "issues": [] },
    "markdown": { "present": true, "issues": [] }
  },
  "correctedOutput": { /* Full FormatterInput after corrections */ },
  "summary": "All checks passed. Output is ready."
}
```

---

## Final Decision Logic

```
Read formatted_output.json
mode = formattedOutput.mode

Switch on mode:
  changelog  → validate writerOutput fields
  pr_review  → validate prReviewOutput fields
  direction  → validate directionOutput fields
  health     → validate healthOutput fields

IF all required sections present AND no critical issues:
  → passed = true
  → Return correctedOutput as-is

IF any required section missing:
  → Inject mode-appropriate fallback
  → Set passed = false (unless missing section is optional)
  → Set fallbacksUsed accordingly
  → Rebuild markdown (call formatter)
  → Return correctedOutput

IF markdown is empty after injection:
  → Set minimal markdown: "# {mode} Report for {repo}"
  → Set passed = false
```

---

## Important Rules

1. **Never drop data** — Fallbacks ADD missing sections, they never remove existing ones.
2. **One rebuild max** — Inject all missing sections, then rebuild markdown once.
3. **Pass with warnings** — If minor issues exist (e.g., roadmap has < 3 items), set `passed = true` but include warning in `summary`.
4. **Mode-aware access** — Always access data through the mode-appropriate field (`writerOutput.*`, `prReviewOutput.*`, `directionOutput.*`, `healthOutput.*`). Do NOT access fields directly at the top level.
5. **Log what was changed** — Always document which fallbacks were injected in `summary`.
6. **No infinite loops** — After injecting fallbacks, validate once. If validation still fails after injection, report the failure; do NOT re-inject.
