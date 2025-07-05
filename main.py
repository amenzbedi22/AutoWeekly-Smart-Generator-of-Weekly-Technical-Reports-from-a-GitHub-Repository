import requests
from dateutil.parser import parse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import os

# === CONFIGURATION ===
# Replace with your GitHub personal access token
GITHUB_TOKEN = 'your_token_here'
REPO = 'Your_Target_GitHub_repository'  
OWNER = ' GitHub_user_or_organization'  

# Headers for GitHub API requests
headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# Define time window: past 7 days
since_dt = datetime.now(timezone.utc) - timedelta(days=7)
since = since_dt.isoformat()

# Initialize default metric counters for each contributor
metrics = defaultdict(lambda: {
    'add': 0,
    'fix': 0,
    'refactor': 0,
    'bugs_closed': 0,
    'tasks_completed': 0,
    'activity_days': set(),
    'commits_count': 0,
    'issues_opened': 0,
    'issues_closed': 0,
})

# Lists for compiling report sections
commit_summaries = []
bugs_resolved_list = []
backlog_tasks_list = []

def get_commits():
    """Fetch commits from the repository in the last 7 days and extract relevant metrics."""
    url = f'https://api.github.com/repos/{REPO}/commits'
    params = {'since': since}
    response = requests.get(url, headers=headers, params=params)
    commits = response.json()

    for commit in commits:
        msg = commit['commit']['message'].strip()
        msg_lower = msg.lower()
        sha = commit['sha'][:7]
        date = commit['commit']['author']['date']
        author = (commit.get('author') or {}).get('login', 'unknown')

        metrics[author]['commits_count'] += 1
        date_only = date.split("T")[0]
        metrics[author]['activity_days'].add(date_only)

        # Classify commit types
        if 'fix' in msg_lower:
            metrics[author]['fix'] += 1
        if 'add' in msg_lower or 'feat' in msg_lower or 'feature' in msg_lower:
            metrics[author]['add'] += 1
        if 'refactor' in msg_lower:
            metrics[author]['refactor'] += 1

        commit_summaries.append(f"- [{sha}] {msg} by @{author} ({date[:10]})")

def get_issues():
    """Fetch issues (opened and closed) and count bugs resolved."""
    url = f'https://api.github.com/repos/{REPO}/issues'
    params = {'state': 'all', 'since': since}
    response = requests.get(url, headers=headers, params=params)
    issues = response.json()

    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)

    for issue in issues:
        if 'pull_request' in issue:
            continue  # Skip PRs
        created = parse(issue['created_at'])
        closed_at = parse(issue['closed_at']) if issue['closed_at'] else None
        title = issue['title']
        number = issue['number']
        user = issue['user']['login']

        metrics[user]['activity_days'].add(created.date().isoformat())

        if created >= one_week_ago:
            metrics[user]['issues_opened'] += 1

        if closed_at and closed_at >= one_week_ago:
            metrics[user]['issues_closed'] += 1
            labels = [label['name'].lower() for label in issue.get('labels', [])]
            if 'bug' in labels:
                metrics[user]['bugs_closed'] += 1
                bugs_resolved_list.append(f"- #{number}: {title} closed by @{user} ({closed_at.date()})")

def get_project_tasks():
    """Fetch Project V2 tasks and determine completed and backlog items."""
    graphql_url = "https://api.github.com/graphql"
    graphql_query = f"""
    {{
      user(login: "{OWNER}") {{
        projectV2(number: 4) {{
          items(first: 50) {{
            nodes {{
              content {{
                __typename
                ... on Issue {{ title updatedAt author {{ login }} }}
                ... on PullRequest {{ title updatedAt author {{ login }} }}
                ... on DraftIssue {{ title updatedAt creator {{ login }} }}
              }}
              updatedAt
              fieldValues(first: 10) {{
                nodes {{
                  ... on ProjectV2ItemFieldSingleSelectValue {{ name }}
                  ... on ProjectV2ItemFieldTextValue {{ text }}
                }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    response = requests.post(graphql_url, json={'query': graphql_query}, headers=headers)
    data = response.json()

    if 'errors' in data:
        print(" GitHub API returned errors:")
        for error in data['errors']:
            print(f" {error.get('message')}")
        return

    try:
        items = data['data']['user']['projectV2']['items']['nodes']
        for item in items:
            content = item.get('content')
            status_list = [
                field.get('name') or field.get('text')
                for field in item.get('fieldValues', {}).get('nodes', [])
                if field.get('name') or field.get('text')
            ]
            status = ", ".join(status_list) if status_list else "No status"

            if content:
                typename = content.get('__typename')
                title = content.get('title', 'No title')
                updated = content.get('updatedAt', 'Unknown date')

                author = content.get('author', {}).get('login') or content.get('creator', {}).get('login', 'unknown')

                updated_dt = parse(updated)
                if updated_dt >= since_dt:
                    metrics[author]['tasks_completed'] += 1
                    metrics[author]['activity_days'].add(updated_dt.date().isoformat())

                if not any(s.lower() in ['done', 'completed', 'closed'] for s in status_list):
                    backlog_tasks_list.append(f"- [{typename}] {title} by @{author} | Status: {status}")
            else:
                backlog_tasks_list.append(f"- [No content task] | Status: No status")

    except Exception as e:
        print(" Error parsing project tasks:", e)

def get_collaborators():
    """Fetch all collaborators for the repository."""
    url = f"https://api.github.com/repos/{REPO}/collaborators"
    response = requests.get(url, headers=headers)
    collaborators = response.json()

    if isinstance(collaborators, dict) and collaborators.get("message"):
        print(f"Error: {collaborators['message']}")
        return []
    return collaborators

def ensure_all_collaborators_in_metrics(collaborators):
    """Ensure all collaborators exist in the metrics dictionary."""
    for user in collaborators:
        login = user['login']
        if login not in metrics:
            metrics[login]  # Triggers default initialization

def calculate_kpis():
    """Calculate KPI score for each user using weighted formula."""
    kpis = {}
    for user, m in metrics.items():
        kpi_score = 2*m['add'] + 2.5*m['fix'] + 2*m['bugs_closed'] + 3*m['tasks_completed']
        kpis[user] = kpi_score
    return kpis

def assign_badges():
    """Assign badges to contributors based on defined performance criteria."""
    badge_awards = {}
    if not metrics:
        return badge_awards

    kpis = calculate_kpis()
    badge_awards['Top Contributor'] = max(kpis, key=kpis.get)
    badge_awards['Bug Squasher'] = max(metrics.items(), key=lambda x: x[1]['bugs_closed'])[0]
    badge_awards['Most Active'] = max(metrics.items(), key=lambda x: (
        x[1]['commits_count'] + x[1]['issues_opened'] + x[1]['issues_closed'] + x[1]['tasks_completed']))[0]
    badge_awards['Feature Creator'] = max(metrics.items(), key=lambda x: x[1]['add'])[0]
    badge_awards['Code Refactorer'] = max(metrics.items(), key=lambda x: x[1]['refactor'])[0]
    badge_awards['Consistent Contributor'] = [user for user, m in metrics.items() if len(m['activity_days']) >= 3]
    return badge_awards

def generate_markdown_report():
    """Generate a structured markdown file summarizing weekly activity."""
    week_number = datetime.now().isocalendar()[1]
    date_from = since_dt.date()
    date_to = (since_dt + timedelta(days=6)).date()
    report_dir = "reports"
    os.makedirs(report_dir, exist_ok=True)
    filename = f"{report_dir}/Weekly_Report_Week_{week_number}.md"

    kpis = calculate_kpis()
    badges = assign_badges()

    lines = [f"# Weekly Technical Report - Week {week_number} ({date_from} to {date_to})\n"]

    lines.append("## Technical Achievements (Commits)\n")
    lines.extend(commit_summaries or ["_No commits recorded this week._"])

    lines.append("\n## Bugs Resolved (Closed Issues labeled 'bug')\n")
    lines.extend(bugs_resolved_list or ["_No bugs closed this week._"])

    lines.append("\n## Backlog Tasks (Open Tasks in Project)\n")
    lines.extend(backlog_tasks_list or ["_No backlog tasks found._"])

    lines.append("\n## KPI Scores\n")
    if kpis:
        for user, score in sorted(kpis.items(), key=lambda x: x[1], reverse=True):
            m = metrics[user]
            lines.append(f"- @{user}: **{score:.2f} points** (add: {m['add']}, fix: {m['fix']}, bugs closed: {m['bugs_closed']}, tasks completed: {m['tasks_completed']})")
    else:
        lines.append("_No KPI data available._")

    lines.append("\n## Contributor Badges\n")
    for badge, users in badges.items():
        if isinstance(users, list):
            lines.append(f"- **{badge}**: {', '.join(f'@{u}' for u in users)}" if users else f"- **{badge}**: None")
        else:
            lines.append(f"- **{badge}**: @{users}")

    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n Markdown report saved to {filename}")

# === MAIN EXECUTION ===
get_commits()
get_issues()
get_project_tasks()
collaborators = get_collaborators()
ensure_all_collaborators_in_metrics(collaborators)
generate_markdown_report()
