from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ----------------- DB Setup -----------------
def init_db():
    conn = sqlite3.connect("project_management.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    name TEXT NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER,
                    title TEXT NOT NULL,
                    status TEXT DEFAULT 'Pending')""")
    conn.commit()
    conn.close()

init_db()

# ----------------- Routes -----------------
@app.route("/")
def index():
    if "username" not in session:
        return redirect("/login")
    conn = sqlite3.connect("project_management.db")
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE user_id=?", (session["user_id"],))
    projects = c.fetchall()
    conn.close()
    return render_template("index.html", projects=projects)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = generate_password_hash(request.form["password"])
        try:
            conn = sqlite3.connect("project_management.db")
            c = conn.cursor()
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            conn.close()
            flash("Registration successful! Please login.", "success")
            return redirect("/login")
        except:
            flash("Username already exists!", "danger")
            return redirect("/register")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = sqlite3.connect("project_management.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()
        if user and check_password_hash(user[2], password):
            session["username"] = user[1]
            session["user_id"] = user[0]
            flash("Login successful!", "success")
            return redirect("/")
        else:
            flash("Invalid username or password", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect("/login")

@app.route("/add_project", methods=["POST"])
def add_project():
    if "username" not in session:
        return redirect("/login")
    name = request.form["name"]
    conn = sqlite3.connect("project_management.db")
    c = conn.cursor()
    c.execute("INSERT INTO projects (user_id, name) VALUES (?, ?)", (session["user_id"], name))
    conn.commit()
    conn.close()
    flash("Project added!", "success")
    return redirect("/")

@app.route("/project/<int:project_id>")
def project_detail(project_id):
    if "username" not in session:
        return redirect("/login")
    conn = sqlite3.connect("project_management.db")
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id=?", (project_id,))
    project = c.fetchone()
    c.execute("SELECT * FROM tasks WHERE project_id=?", (project_id,))
    tasks = c.fetchall()
    conn.close()
    return render_template("project_detail.html", project=project, tasks=tasks)

@app.route("/add_task/<int:project_id>", methods=["POST"])
def add_task(project_id):
    if "username" not in session:
        return redirect("/login")
    title = request.form["title"]
    conn = sqlite3.connect("project_management.db")
    c = conn.cursor()
    c.execute("INSERT INTO tasks (project_id, title) VALUES (?, ?)", (project_id, title))
    conn.commit()
    conn.close()
    flash("Task added!", "success")
    return redirect(f"/project/{project_id}")

@app.route("/update_task/<int:task_id>/<int:project_id>")
def update_task(task_id, project_id):
    if "username" not in session:
        return redirect("/login")
    conn = sqlite3.connect("project_management.db")
    c = conn.cursor()
    c.execute("UPDATE tasks SET status='Done' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()
    flash("Task marked as done!", "success")
    return redirect(f"/project/{project_id}")

# ----------------- Dashboard -----------------
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        return redirect("/login")

    conn = sqlite3.connect("project_management.db")
    c = conn.cursor()

    # Total projects
    c.execute("SELECT COUNT(*) FROM projects WHERE user_id=?", (session["user_id"],))
    total_projects = c.fetchone()[0]

    # Total tasks
    c.execute("SELECT COUNT(*) FROM tasks WHERE project_id IN (SELECT id FROM projects WHERE user_id=?)", (session["user_id"],))
    total_tasks = c.fetchone()[0]

    # Completed tasks
    c.execute("SELECT COUNT(*) FROM tasks WHERE status='Done' AND project_id IN (SELECT id FROM projects WHERE user_id=?)", (session["user_id"],))
    completed_tasks = c.fetchone()[0]

    conn.close()

    return render_template("dashboard.html", 
                           total_projects=total_projects,
                           total_tasks=total_tasks,
                           completed_tasks=completed_tasks)

# ----------------- Run App -----------------
if __name__ == "__main__":
    app.run(debug=True)
