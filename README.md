# JobTrail

**An MCP server that gives Claude (or any MCP-compatible AI) hands to manage your job search — reads your inbox, tracks applications, tailors your resume per role, checks a company's tech stack, and keeps a full audit trail of everything it touches.**

Every write action requires your explicit approval before it happens. Nothing gets added, changed, or saved without you saying yes.

---

## What it does

JobTrail exposes a set of tools an AI agent can call to help manage a job search:

- **Track applications** — add, update, and review your application pipeline
- **Read your Gmail** — search for application-related emails (read-only) and surface them so the AI can propose updates
- **Manage resumes** — store multiple PDF resume versions per company + role, and store your resume as editable LaTeX
- **Tailor your resume automatically** — give it a job description, and it pulls your base resume, rewrites it to match the role, and saves the tailored version — no prompt-engineering skill required, the tool's own instructions guide the AI
- **Research a company's tech stack** — analyze a company's public GitHub org to see what languages/frameworks they actually use, to inform how you tailor your resume
- **Keep your own projects current** — pull your own public GitHub repos to help keep resume bullets up to date
- **Surface stats and follow-ups** — response rate, applications by status, and which applications have gone quiet and are worth a follow-up
- **Log everything** — every write action is recorded in an audit log with a timestamp, so there's always a record of what changed and when

## Why the approval gate matters

An AI agent with hands can also make mistakes with those hands. JobTrail's design principle: reads are free, but nothing gets *written* — no new application, no status change, no saved resume — without a human confirming it first. Every MCP client (Claude Desktop, Cursor, etc.) shows this as a built-in approval prompt before the tool actually runs.

## Your data stays on your machine

JobTrail is local-first. There's no hosted server, no cloud database, no third party touching your resume, applications, or inbox data. Everything — your SQLite database, your resume files, your Gmail token — lives on your own computer. Cloning this repo gives you your own private instance; it never talks to anyone else's server.

## Tools

| Tool | Description | Type |
|---|---|---|
| `list_applications` | List all tracked applications | Read |
| `get_application` | Get details on one application by id | Read |
| `add_application` | Add a new application | Write |
| `update_status` | Update an application's status | Write |
| `save_resume` | Save a PDF resume for a company + role | Write |
| `get_resume` | Retrieve a saved resume's file path | Read |
| `save_resume_tex` | Save a named LaTeX resume variant | Write |
| `list_resume_variants` | List saved LaTeX resume variants | Read |
| `get_resume_tex` | Retrieve a LaTeX resume variant's source | Read |
| `search_gmail_applications` | Search Gmail for application-related emails | Read |
| `get_stats` | Summary stats: counts by status, response rate | Read |
| `get_pending_followups` | Applications awaiting a response past N days | Read |
| `get_my_github_projects` | Summary of your public GitHub repos | Read |
| `analyze_company_tech_stack` | Language breakdown of a company's public GitHub org | Read |

## Setup

### 1. Clone and install

```bash
git clone https://github.com/mathurkunal2005/jobtrail.git
cd jobtrail
python3 -m venv venv
source venv/bin/activate   # on Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set up Gmail access (optional, needed for `search_gmail_applications`)

1. Create a project at [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Gmail API
3. Configure the OAuth consent screen (External, add yourself as a test user)
4. Create OAuth credentials (type: Desktop app)
5. Download the credentials JSON and save it as `credentials.json` in the project root

### 3. Set up GitHub access (optional, needed for the GitHub tools)

1. Create a [Personal Access Token](https://github.com/settings/tokens) (classic) with the `public_repo` scope
2. Create a `.env` file in the project root with a line like:
   GITHUB_TOKEN=your_token_here

### 4. Connect it to your AI client

```bash
python3 setup.py
```

Pick your client from the menu — supports **Claude Desktop**, **Antigravity**, **Cursor**, **Cline**, and **VS Code** (native Copilot MCP). The script writes the correct config automatically; no manual JSON editing required.

Then fully restart your AI client and try asking it: "List my job applications"

The first Gmail-related request will open a browser window to authorize access — after that, it's remembered.

### 5. (Optional) View the dashboard

```bash
python3 dashboard.py
```

Open `http://127.0.0.1:5050` to see your applications and audit log in a browser.

## Tech stack

Python · SQLite · MCP SDK · Google Gmail API (OAuth) · GitHub API · Flask

## License

MIT
