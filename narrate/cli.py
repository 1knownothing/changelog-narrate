#!/usr/bin/env python3
"""
changelog-release-notes orchestrator
One command, full pipeline: fetch -> analyze -> write -> format -> verify

Usage:
  python orchestrator.py owner/repo --from master@{7day} --to master
  python orchestrator.py owner/repo --from v1.0 --to v2.0 --template technical
  python orchestrator.py owner/repo --from HEAD~4 --to HEAD --skip-quality

Optional env vars:
  GITHUB_TOKEN=<token>     # Higher API rate limit (5,000 req/h vs 60)
  DEEPSEEK_API_KEY=<key>   # AI-powered writer (better quality output)
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF_DIR = os.path.join(BASE_DIR, "references")
GITHUB_API = "https://api.github.com"


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    eprint(f"  wrote {os.path.relpath(path, BASE_DIR)}")


def github_get(path, token=None):
    url = f"{GITHUB_API}{path}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "changelog-orchestrator/1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        eprint(f"  GitHub API error {e.code} on {path}: {body[:200]}")
        raise


def fmt_date(iso_str):
    if not iso_str:
        return ""
    d = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return d.strftime("%Y-%m-%d")


def fmt_date_range(first, last):
    if not first or not last:
        return ""
    return f"{fmt_date(first)} to {fmt_date(last)}"


def parse_conventional_commit(message):
    m = re.match(r'^(\w+)(?:\(([^)]*)\))?(!)?\s*:\s*(.*)', message)
    if not m:
        return {"type": "other", "scope": None, "description": message, "breaking": False}
    return {
        "type": m.group(1).lower(),
        "scope": m.group(2),
        "description": m.group(4).strip(),
        "breaking": m.group(3) == "!" or "BREAKING CHANGE" in message,
    }


def extract_pr_number(message):
    m = re.search(r'#(\d+)', message)
    return int(m.group(1)) if m else None


def enrich_commits(commits_raw):
    enriched = []
    for c in commits_raw:
        sha = c.get("sha", "")
        msg = c.get("commit", {}).get("message", "")
        author = c.get("author", {})
        author_login = author.get("login") if author else None
        author_name = c.get("commit", {}).get("author", {}).get("name", "unknown")
        date = c.get("commit", {}).get("author", {}).get("date", "")
        parsed = parse_conventional_commit(msg)
        enriched.append({
            "sha": sha,
            "message": msg,
            "description": parsed["description"],
            "type": parsed["type"],
            "scope": parsed["scope"],
            "isBreaking": parsed["breaking"],
            "author": author_login or author_name,
            "authorName": author_name,
            "date": date,
            "url": c.get("html_url", ""),
            "issueOrPR": extract_pr_number(msg),
        })
    return enriched


def enrich_issues(issues_raw, repo_url):
    enriched = []
    for issue in issues_raw:
        if "pull_request" in issue:
            continue
        enriched.append({
            "number": issue.get("number"),
            "title": issue.get("title", ""),
            "body": issue.get("body", "") or "",
            "url": issue.get("html_url", f"{repo_url}/issues/{issue.get('number')}"),
            "state": issue.get("state", "open"),
            "author": issue.get("user", {}).get("login", "unknown"),
            "labels": [l.get("name", "") for l in issue.get("labels", [])],
            "reactions": issue.get("reactions", {}).get("total_count", 0),
            "comments": issue.get("comments", 0),
            "createdAt": issue.get("created_at", ""),
            "communityScore": (issue.get("reactions", {}).get("total_count", 0) or 0) * 2 + (issue.get("comments", 0) or 0),
        })
    return enriched


def infer_impact(reactions):
    if reactions >= 20:
        return f"This is a highly requested feature with {reactions} reactions from the community. Implementing it would directly address a top user need and improve satisfaction for a significant portion of users."
    elif reactions >= 10:
        return f"With {reactions} reactions, this is a meaningful improvement that many users have been waiting for. It addresses a real pain point in the daily workflow."
    elif reactions >= 5:
        return f"This improvement has garnered {reactions} reactions, indicating genuine community interest. It's a thoughtful enhancement that makes the tool more approachable."
    return f"Even with {reactions} reactions, this issue represents a real user pain point. Every fix makes the ecosystem healthier for everyone."


def step_parse_input(owner, repo, from_ref, to_ref, template, output_dir):
    state = {
        "state": "PARSE_INPUT",
        "mode": "changelog",
        "owner": owner,
        "repo": repo,
        "fromRef": from_ref,
        "toRef": to_ref,
        "template": template,
    }
    write_json(os.path.join(output_dir, "orchestrator_state.json"), state)
    return state


def step_collect_data(owner, repo, from_ref, to_ref, token, output_dir):
    eprint("  [2a] Fetching comparison...")
    comp = github_get(f"/repos/{owner}/{repo}/compare/{from_ref}...{to_ref}", token)

    commits_raw = comp.get("commits", [])
    stats = {"filesChanged": 0, "additions": 0, "deletions": 0}
    if "stats" in comp:
        stats = {
            "filesChanged": comp["stats"].get("files", 0),
            "additions": comp["stats"].get("additions", 0),
            "deletions": comp["stats"].get("deletions", 0),
        }
    files = comp.get("files", [])
    if isinstance(files, list) and len(files) > 0:
        stats["filesChanged"] = len(files)
        stats["additions"] = sum(f.get("additions", 0) for f in files)
        stats["deletions"] = sum(f.get("deletions", 0) for f in files)

    comparison = {
        "totalCommits": comp.get("total_commits", len(commits_raw)),
        "firstCommitDate": commits_raw[0]["commit"]["author"]["date"] if commits_raw else None,
        "stats": stats,
        "commits": commits_raw,
    }

    eprint("  [2b] Fetching top open issues...")
    try:
        open_issues = github_get(
            f"/repos/{owner}/{repo}/issues?state=open&sort=reactions&direction=desc&per_page=30&page=1",
            token,
        )
    except urllib.error.HTTPError:
        open_issues = []

    if comparison["firstCommitDate"]:
        since = fmt_date(comparison["firstCommitDate"])
        eprint(f"  [2c] Fetching closed issues since {since}...")
        try:
            closed_issues = github_get(
                f"/repos/{owner}/{repo}/issues?state=closed&since={since}T00:00:00Z&per_page=100&page=1",
                token,
            )
        except urllib.error.HTTPError:
            closed_issues = []
    else:
        closed_issues = []

    collector_output = {
        "comparison": comparison,
        "openIssues": open_issues,
        "closedIssues": closed_issues,
    }
    write_json(os.path.join(output_dir, "collector_output.json"), collector_output)
    return collector_output


def step_analyze(collector_output, owner, repo):
    comparison = collector_output["comparison"]
    commits_raw = comparison.get("commits", [])
    open_issues_raw = collector_output.get("openIssues", [])
    closed_issues_raw = collector_output.get("closedIssues", [])

    repo_url = f"https://github.com/{owner}/{repo}"
    all_contributors = set()

    enriched_commits = enrich_commits(commits_raw)
    for c in enriched_commits:
        all_contributors.add(c["author"])

    enriched_open = enrich_issues(open_issues_raw, repo_url)
    enriched_closed = enrich_issues(closed_issues_raw, repo_url)

    referenced_nums = set()
    for c in enriched_commits:
        if c["issueOrPR"]:
            referenced_nums.add(c["issueOrPR"])
        for n in re.findall(r'#(\d+)', c["message"]):
            referenced_nums.add(int(n))

    cross_refs = [i for i in enriched_closed if i["number"] in referenced_nums]

    stats = comparison.get("stats", {})
    first_date = enriched_commits[0]["date"] if enriched_commits else ""
    last_date = enriched_commits[-1]["date"] if enriched_commits else ""

    contributor_counts = defaultdict(int)
    for c in enriched_commits:
        contributor_counts[c["author"]] += 1
    top = sorted(contributor_counts.items(), key=lambda x: -x[1])
    top_contributor = top[0][0] if top else "unknown"

    top_highlights = sorted(cross_refs, key=lambda x: -x["communityScore"])[:5]
    if len(top_highlights) < 3:
        remaining = sorted(
            [i for i in enriched_closed if i not in top_highlights],
            key=lambda x: -x["communityScore"],
        )[:5 - len(top_highlights)]
        top_highlights.extend(remaining)

    return {
        "repo": f"{owner}/{repo}",
        "mode": "changelog",
        "summary": {
            "totalCommits": len(enriched_commits),
            "totalIssues": len(enriched_closed),
            "contributors": list(all_contributors),
            "topContributor": top_contributor,
            "dateRange": fmt_date_range(first_date, last_date),
            "filesChanged": stats.get("filesChanged", 0),
            "additions": stats.get("additions", 0),
            "deletions": stats.get("deletions", 0),
        },
        "categorized": {k: len(v) for k, v in {
            "breaking": [c for c in enriched_commits if c["isBreaking"]],
            "features": [c for c in enriched_commits if c["type"] == "feat" and not c["isBreaking"]],
            "fixes": [c for c in enriched_commits if c["type"] == "fix"],
        }.items()},
        "commits": enriched_commits,
        "openIssues": enriched_open,
        "closedIssues": enriched_closed,
        "crossReferencedIssues": cross_refs,
        "communityHighlights": top_highlights,
    }


def _template_writer(summary, commits, highlights_data, open_issues, repo_short, template):
    community_highlights = []
    for h in highlights_data[:5]:
        labels_lower = [l.lower() for l in h.get("labels", [])]
        if any("bug" in l for l in labels_lower):
            htype = "bug"
        elif any(l in ("enhancement", "feature", "feat") for l in labels_lower):
            htype = "feature"
        else:
            htype = "improvement"
        body = h.get("body") or ""
        first_para = ""
        for line in body.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("###") and len(stripped) > 20:
                first_para = stripped[:300]
                break
        if not first_para:
            first_para = (body.strip() or "Community-requested improvement.")[:300]
        community_highlights.append({
            "title": h["title"],
            "issueNumber": h["number"],
            "url": h["url"],
            "reactions": h["reactions"],
            "description": first_para,
            "type": htype,
            "comments": h["comments"],
            "requestedBy": h["author"],
            "communityImpact": infer_impact(h["reactions"]),
        })

    sections = defaultdict(list)
    for c in commits:
        item = {
            "description": (c["description"] or c["message"].split("\n")[0])[:200],
            "author": c["author"],
            "url": c["url"],
            "userBenefit": "",
        }
        if c["issueOrPR"]:
            item["issueOrPR"] = c["issueOrPR"]
        if c["isBreaking"]:
            sections["breaking"].append(item)
        elif c["type"] == "feat":
            sections["features"].append(item)
        elif c["type"] == "fix":
            sections["fixes"].append(item)
        elif c["type"] == "perf":
            sections["perf"].append(item)
        else:
            sections["other"].append(item)

    categories = []
    if sections["breaking"]:
        categories.append({"title": "Breaking Changes", "emoji": "⚠️", "items": sections["breaking"][:10]})
    if sections["features"]:
        categories.append({"title": "New Features", "emoji": "✨", "items": sections["features"][:20]})
    if sections["fixes"]:
        categories.append({"title": "Bug Fixes", "emoji": "🛠️", "items": sections["fixes"][:15]})
    if sections["perf"]:
        categories.append({"title": "Performance", "emoji": "⚡", "items": sections["perf"][:10]})
    if sections["other"]:
        categories.append({"title": "Other Improvements", "emoji": "🔧", "items": sections["other"][:10]})

    roadmap = []
    for i in open_issues[:5]:
        reactions = i.get("reactions", {})
        total = reactions.get("total_count", 0) if isinstance(reactions, dict) else (reactions or 0)
        likelihood = "high" if total > 20 else ("medium" if total > 5 else "low")
        roadmap.append({
            "title": i.get("title", ""),
            "issueNumber": i.get("number"),
            "reactions": total,
            "likelihood": likelihood,
            "url": i.get("url") or i.get("html_url", ""),
            "prediction": (
                "This is a top community priority. Expected to ship in an upcoming release."
                if likelihood == "high" else
                "Under active consideration, timeline depends on prioritization."
                if likelihood == "medium" else
                "Tracking this issue. Community interest will help prioritize."
            ),
        })

    return {
        "repo": repo_short,
        "template": template,
        "summary": summary,
        "communityHighlights": community_highlights,
        "categories": categories,
        "roadmap": roadmap,
    }


def _ai_writer(analyzer_output, template, api_key):
    summary = analyzer_output["summary"]
    commits = analyzer_output["commits"]
    open_issues = analyzer_output["openIssues"]
    closed_issues = analyzer_output["closedIssues"]
    repo = analyzer_output["repo"]

    breaking = [c for c in commits if c["isBreaking"]]
    features = [c for c in commits if c["type"] == "feat" and not c["isBreaking"]]
    fixes = [c for c in commits if c["type"] == "fix"]
    others = [c for c in commits if not c["isBreaking"] and c["type"] not in ("feat", "fix")]

    top_closed = sorted(closed_issues, key=lambda i: i.get("communityScore", 0), reverse=True)[:10]
    resolved_nums = {c["issueOrPR"] for c in commits if c.get("issueOrPR")}

    def fmt(i):
        return i["message"].split("\n")[0]

    prompt = f"""Generate {template}-style release notes for the following software release.

Repository: {repo}
Style: {template}

=== STATS ===
{summary['filesChanged']} files changed, +{summary['additions']} -{summary['deletions']}

=== BREAKING CHANGES ({len(breaking)}) ===
{chr(10).join(f"- [{c['sha'][:7]}] {fmt(c)} ({c['author']})" for c in breaking[:10]) or "(none)"}

=== FEATURES ({len(features)}) ===
{chr(10).join(f"- [{c['sha'][:7]}] {fmt(c)} ({c['author']})" for c in features[:30]) or "(none)"}

=== BUG FIXES ({len(fixes)}) ===
{chr(10).join(f"- [{c['sha'][:7]}] {fmt(c)} ({c['author']})" for c in fixes[:20]) or "(none)"}

=== OTHER ({len(others)}) ===
{chr(10).join(f"- [{c['sha'][:7]}] {fmt(c)} ({c['author']})" for c in others[:10]) or "(none)"}

=== TOP COMMUNITY ISSUES ===
{chr(10).join(f"- #{i['number']}: {i['title']} (community score: {i.get('communityScore',0)})" for i in top_closed[:5]) or "(none)"}

=== TOP OPEN ISSUES ===
{chr(10).join(f"- #{i['number']}: {i['title']} (reactions: {i.get('reactions',{}).get('total_count',0) if isinstance(i.get('reactions'), dict) else i.get('reactions',0)})" for i in open_issues[:5]) or "(none)"}

Output JSON format:
{{
  "communityHighlights": [
    {{ "title": "...", "issueNumber": 123, "type": "feature|bug|improvement", "description": "...", "reactions": 10, "comments": 5, "requestedBy": "...", "communityImpact": "..." }}
  ],
  "categories": [
    {{ "title": "New Features", "emoji": "✨", "items": [{{"description": "...", "userBenefit": "...", "issueOrPR": 123, "author": "..."}}] }},
    {{ "title": "Bug Fixes", "emoji": "🛠️", "items": [...] }},
    {{ "title": "Other Improvements", "emoji": "🔧", "items": [...] }}
  ],
  "roadmap": [
    {{ "title": "...", "issueNumber": 123, "reactions": 10, "likelihood": "high|medium|low", "url": "...", "prediction": "..." }}
  ]
}}

Return ONLY valid JSON inside a ```json code block."""

    payload = json.dumps({
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": f"You are a world-class Developer Relations engineer. Style: {template}."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 6000,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.deepseek.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
    )

    eprint("  [4] Calling DeepSeek API...")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        m = re.search(r'```json\s*([\s\S]*?)\s*```', content)
        ai_result = json.loads(m.group(1)) if m else json.loads(re.search(r'\{[\s\S]*\}', content).group(0))
        return {
            "repo": repo,
            "template": template,
            "summary": summary,
            "communityHighlights": ai_result.get("communityHighlights", []),
            "categories": ai_result.get("categories", []),
            "roadmap": ai_result.get("roadmap", []),
        }
    except Exception as e:
        eprint(f"  AI writer failed: {e}. Falling back to template.")
        return None


def step_write(analyzer_output, template, deepseek_key):
    summary = analyzer_output["summary"]
    commits = analyzer_output["commits"]
    highlights_data = analyzer_output["communityHighlights"]
    open_issues = analyzer_output["openIssues"]
    closed_issues = analyzer_output["closedIssues"]
    repo_short = analyzer_output["repo"].split("/")[1]

    writer_output = None
    if deepseek_key:
        writer_output = _ai_writer(analyzer_output, template, deepseek_key)

    if not writer_output:
        writer_output = _template_writer(summary, commits, highlights_data, open_issues, repo_short, template)
    return writer_output


def step_format(writer_output, owner, repo, from_ref, to_ref, output_dir):
    summary = writer_output["summary"]
    highlights = writer_output["communityHighlights"]
    categories = writer_output["categories"]
    roadmap = writer_output["roadmap"]

    lines = []
    lines.append(f"# {repo} {to_ref}")
    lines.append("")
    lines.append(f"**{summary['totalCommits']}** commits · **{summary['totalIssues']}** issues resolved · **{len(summary['contributors'])}** contributors")
    lines.append(f"{summary.get('dateRange', '')} · {summary['filesChanged']} files · +{summary['additions']} -{summary['deletions']}")
    lines.append("")

    if highlights:
        lines.append("## Community Highlights")
        lines.append("")
        for h in highlights:
            type_badge = {"feature": "New", "bug": "Fixed", "improvement": "Improved"}.get(h.get("type", ""), "Improved")
            lines.append(f"### {type_badge}: {h['title']}")
            lines.append("")
            lines.append(f"[#{h['issueNumber']}]({h['url']}) · {h['reactions']} reactions · {h.get('comments', 0)} comments · by @{h.get('requestedBy', 'community')}")
            lines.append("")
            lines.append(f"> {h.get('description', 'No description available.')}")
            if h.get("communityImpact"):
                lines.append("")
                lines.append(f"**Impact:** {h['communityImpact']}")
            lines.append("")

    for cat in categories:
        if not cat.get("items"):
            continue
        lines.append(f"## {cat.get('emoji', '')} {cat['title']}")
        lines.append("")
        for item in cat["items"]:
            by = f" (@{item['author']})" if item.get("author") else ""
            parts = [f"- **{item['description']}**"]
            if item.get("issueOrPR"):
                parts.append(f"[#{item['issueOrPR']}](https://github.com/{owner}/{repo}/pull/{item['issueOrPR']})")
            if item.get("url"):
                parts.append(f"[link]({item['url']})")
            parts[-1] += by
            lines.append(" ".join(parts))
            if item.get("userBenefit"):
                lines.append(f"  *{item['userBenefit']}*")
        lines.append("")

    if roadmap:
        lines.append("## What's Next")
        lines.append("")
        for r in roadmap:
            badge = {"high": "High Priority", "medium": "In Discussion", "low": "On Radar"}.get(r.get("likelihood", "low"), "On Radar")
            lines.append(f"- **[{badge}]** {r['title']} ([#{r['issueNumber']}]({r.get('url', '#')}))")
            if r.get("prediction"):
                lines.append(f"  {r['prediction']}")
        lines.append("")

    lines.append("---")
    lines.append(f"Full changelog: https://github.com/{owner}/{repo}/compare/{from_ref}...{to_ref}")

    formatted = {
        "repo": f"{owner}/{repo}",
        "mode": "changelog",
        "writerOutput": writer_output,
        "rawMarkdown": "\n".join(lines),
    }
    write_json(os.path.join(output_dir, "formatted_output.json"), formatted)
    return formatted


def step_quality_check(formatted_output, output_dir):
    writer_output = formatted_output.get("writerOutput", {})
    raw_md = formatted_output.get("rawMarkdown", "")
    summary = writer_output.get("summary", {})

    s_issues, c_issues, m_issues = [], [], []

    if summary.get("totalCommits", 0) <= 0:
        s_issues.append("totalCommits is 0 or missing")
    if not summary.get("contributors"):
        s_issues.append("contributors list is empty")

    highlights = writer_output.get("communityHighlights", [])
    if len(highlights) == 0:
        c_issues.append("no community highlights")
    for h in highlights:
        if not h.get("title"):
            c_issues.append("highlight missing title")

    categories = writer_output.get("categories", [])
    total_items = sum(len(c.get("items", [])) for c in categories)
    if total_items == 0:
        c_issues.append("all categories are empty")

    for r in writer_output.get("roadmap", []):
        if r.get("likelihood") not in ("high", "medium", "low"):
            c_issues.append(f"invalid likelihood: {r.get('likelihood')}")

    if len(raw_md) < 100:
        m_issues.append("markdown too short")
    if "TODO" in raw_md or "TBD" in raw_md:
        m_issues.append("placeholder text found")
    if raw_md.count("https://") == 0:
        m_issues.append("no URLs in markdown")

    passed = len(s_issues) == 0 and len(c_issues) == 0 and len(m_issues) == 0
    report = {
        "passed": passed,
        "sections": {
            "summary": {"present": len(s_issues) == 0, "issues": s_issues},
            "content": {"present": len(c_issues) == 0, "issues": c_issues},
            "markdown": {"present": len(m_issues) == 0, "issues": m_issues},
        },
        "correctedOutput": formatted_output,
        "summary": "All checks passed." if passed else f"Issues: {len(s_issues) + len(c_issues) + len(m_issues)} problem(s).",
    }
    write_json(os.path.join(output_dir, "quality_report.json"), report)
    return report


def main():
    parser = argparse.ArgumentParser(
        description="One-command release notes from git history.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repo", help="owner/name format (e.g., ohmyzsh/ohmyzsh)")
    parser.add_argument("--from", dest="from_ref", required=True)
    parser.add_argument("--to", dest="to_ref", required=True)
    parser.add_argument("--template", choices=["community", "technical", "marketing"], default="community")
    parser.add_argument("--output", "-o", default=REF_DIR)
    parser.add_argument("--skip-quality", action="store_true")
    parser.add_argument("--print", dest="print_output", action="store_true")
    parser.add_argument("--json-only", action="store_true",
                        help="Stop after ANALYZE step, output structured JSON. "
                             "Use this when the AI in your coding tool (opencode, Claude Code) "
                             "will write the changelog itself.")

    args = parser.parse_args()
    if "/" not in args.repo:
        parser.error("repo must be owner/name")
    owner, repo_name = args.repo.split("/", 1)

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    deepseek_key = os.environ.get("DEEPSEEK_API_KEY")
    output_dir = os.path.abspath(args.output)

    eprint(f"== {owner}/{repo_name}  {args.from_ref} -> {args.to_ref}  [{args.template}] ==")

    eprint("[1/6] PARSE_INPUT")
    step_parse_input(owner, repo_name, args.from_ref, args.to_ref, args.template, output_dir)

    eprint("[2/6] COLLECT_DATA")
    collector_output = step_collect_data(owner, repo_name, args.from_ref, args.to_ref, token, output_dir)

    eprint("[3/6] ANALYZE")
    analyzer_output = step_analyze(collector_output, owner, repo_name)
    write_json(os.path.join(output_dir, "analyzer_output.json"), analyzer_output)
    eprint(f"  {analyzer_output['summary']['totalCommits']} commits, {len(analyzer_output['closedIssues'])} closed, {len(analyzer_output['openIssues'])} open")

    if args.json_only:
        json.dump(analyzer_output, sys.stdout, indent=2, ensure_ascii=False)
        eprint("  [json-only mode] Raw data written to stdout. Skipping WRITER/FORMATTER/QUALITY.")
        return

    eprint("[4/6] WRITER")
    writer_output = step_write(analyzer_output, args.template, deepseek_key)
    write_json(os.path.join(output_dir, "writer_output.json"), writer_output)
    eprint(f"  {len(writer_output['communityHighlights'])} highlights, {len(writer_output['categories'])} categories, {len(writer_output['roadmap'])} roadmap")

    eprint("[5/6] FORMATTER")
    formatted = step_format(writer_output, owner, repo_name, args.from_ref, args.to_ref, output_dir)
    eprint(f"  {len(formatted['rawMarkdown'])} chars of markdown")

    if args.skip_quality:
        eprint("[6/6] QUALITY_CHECK (skipped)")
    else:
        eprint("[6/6] QUALITY_CHECK")
        report = step_quality_check(formatted, output_dir)
        if report["passed"]:
            eprint("  PASSED")
        else:
            all_issues = report["sections"]["summary"]["issues"] + report["sections"]["content"]["issues"] + report["sections"]["markdown"]["issues"]
            eprint(f"  Issues ({len(all_issues)}):")
            for iss in all_issues:
                eprint(f"    - {iss}")

    eprint(f"== Output: {os.path.join(output_dir, 'formatted_output.json')} ==")

    if args.print_output:
        sys.stdout.buffer.write(formatted["rawMarkdown"].encode("utf-8"))


if __name__ == "__main__":
    main()
