# Data Collector Agent

**Replaces**: `data_fetcher.md`

## Role
Fetches all relevant GitHub data for a repository based on the current mode. Each mode fetches only what it needs (lazy collection).

## Inputs
Reads `references/orchestrator_state.json` for `{ owner, repo, mode, fromRef, toRef, prNumber }`.

## Outputs
Writes `references/collector_output.json` conforming to `CollectorOutput` schema.

---

## Data Fetching by Mode

### Mode: `changelog`
| Endpoint | Purpose |
|----------|---------|
| `GET /repos/{o}/{r}/compare/{from}...{to}` | Commits + stats |
| `GET /repos/{o}/{r}/issues?state=open&sort=reactions` | Open issues for roadmap |
| `GET /repos/{o}/{r}/issues?state=closed&since={firstDate}` | Closed issues for highlights |

### Mode: `pr_review`
| Endpoint | Purpose |
|----------|---------|
| `GET /repos/{o}/{r}/pulls/{pr}` | PR metadata (title, body, author, state, commits count) |
| `GET /repos/{o}/{r}/pulls/{pr}/commits` | PR commits (for change progression analysis) |
| `GET /repos/{o}/{r}/pulls/{pr}/files` | Changed files with diffs |
| `GET /repos/{o}/{r}/pulls/{pr}/comments` | Inline review comments |
| `GET /repos/{o}/{r}/issues/{pr}/comments` | PR timeline comments |
| `GET /repos/{o}/{r}/pulls/{pr}/reviews` | Review summaries (approvals/rejections) |

### Mode: `direction`
| Endpoint | Purpose |
|----------|---------|
| `GET /repos/{o}/{r}/issues?state=open&sort=reactions` | Most requested features |
| `GET /repos/{o}/{r}/issues?state=closed&sort=updated` | Recently resolved |
| `GET /repos/{o}/{r}/issues/{n}/comments` (per top issue) | Community discussion |
| `GET /repos/{o}/{r}/pulls?state=open` | Open PRs (what's in flight) |
| `POST /api.github.com/graphql` (optional) | Discussions data |

### Mode: `health`
| Endpoint | Purpose |
|----------|---------|
| `GET /repos/{o}/{r}/issues?state=all&sort=created&per_page=100` | Issue flow |
| `GET /repos/{o}/{r}/pulls?state=all&sort=updated&per_page=100` | PR flow |
| `GET /repos/{o}/{r}/stats/commit_activity` | Commit cadence |
| `GET /repos/{o}/{r}/contributors?per_page=1` | Total contributor count |

---

## GitHub GraphQL for Discussions

For any mode that includes discussions (direction mode), use `webfetch` to POST to the GraphQL API:

**Endpoint**: `POST https://api.github.com/graphql`
**Headers**: `Authorization: Bearer {token if available}`
**Body**:
```graphql
query {
  repository(owner: "OWNER", name: "REPO") {
    discussions(first: 50, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        number
        title
        body
        category { name emoji }
        author { login }
        createdAt
        isAnswered
        comments(first: 20) {
          nodes { id body author { login } createdAt }
        }
      }
    }
  }
}
```

**⚠️ Variable substitution**: Replace `OWNER` and `REPO` in the query with actual `owner` and `repo` from `orchestrator_state.json`. Simple string replacement before sending.

**⚠️ Note**: GraphQL has separate rate limits (5000 points/hr, this query costs ~1 point). If the call fails, set `discussionsFailed: true` and continue without discussions data.

---

## Field Mapping (GitHub API → Schema)

| API Response Field | Schema Field | Notes |
|--------------------|-------------|-------|
| `total_commits` | `comparison.totalCommits` | Snake_case → camelCase |
| `files` (root array) | `comparison.stats.filesChanged` | `files?.length` |
| `stats.additions` | `comparison.stats.additions` | Direct |
| `stats.deletions` | `comparison.stats.deletions` | Direct |
| `commits[last].commit.author.date` | `comparison.firstCommitDate` | Oldest commit date |
| `issue.pull_request` (exists) | → filter out (it's a PR) | Always check |
| `reactions.total_count` | `reactions.total_count` | On issues/comments |

---

## Error Handling

- Each data source sets its own error flag in `errors.*`
- A failed data source = empty array for that field, NOT a pipeline failure
- Pipeline only stops if ALL data sources for the current mode fail
- Rate limiting: check `x-ratelimit-remaining` header. If < 100, add 2-second delay between requests
- Pagination: follow `Link` header, max 3 pages (300 items) per endpoint

---

## Write-Back Capabilities (POST to GitHub)

The Data Collector can also WRITE data back to GitHub after user confirmation. These are gated by the orchestrator — the Data Collector only performs writes when explicitly told to.

### Create an Issue

**Endpoint**: `POST /repos/{o}/{r}/issues`
**Body**:
```json
{
  "title": "string",
  "body": "string (markdown)",
  "labels": ["string"]
}
```
**Response**: Created issue object with `html_url` and `number`.

**Usage**: Direction Planner's recommendations can be turned into tracking issues. SKILL.md asks user "Create tracking issues for these recommendations?" before dispatching.

### Post a PR Review Comment

**Endpoint**: `POST /repos/{o}/{r}/pulls/{n}/comments`
**Body**:
```json
{
  "body": "string (markdown review body)",
  "commit_id": "string",
  "path": "string",
  "line": 0
}
```
**Usage**: PR Reviewer's output can be posted as a PR review. Only when user confirms.

### Close/Reopen an Issue

**Endpoint**: `PATCH /repos/{o}/{r}/issues/{n}`
**Body**:
```json
{
  "state": "closed"
}
```
**Usage**: Mark resolved recommendations as closed (optional, user confirmation required).

---

## Important Rules
1. **Filter out PRs from issue endpoints** — check `pull_request` field
2. **Handle GraphQL errors gracefully** — if GraphQL call fails, set `discussionsFailed` and continue
3. **Conditional requests** — use `If-None-Match`/`If-Modified-Since` with fresh ETags to save rate limit
4. **Don't fetch unnecessary data** — only fetch endpoints needed for the current mode
5. **Null safety** — `author.login` can be null → fallback to `"unknown"`
6. **Write-back requires confirmation** — Never POST to GitHub without user confirmation. Write-back is triggered by SKILL.md, not autonomously.
