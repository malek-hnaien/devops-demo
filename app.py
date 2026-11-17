import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    psycopg2 = None

app = Flask(__name__)


def is_postgres():
    return bool(os.getenv("DB_HOST"))


def get_db_connection():
    db_host = os.getenv("DB_HOST")
    if db_host:
        conn = psycopg2.connect(
            host=db_host,
            port=int(os.getenv("DB_PORT", 5432)),
            user=os.getenv("DB_USER", "demo"),
            password=os.getenv("DB_PASSWORD", "demopass"),
            dbname=os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "demodb")),
        )
        return conn
    else:
        default_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.db")
        db_path = os.getenv("SQLITE_DB_PATH", default_db)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    if is_postgres():
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                course TEXT NOT NULL,
                due_date TEXT,
                completed BOOLEAN DEFAULT FALSE
            )
            """
        )
    else:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course TEXT NOT NULL,
                due_date TEXT,
                completed BOOLEAN DEFAULT 0
            )
            """
        )
    conn.commit()
    cur.close()
    conn.close()


def fetch_all_tasks():
    init_db()
    conn = get_db_connection()
    if is_postgres():
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT id, title, course, due_date, completed FROM tasks ORDER BY id DESC")
        rows = cur.fetchall()
        tasks = [dict(row) for row in rows]
    else:
        cur = conn.cursor()
        cur.execute("SELECT id, title, course, due_date, completed FROM tasks ORDER BY id DESC")
        rows = cur.fetchall()
        tasks = [
            {
                "id": row["id"],
                "title": row["title"],
                "course": row["course"],
                "due_date": row["due_date"],
                "completed": bool(row["completed"]),
            }
            for row in rows
        ]
    cur.close()
    conn.close()
    return tasks


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/", methods=["GET"])
def index():
    tasks = fetch_all_tasks()
    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t["completed"])
    pending_tasks = total_tasks - completed_tasks
    return render_template(
        "index.html",
        tasks=tasks,
        total_tasks=total_tasks,
        pending_tasks=pending_tasks,
        completed_tasks=completed_tasks,
    )


@app.route("/api/tasks", methods=["GET"])
def api_tasks():
    tasks = fetch_all_tasks()
    return jsonify(tasks), 200


@app.route("/tasks", methods=["POST"])
def add_task():
    init_db()
    if request.is_json:
        data = request.get_json()
        title = (data.get("title") or "").strip()
        course = (data.get("course") or "General").strip()
        due_date = (data.get("due_date") or "").strip()
    else:
        title = (request.form.get("title") or "").strip()
        course = (request.form.get("course") or "General").strip()
        due_date = (request.form.get("due_date") or "").strip()

    if not title:
        if request.is_json:
            return jsonify({"error": "Title is required"}), 400
        return redirect(url_for("index"))

    conn = get_db_connection()
    cur = conn.cursor()
    if is_postgres():
        cur.execute(
            "INSERT INTO tasks (title, course, due_date, completed) VALUES (%s, %s, %s, FALSE)",
            (title, course, due_date),
        )
    else:
        cur.execute(
            "INSERT INTO tasks (title, course, due_date, completed) VALUES (?, ?, ?, 0)",
            (title, course, due_date),
        )
    conn.commit()
    cur.close()
    conn.close()

    if request.is_json:
        return jsonify({"message": "Task created"}), 201
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/toggle", methods=["POST"])
def toggle_task(task_id):
    init_db()
    conn = get_db_connection()
    cur = conn.cursor()
    if is_postgres():
        cur.execute("UPDATE tasks SET completed = NOT completed WHERE id = %s", (task_id,))
    else:
        cur.execute(
            "UPDATE tasks SET completed = CASE WHEN completed = 1 THEN 0 ELSE 1 END WHERE id = ?",
            (task_id,),
        )
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    init_db()
    conn = get_db_connection()
    cur = conn.cursor()
    if is_postgres():
        cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
    else:
        cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    init_db()
    if os.name == "nt" and not os.getenv("DB_HOST"):
        import threading
        import webbrowser

        threading.Timer(1.0, lambda: webbrowser.open("http://localhost:3000")).start()
    app.run(host="0.0.0.0", port=3000)
