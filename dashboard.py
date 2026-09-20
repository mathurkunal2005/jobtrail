from flask import Flask, render_template_string
from db import get_connection

app = Flask(__name__)

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>JobTrail Dashboard</title>
    <style>
        body { font-family: -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }
        h1 { color: #f97316; }
        h2 { color: #94a3b8; font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 2.5rem; }
        table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
        th, td { text-align: left; padding: 0.6rem 0.8rem; border-bottom: 1px solid #1e293b; }
        th { color: #64748b; font-weight: 500; font-size: 0.85rem; }
        .status { display: inline-block; padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.8rem; }
        .status-applied { background: #1e3a8a; color: #93c5fd; }
        .status-interview { background: #78350f; color: #fcd34d; }
        .status-rejected { background: #7f1d1d; color: #fca5a5; }
        .status-offer { background: #14532d; color: #86efac; }
        .status-default { background: #334155; color: #cbd5e1; }
        .stat-cards { display: flex; gap: 1rem; margin-top: 1rem; }
        .card { background: #1e293b; border-radius: 0.5rem; padding: 1.2rem; flex: 1; }
        .card .number { font-size: 2rem; font-weight: bold; color: #f97316; }
        .card .label { color: #94a3b8; font-size: 0.85rem; }
        .audit-row { font-family: monospace; font-size: 0.85rem; color: #94a3b8; }
    </style>
</head>
<body>
    <h1>🗂️ JobTrail Dashboard</h1>

    <div class="stat-cards">
        <div class="card">
            <div class="number">{{ total }}</div>
            <div class="label">Total Applications</div>
        </div>
        <div class="card">
            <div class="number">{{ response_rate }}%</div>
            <div class="label">Response Rate</div>
        </div>
        <div class="card">
            <div class="number">{{ audit_count }}</div>
            <div class="label">Logged Actions</div>
        </div>
    </div>

    <h2>Applications</h2>
    <table>
        <tr><th>#</th><th>Company</th><th>Role</th><th>Status</th><th>Applied</th></tr>
        {% for app in applications %}
        <tr>
            <td>{{ app['id'] }}</td>
            <td>{{ app['company'] }}</td>
            <td>{{ app['role'] }}</td>
            <td><span class="status status-{{ app['status']|lower|replace(' ', '-') }}">{{ app['status'] }}</span></td>
            <td>{{ app['date_applied'] }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2>Recent Activity (Audit Log)</h2>
    <table>
        <tr><th>Timestamp</th><th>Action</th><th>Details</th></tr>
        {% for entry in audit_log %}
        <tr class="audit-row">
            <td>{{ entry['timestamp'] }}</td>
            <td>{{ entry['action'] }}</td>
            <td>{{ entry['details'] }}</td>
        </tr>
        {% endfor %}
    </table>
</body>
</html>
"""

@app.route("/")
def dashboard():
    conn = get_connection()
    applications = conn.execute("SELECT * FROM applications ORDER BY id DESC").fetchall()
    audit_log = conn.execute("SELECT * FROM audit_log ORDER BY id DESC LIMIT 20").fetchall()
    audit_count = conn.execute("SELECT COUNT(*) as c FROM audit_log").fetchone()["c"]
    conn.close()

    total = len(applications)
    if total > 0:
        awaiting = sum(1 for a in applications if a["status"] == "Applied")
        response_rate = round(((total - awaiting) / total) * 100)
    else:
        response_rate = 0

    return render_template_string(
        TEMPLATE,
        applications=applications,
        audit_log=audit_log,
        audit_count=audit_count,
        total=total,
        response_rate=response_rate
    )

if __name__ == "__main__":
    app.run(debug=True, port=5050)