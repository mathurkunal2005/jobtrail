from mcp.server.mcpserver import MCPServer
from db import get_connection, init_db, log_action

# Create the server, give it a name
mcp = MCPServer("jobtrail")

# Make sure the database and tables exist before we start
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

# This runs the server when we execute this file directly
if __name__ == "__main__":
    mcp.run()