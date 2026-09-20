import os
import shutil
from datetime import datetime
from mcp.server.mcpserver import MCPServer
from db import get_connection, init_db, log_action, RESUMES_DIR

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

    # First check it actually exists, so we can give a clear error otherwise
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

    # Build a clean destination filename, e.g. "Google_SDE.pdf"
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

# This runs the server when we execute this file directly
if __name__ == "__main__":
    mcp.run()