from flask import Flask, render_template, request, redirect, session, flash, jsonify
import sqlite3, hashlib
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
BUMP_LIMIT = 100
app = Flask(__name__)
app.secret_key = "s!U@p#r$a%S^e&k*r(E)t_K+e~Y<6>7?I:z'k}1{b]i[DI|t=0-I,l.e/T;Z`ekret69"
DB = "board.db"

# ---------------- DATABASE ----------------
def get_db():
    return sqlite3.connect(DB, check_same_thread=False)

def hash_ip(ip, thread_id):
    return hashlib.sha256(f"{ip}-{thread_id}".encode()).hexdigest()[:8]

def init_db():
    db = get_db()
    c = db.cursor()

    # Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password_hash TEXT
        )
    """)

    # Boards
    c.execute("""
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE
        )
    """)

    # Threads
    c.execute("""
        CREATE TABLE IF NOT EXISTS threads (
            id INTEGER PRIMARY KEY,
            board_id INTEGER,
            title TEXT,
            content TEXT,
            user_id INTEGER,
            created_at TEXT,
            bumped_at TEXT
        )
    """)

    # Posts
    c.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY,
            thread_id INTEGER,
            content TEXT,
            user_id INTEGER,
            anon_id TEXT,
            created_at TEXT
        )
    """)

    #  HARD-CODED BOARDS 
    boards = [
        # General / Random
        "random",
        "memes",
        "funny",
        "videos",
        "events",

        # Stories & Writing
        "storys",

        # Media & Entertainment
        "movies",
        "tv",
        "books",
        "comics",
        "cartoons",
        "anime",

        # Arts & Performance
        "art",
        "music",
        "dance",
        "theater",
        "photography",

        # Food & Cooking
        "food",
        "cooking",
        "baking",

        # Lifestyle & Personal
        "fashion",
        "fitness",
        "health",
        "relationships",
        "pets",
        "home",
        "diy",
        "gardening",

        # Travel & Outdoors
        "travel",
        "nature",
        "hiking",
        "camping",
        "fishing",
        "hunting",

        # Environment & Climate
        "environment",
        "environment",
        "climate",

        # News & Society
        "news",
        "politics",

        # Business & Finance
        "economy",
        "business",
        "finance",
        "investing",
        "realestate",

        # Vehicles
        "cars",
        "motorcycles",

        # Technology & Computing
        "technology",
        "tech",
        "pc",
        "programming",
        "webdev",
        "mobiledev",
        "cybersecurity",
        "ai",
        "robotics",

        # Gaming
        "gaming",
        "boardgames",
        "tabletop",
        "roleplaying",
        "cardgames",
        "puzzles",

        # Science & Space
        "science",
        "space",
        "astronomy",
        "astrophysics",
        "cosmology",

        # Biology & Medical
        "zoology",
        "marinebiology",
        "veterinary",
        " medicine",
        "xenology",

        # Education & School Subjects
        "school",
        "math",
        "geography",
        "history",
        "english",
        "languages",
        "philosophy",
        "psychology",
        "religion",

        # Crafts & Hobbies
        "crafts",
        "knitting",
        "sewing",
        "woodworking",
        "collecting",

        # Sports
        "sports"
    ]

    for name in boards:
        c.execute("INSERT OR IGNORE INTO boards (name) VALUES (?)", (name,))

    db.commit()
    db.close()

# ---------------- SESSION LOGIN CHECK ----------------
@app.before_request
def require_login():
    if request.endpoint not in ("login", "register", "static") and "user_id" not in session:
        return redirect("/login")

# ---------------- AUTH ----------------
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"]
        if not u or not p:
            flash("Missing fields")
            return redirect("/register")
        db = get_db()
        try:
            db.execute("INSERT INTO users VALUES (NULL,?,?)",
                       (u, generate_password_hash(p)))
            db.commit()
        except:
            flash("Username exists")
            return redirect("/register")
        db.close()
        flash("Registration successful")
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]
        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=?", (u,)).fetchone()
        db.close()
        if user and check_password_hash(user[2], p):
            session["user_id"] = user[0]
            session["username"] = user[1]
            return redirect("/")
        flash("Invalid login")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ---------------- INDEX ----------------
@app.route("/")
def index():
    username = session.get("username")
    db = get_db()
    boards = db.execute("SELECT * FROM boards").fetchall()
    db.close()
    return render_template("index.html", boards=boards, username=username)

# ---------------- BOARD ----------------
@app.route("/board/<name>", methods=["GET","POST"])
def board(name):
    username = session.get("username")
    db = get_db()
    board = db.execute("SELECT * FROM boards WHERE name=?", (name,)).fetchone()
    if not board:
        db.close()
        return "Board not found", 404

    if request.method == "POST":
        title = request.form["title"].strip()
        content = request.form["content"].strip()
        if not title or not content:
            flash("Empty thread")
            return redirect(request.url)
        now = datetime.utcnow().isoformat()
        db.execute("""INSERT INTO threads VALUES
            (NULL,?,?,?,?,?,?)""",
            (board[0], title, content, session["user_id"], now, now))
        db.commit()
    db.close()
    return render_template("board.html", board=name, username=username)

# ---------------- THREAD ----------------
@app.route("/thread/<int:tid>", methods=["GET","POST"])
def thread(tid):
    username = session.get("username")
    user_id = session.get("user_id")
    db = get_db()

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        if content:
            anon = hash_ip(request.remote_addr or "unknown", tid)
            now = datetime.utcnow().isoformat()
            db.execute("""INSERT INTO posts (thread_id, content, user_id, anon_id, created_at)
                          VALUES (?, ?, ?, ?, ?)""",
                       (tid, content, user_id, anon, now))
            db.execute("UPDATE threads SET bumped_at=? WHERE id=?", (now, tid))
            db.commit()

    thread_row = db.execute("""
        SELECT threads.*, users.username, boards.name
        FROM threads
        JOIN users ON users.id=threads.user_id
        JOIN boards ON boards.id=threads.board_id
        WHERE threads.id=?""", (tid,)).fetchone()
    db.close()
    if not thread_row:
        return "Thread not found", 404

    return render_template("thread.html",
        thread=thread_row,
        user_id=user_id,
        username=username,
        board_name=thread_row[-1]  # pass board name for back link
    )


@app.route("/delete_thread/<int:tid>", methods=["POST"])
def delete_thread(tid):
    db = get_db()
    db.execute(
        "DELETE FROM threads WHERE id=? AND user_id=?",
        (tid, session["user_id"])
    )
    db.execute("DELETE FROM posts WHERE thread_id=?", (tid,))
    db.commit()
    db.close()
    return redirect(request.referrer or "/")

# ---------------- DELETE Reply ----------------
@app.route("/delete_post/<int:pid>", methods=["POST"])
def delete_post(pid):
    user_id = session.get("user_id")
    if not user_id:
        return redirect("/login")

    db = get_db()
    db.execute(
        "DELETE FROM posts WHERE id=? AND user_id=?",
        (pid, user_id)
    )
    db.commit()
    db.close()
    return redirect(request.referrer or "/")

# ---------------- JSON ----------------
@app.route("/board/<name>/threads.json")
def threads_json(name):
    db = get_db()
    board = db.execute("SELECT * FROM boards WHERE name=?", (name,)).fetchone()
    if not board:
        db.close()
        return jsonify([])

    threads = db.execute("""
        SELECT threads.*, users.username,
        (SELECT COUNT(*) FROM posts WHERE thread_id=threads.id) AS reply_count
        FROM threads JOIN users ON users.id=threads.user_id
        WHERE board_id=? ORDER BY bumped_at DESC
    """, (board[0],)).fetchall()
    db.close()

    return jsonify([
        {
            "id": t[0],
            "title": t[2],
            "content": t[3],
            "username": t[7],
            "replies": t[8],
            "time": t[5]
        }
        for t in threads
    ])

@app.route("/thread/<int:tid>/posts.json")
def posts_json(tid):
    db = get_db()
    posts = db.execute("""
        SELECT posts.content, posts.anon_id, posts.created_at, posts.user_id, posts.id, users.username
        FROM posts
        LEFT JOIN users ON posts.user_id=users.id
        WHERE thread_id=? ORDER BY posts.id
    """,(tid,)).fetchall()
    db.close()

    return jsonify([
        {
            "content": p[0],
            "anon": p[1],
            "time": p[2],
            "user_id": p[3],
            "id": p[4],
            "username": p[5]
        }
        for p in posts
    ])

# ---------------- INIT ----------------
init_db()

port = int(os.environ.get("PORT", 5000))

# Run the Flask app on 0.0.0.0 so it’s accessible externally
app.run(host="0.0.0.0", port=port, debug=True)

