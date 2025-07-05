# AutoWeekly-Smart-Generator-of-Weekly-Technical-Reports-from-a-GitHub-Repository

# 🧠 AutoWeekly – Smart Generator of Weekly Technical Reports from a GitHub Repository

AutoWeekly is an automated Python-based tool that generates a weekly Markdown report summarizing all GitHub activity in a repository. It computes contributor KPIs, assigns motivational badges, and saves the report in a clean format for visibility and performance tracking.

---

## 📦 Features

- Collects and analyzes:
  - ✅ Commits (by type: `add`, `fix`, `refactor`, etc.)
  - ✅ Issues opened and closed (bugs highlighted)
  - ✅ GitHub Project V2 task completions
  - ✅ Collaborator activity (commits, tasks, issues)
- Computes a weighted **KPI Score** for each contributor
- Assigns **weekly performance badges**
- Generates a Markdown report in the `/reports` directory
- Automatically runs **every Friday at 5:00 PM** via GitHub Actions

---

## 🚀 Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
```

### 2. Install Required Dependencies

Make sure you have Python 3.7+ installed.

```bash
pip install requests python-dateutil
```

### 3. Configure Your GitHub Token

Create a **Personal Access Token (PAT)** with the following scopes:
- `repo` (to access repo data)
- `read:org` (to access collaborators)
- `project` (to access Project V2)

Then, set your token in the script or via an environment variable:

```bash
# Option 1: Add directly to the script (not recommended for production)
GITHUB_TOKEN = 'ghp_YourTokenHere'

# Option 2: Export as environment variable (recommended)
export GITHUB_TOKEN=ghp_YourTokenHere
```

---

## 🧮 KPI Score Calculation

Each contributor's **KPI Score** is calculated with the following weighted formula:

```text
KPI = (2 × add) + (2.5 × fix) + (2 × bugs_closed) + (3 × tasks_completed)
```

| Contribution Type       | Weight |
|-------------------------|--------|
| `add` commits           | 2.0    |
| `fix` commits           | 2.5    |
| Closed `bug` issues     | 2.0    |
| Completed project tasks | 3.0    |

---

## 🏅 Contributor Badge Assignment

| Badge                  | Criteria                                                           |
|------------------------|--------------------------------------------------------------------|
| **Top Contributor**     | Highest weekly KPI score                                           |
| **Bug Squasher**        | Most closed issues labeled `bug`                                   |
| **Most Active**         | Highest total number of actions (commits, issues, tasks)           |
| **Feature Creator**     | Most commits labeled as `add`/`feat`                               |
| **Code Refactorer**     | Most `refactor` commits                                            |
| **Consistent Contributor** | Activity detected on at least 3 different days during the week |

---

## 📄 Output Report

- Reports are saved in the `/reports` folder
- Filename format: `Weekly_Report_Week_<XX>.md`
- Example content:

```markdown
# Weekly Technical Report - Week 27 (2025-06-30 to 2025-07-06)

## Technical Achievements (Commits)
- [a1b2c3d] Add UART driver support by @johndoe (2025-07-02)

## Bugs Resolved (Closed Issues labeled 'bug')
- #14: Fix broken ISR handler closed by @johndoe (2025-07-04)

## Backlog Tasks
- [Issue] Finalize datasheet parsing by @janedoe | Status: In Progress

## KPI Scores
- @johndoe: **10.5 points** (add: 2, fix: 2, bugs closed: 1, tasks completed: 1)

## Contributor Badges
- **Top Contributor**: @johndoe
- **Bug Squasher**: @johndoe
- **Feature Creator**: @johndoe
- **Consistent Contributor**: @johndoe
```

---

## 🤖 GitHub Actions Automation

A GitHub Actions workflow file (`.github/workflows/weekly.yml`) runs the script every **Friday at 17:00 (UTC)**.

### Sample Workflow

```yaml
name: Weekly KPI Report

on:
  schedule:
    - cron: '0 17 * * 5'
  workflow_dispatch:

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install requests python-dateutil

      - name: Run Weekly Report Generator
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: python auto_weekly.py

      - name: Commit and push report
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add reports/
          git commit -m "📊 Weekly KPI Report - Week $(date +'%V')" || echo "No changes"
          git push
```

> Make sure your script is named `auto_weekly.py` and placed at the root.

---

## 📬 Contributing

Want to improve the badge system, support multiple repos, or add Slack/email integration? PRs are welcome!

---

## 📜 License

MIT License – Feel free to use and modify.
