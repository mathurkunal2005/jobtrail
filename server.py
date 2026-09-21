import os
import shutil
from datetime import datetime
from mcp.server.mcpserver import MCPServer
from db import get_connection, init_db, log_action, RESUMES_DIR
from gmail_helper import fetch_recent_emails
from github_helper import get_user_repo_summary, get_org_tech_stack_summary

# Create the server, give it a name
mcp = MCPServer("jobtrail")

# Make sure the database, tables, and resumes folder exist before we start
init_db()

# This is our one dummy tool, just to prove things work
@mcp.tool()
def say_hello(name: str) -> str:
    """Say hello to someone by name."""
    return f"Hello, {name}! JobTrail server is working."

@mcp.tool()
def list_applications() -> str:
    """Lists all job applications currently tracked, with their status."""
    conn = get_connection()
    rows = conn.execute("SELECT * FROM applications ORDER BY id").fetchall()
    conn.close()

    if not rows:
        return "No applications tracked yet."

    lines = []
    for row in rows:
        lines.append(
            f"#{row['id']} — {row['company']} ({row['role']}): "
            f"{row['status']}, applied {row['date_applied']}"
        )
    return "\n".join(lines)

@mcp.tool()
def get_application(id: int) -> str:
    """Gets full details on one specific application by its id number."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (id,)).fetchone()
    conn.close()

    if row is None:
        return f"No application found with id {id}."

    return (
        f"#{row['id']} — {row['company']} ({row['role']})\n"
        f"Status: {row['status']}\n"
        f"Date applied: {row['date_applied']}"
    )

@mcp.tool()
def add_application(company: str, role: str, status: str, date_applied: str) -> str:
    """
    Adds a new job application to the tracker.
    date_applied should be in YYYY-MM-DD format.
    """
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO applications (company, role, status, date_applied) VALUES (?, ?, ?, ?)",
        (company, role, status, date_applied)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    log_action(
        "add_application",
        f"Added #{new_id}: {company} ({role}), status={status}, applied={date_applied}"
    )

    return f"Added application #{new_id}: {company} — {role} ({status})"

@mcp.tool()
def update_status(id: int, new_status: str) -> str:
    """Updates the status of an existing application by its id number."""
    conn = get_connection()

    row = conn.execute("SELECT * FROM applications WHERE id = ?", (id,)).fetchone()
    if row is None:
        conn.close()
        return f"No application found with id {id}. Nothing was changed."

    old_status = row["status"]

    conn.execute(
        "UPDATE applications SET status = ? WHERE id = ?",
        (new_status, id)
    )
    conn.commit()
    conn.close()

    log_action(
        "update_status",
        f"#{id} ({row['company']}): status changed from '{old_status}' to '{new_status}'"
    )

    return f"Updated #{id} ({row['company']}): status changed from '{old_status}' to '{new_status}'"

@mcp.tool()
def save_resume(company: str, role: str, source_file_path: str) -> str:
    """
    Saves a resume PDF for a specific company + role combination.
    source_file_path should be the full local path to the PDF file to save.
    If a resume already exists for this exact company + role, it gets replaced.
    """
    if not os.path.isfile(source_file_path):
        return f"File not found: {source_file_path}"

    ext = os.path.splitext(source_file_path)[1] or ".pdf"
    safe_company = company.replace(" ", "_")
    safe_role = role.replace(" ", "_")
    dest_filename = f"{safe_company}_{safe_role}{ext}"
    dest_path = os.path.join(RESUMES_DIR, dest_filename)

    shutil.copy2(source_file_path, dest_path)

    conn = get_connection()
    conn.execute("""
        INSERT INTO resumes (company, role, file_path, uploaded_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(company, role) DO UPDATE SET
            file_path = excluded.file_path,
            uploaded_at = excluded.uploaded_at
    """, (company, role, dest_path, datetime.now().isoformat()))
    conn.commit()
    conn.close()

    log_action(
        "save_resume",
        f"Saved resume for {company} ({role}) -> {dest_path}"
    )

    return f"Saved resume for {company} — {role} at {dest_path}"

@mcp.tool()
def get_resume(company: str, role: str) -> str:
    """Retrieves the saved resume file path for a specific company + role combination."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM resumes WHERE company = ? AND role = ?", (company, role)
    ).fetchone()
    conn.close()

    if row is None:
        return f"No resume found for {company} — {role}."

    return f"Resume for {company} — {role}: {row['file_path']} (uploaded {row['uploaded_at']})"

@mcp.tool()
def search_gmail_applications(query: str, max_results: int) -> str:
    """
    Searches Gmail for emails that might be related to job applications
    (using Gmail's own search syntax) and returns their subject, sender,
    date, and a short preview of each match. Read-only — does not modify
    or send any email.

    After reviewing the results, use add_application or update_status to
    record anything relevant — those still require your approval.
    """
    try:
        emails = fetch_recent_emails(query, max_results)
    except FileNotFoundError:
        return "Gmail credentials not found. Make sure credentials.json is in the project folder."

    if not emails:
        return "No matching emails found."

    lines = []
    for e in emails:
        lines.append(
            f"From: {e['from']}\n"
            f"Subject: {e['subject']}\n"
            f"Date: {e['date']}\n"
            f"Preview: {e['snippet']}\n"
            f"---"
        )
    return "\n".join(lines)

@mcp.tool()
def get_stats() -> str:
    """
    Shows summary statistics across all tracked applications:
    counts by status, and overall response rate.
    """
    conn = get_connection()
    rows = conn.execute("SELECT status FROM applications").fetchall()
    conn.close()

    total = len(rows)
    if total == 0:
        return "No applications tracked yet."

    counts = {}
    for row in rows:
        status = row["status"]
        counts[status] = counts.get(status, 0) + 1

    awaiting = counts.get("Applied", 0)
    responded = total - awaiting
    response_rate = (responded / total) * 100

    lines = [f"Total applications: {total}", ""]
    lines.append("By status:")
    for status, count in sorted(counts.items(), key=lambda x: -x[1]):
        lines.append(f"  {status}: {count}")
    lines.append("")
    lines.append(f"Response rate: {response_rate:.0f}% ({responded}/{total} moved past 'Applied')")

    return "\n".join(lines)

@mcp.tool()
def get_pending_followups(days_threshold: int) -> str:
    """
    Lists applications still in 'Applied' status with no update for at least
    days_threshold days — candidates for a follow-up email.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM applications WHERE status = 'Applied' ORDER BY date_applied"
    ).fetchall()
    conn.close()

    if not rows:
        return "No applications are currently awaiting a response."

    today = datetime.now().date()
    overdue = []

    for row in rows:
        try:
            applied_date = datetime.strptime(row["date_applied"], "%Y-%m-%d").date()
        except ValueError:
            continue

        days_waiting = (today - applied_date).days
        if days_waiting >= days_threshold:
            overdue.append((row, days_waiting))

    if not overdue:
        return f"No applications have been waiting {days_threshold}+ days."

    lines = [f"Applications waiting {days_threshold}+ days with no update:", ""]
    for row, days_waiting in overdue:
        lines.append(
            f"#{row['id']} — {row['company']} ({row['role']}): "
            f"applied {row['date_applied']}, {days_waiting} days ago"
        )

    return "\n".join(lines)

@mcp.tool()
def save_resume_tex(label: str, latex_source: str) -> str:
    """
    Saves a named LaTeX resume variant (e.g. "master", "Google_SDE").
    If a variant with this label already exists, it gets overwritten with
    the new content — its previous version is not kept.
    Use this to store your base resume, and later to save a tailored
    version after editing it for a specific job.
    """
    now = datetime.now().isoformat()
    conn = get_connection()
    conn.execute("""
        INSERT INTO resume_variants (label, latex_source, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(label) DO UPDATE SET
            latex_source = excluded.latex_source,
            updated_at = excluded.updated_at
    """, (label, latex_source, now, now))
    conn.commit()
    conn.close()

    log_action("save_resume_tex", f"Saved resume variant '{label}' ({len(latex_source)} chars)")

    return f"Saved resume variant '{label}'."

@mcp.tool()
def list_resume_variants() -> str:
    """Lists all saved LaTeX resume variants by label, with when each was last updated."""
    conn = get_connection()
    rows = conn.execute("SELECT label, updated_at FROM resume_variants ORDER BY updated_at DESC").fetchall()
    conn.close()

    if not rows:
        return "No resume variants saved yet."

    lines = [f"{row['label']} (updated {row['updated_at']})" for row in rows]
    return "\n".join(lines)

@mcp.tool()
def get_resume_tex(label: str) -> str:
    """
    Retrieves the full LaTeX source of a saved resume variant by its label.
    Use this to pull up your base resume before tailoring it for a job description.
    """
    conn = get_connection()
    row = conn.execute("SELECT * FROM resume_variants WHERE label = ?", (label,)).fetchone()
    conn.close()

    if row is None:
        return f"No resume variant found with label '{label}'."

    return row["latex_source"]

@mcp.tool()
def get_my_github_projects(username: str, max_repos: int) -> str:
    """
    Fetches a summary of your public GitHub repositories (name, description,
    primary language, stars, last updated) to help keep resume project
    bullets current. Forked repos are excluded.
    """
    try:
        repos = get_user_repo_summary(username, max_repos)
    except Exception as e:
        return f"Couldn't fetch GitHub repos: {e}"

    if not repos:
        return f"No public repos found for {username}."

    lines = []
    for r in repos:
        lines.append(
            f"{r['name']} ({r['language']}, {r['stars']}★) — updated {r['updated_at']}\n"
            f"  {r['description']}\n"
            f"  {r['url']}"
        )
    return "\n".join(lines)

@mcp.tool()
def analyze_company_tech_stack(github_org: str, max_repos: int) -> str:
    """
    Analyzes a company's public GitHub organization to summarize their
    dominant programming languages across their repos — useful context
    when tailoring a resume for a role at that company.
    """
    try:
        result = get_org_tech_stack_summary(github_org, max_repos)
    except Exception as e:
        return f"Couldn't fetch GitHub org data: {e}"

    if result["repos_analyzed"] == 0:
        return f"No public repos found for organization '{github_org}'."

    lines = [f"Analyzed {result['repos_analyzed']} public repos from '{github_org}':", ""]
    for lang, count in sorted(result["language_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"  {lang}: {count}")

    return "\n".join(lines)

# This runs the server when we execute this file directly
if __name__ == "__main__":
    mcp.run()