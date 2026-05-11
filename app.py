import os
import sqlite3
from datetime import date, timedelta
from flask import Flask, flash, g, redirect, render_template, request, session, url_for, jsonify, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DATABASE = os.path.join(DATA_DIR, "tracker.db")
UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "change-me-to-a-secret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def get_db():
    db = getattr(g, "db", None)
    if db is None:
        db = g.db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    db = get_db()
    with app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))
    db.commit()


@app.before_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, "db", None)
    if db is not None:
        db.close()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def column_exists(table, column_name):
    rows = query_db(f"PRAGMA table_info({table})")
    return any(row["name"] == column_name for row in rows)


def ensure_db_schema():
    db = get_db()
    if not column_exists("locations", "description"):
        db.execute("ALTER TABLE locations ADD COLUMN description TEXT")
    if not column_exists("locations", "image_filename"):
        db.execute("ALTER TABLE locations ADD COLUMN image_filename TEXT")
    db.commit()


with app.app_context():
    if not os.path.exists(DATABASE):
        init_db()
    else:
        ensure_db_schema()


@app.route("/")
def home():
    if g.user:
        return redirect(url_for("tracker"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        user = query_db("SELECT * FROM users WHERE username = ?", (username,), one=True)
        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Invalid username or password.", "error")
        else:
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("tracker"))
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm = request.form["confirm_password"]
        if not username or not password:
            flash("Username and password are required.", "error")
        elif password != confirm:
            flash("Passwords do not match.", "error")
        elif query_db("SELECT id FROM users WHERE username = ?", (username,), one=True):
            flash("Username is already taken.", "error")
        else:
            db = get_db()
            db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, generate_password_hash(password)),
            )
            db.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/account", methods=["GET", "POST"])
def account():
    if g.user is None:
        return redirect(url_for("login"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        if not username:
            flash("Username cannot be empty.", "error")
        elif username != g.user["username"] and query_db("SELECT id FROM users WHERE username = ?", (username,), one=True):
            flash("Username is already taken.", "error")
        elif new_password and new_password != confirm_password:
            flash("New passwords do not match.", "error")
        elif new_password and not check_password_hash(g.user["password_hash"], current_password):
            flash("Current password is incorrect.", "error")
        else:
            db = get_db()
            db.execute("UPDATE users SET username = ? WHERE id = ?", (username, g.user["id"]))
            if new_password:
                db.execute(
                    "UPDATE users SET password_hash = ? WHERE id = ?",
                    (generate_password_hash(new_password), g.user["id"]),
                )
            db.commit()
            flash("Account updated successfully.", "success")
            return redirect(url_for("account"))
    return render_template("account.html", user=g.user)


@app.route("/locations", methods=["GET", "POST"])
def locations():
    if g.user is None:
        return redirect(url_for("login"))
    location = query_db("SELECT * FROM locations WHERE user_id = ?", (g.user["id"],), one=True)
    if location is None:
        return redirect(url_for("setup"))
    fishes = query_db("SELECT * FROM fish WHERE location_id = ? ORDER BY id", (location["id"],))
    if request.method == "POST":
        location_name = request.form.get("location_name", "").strip()
        location_desc = request.form.get("location_desc", "").strip()
        file_field = request.files.get("location_image")
        filename = location["image_filename"]
        if file_field and allowed_file(file_field.filename):
            filename = secure_filename(f"{g.user['id']}_location_{file_field.filename}")
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file_field.save(file_path)
        if not location_name:
            flash("Location name cannot be empty.", "error")
            return redirect(url_for("locations"))
        db = get_db()
        db.execute("UPDATE locations SET name = ?, description = ?, image_filename = ? WHERE id = ?", (location_name, location_desc, filename, location["id"]))
        for fish in fishes:
            fish_name = request.form.get(f"fish_name_{fish['id']}", "").strip() or fish["name"]
            fish_desc = request.form.get(f"fish_desc_{fish['id']}", "").strip()
            file_field = request.files.get(f"fish_image_{fish['id']}")
            fish_filename = fish["image_filename"]
            if file_field and allowed_file(file_field.filename):
                fish_filename = secure_filename(f"{g.user['id']}_fish_{fish['id']}_{file_field.filename}")
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], fish_filename)
                file_field.save(file_path)
            db.execute(
                "UPDATE fish SET name = ?, description = ?, image_filename = ? WHERE id = ?",
                (fish_name, fish_desc, fish_filename, fish["id"]),
            )
        new_fish_count = int(request.form.get("new_fish_count", 0))
        for index in range(1, new_fish_count + 1):
            fish_name = request.form.get(f"fish_name_new_{index}", "").strip()
            fish_desc = request.form.get(f"fish_desc_new_{index}", "").strip()
            file_field = request.files.get(f"fish_image_new_{index}")
            if not fish_name and not fish_desc and (file_field is None or file_field.filename == ""):
                continue
            fish_filename = None
            if file_field and allowed_file(file_field.filename):
                fish_filename = secure_filename(f"{g.user['id']}_fish_new_{index}_{file_field.filename}")
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], fish_filename)
                file_field.save(file_path)
            if not fish_name:
                fish_name = f"Fish {len(fishes) + index}"
            db.execute(
                "INSERT INTO fish (location_id, name, description, image_filename) VALUES (?, ?, ?, ?)",
                (location["id"], fish_name, fish_desc, fish_filename),
            )
        db.commit()
        flash("Location details updated.", "success")
        return redirect(url_for("locations"))
    return render_template("locations.html", location=location, fishes=fishes, body_class="locations-page")


@app.route("/setup", methods=["GET", "POST"])
def setup():
    if g.user is None:
        return redirect(url_for("login"))
    location = query_db("SELECT * FROM locations WHERE user_id = ?", (g.user["id"],), one=True)
    if location:
        return redirect(url_for("tracker"))
    if request.method == "POST":
        location_name = request.form.get("location_name", "").strip()
        location_desc = request.form.get("location_desc", "").strip()
        fish_count = int(request.form.get("fish_count", 0))
        file_field = request.files.get("location_image")
        location_filename = None
        if file_field and allowed_file(file_field.filename):
            location_filename = secure_filename(f"{g.user['id']}_location_{file_field.filename}")
            location_path = os.path.join(app.config["UPLOAD_FOLDER"], location_filename)
            file_field.save(location_path)
        if not location_name or fish_count <= 0:
            flash("Location name and number of fish are required.", "error")
            return redirect(url_for("setup"))
        db = get_db()
        cur = db.execute(
            "INSERT INTO locations (user_id, name, fish_count, description, image_filename) VALUES (?, ?, ?, ?, ?)",
            (g.user["id"], location_name, fish_count, location_desc, location_filename),
        )
        location_id = cur.lastrowid
        for index in range(1, fish_count + 1):
            fish_name = request.form.get(f"fish_name_{index}", "").strip()
            fish_desc = request.form.get(f"fish_desc_{index}", "").strip()
            file_field = request.files.get(f"fish_image_{index}")
            filename = None
            if file_field and allowed_file(file_field.filename):
                filename = secure_filename(f"{g.user['id']}_fish_{index}_{file_field.filename}")
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                file_field.save(file_path)
            db.execute(
                "INSERT INTO fish (location_id, name, description, image_filename) VALUES (?, ?, ?, ?)",
                (location_id, fish_name or f"Fish {index}", fish_desc, filename),
            )
        db.commit()
        flash("Location setup completed.", "success")
        return redirect(url_for("tracker"))
    return render_template("setup.html")


@app.route("/tracker")
def tracker():
    if g.user is None:
        return redirect(url_for("login"))
    location = query_db("SELECT * FROM locations WHERE user_id = ?", (g.user["id"],), one=True)
    if location is None:
        return redirect(url_for("setup"))
    date_value = request.args.get("date")
    try:
        selected_date = date.fromisoformat(date_value) if date_value else date.today()
    except ValueError:
        selected_date = date.today()
    rows = query_db(
        "SELECT * FROM fish WHERE location_id = ? ORDER BY id", (location["id"],)
    )
    selected_date_str = selected_date.isoformat()
    logs = {
        row["fish_id"]: row["pellets"]
        for row in query_db(
            "SELECT fish_id, pellets FROM food_logs WHERE date = ? AND fish_id IN (SELECT id FROM fish WHERE location_id = ?)",
            (selected_date_str, location["id"]),
        )
    }
    fishes = []
    for row in rows:
        fish = dict(row)
        fish["today_count"] = logs.get(fish["id"], 0)
        fish["image_url"] = url_for("uploaded_file", filename=fish["image_filename"]) if fish["image_filename"] else url_for("static", filename="default-fish.svg")
        fishes.append(fish)
    prev_date = (selected_date - timedelta(days=1)).isoformat()
    next_date = (selected_date + timedelta(days=1)).isoformat()
    location_image = url_for("uploaded_file", filename=location["image_filename"]) if location["image_filename"] else url_for("static", filename="default-location.svg")
    return render_template(
        "tracker.html",
        location=location,
        fishes=fishes,
        selected_date=selected_date_str,
        prev_date=prev_date,
        next_date=next_date,
        location_image=location_image,
        body_class="tracker-page",
    )


@app.route("/dashboard")
def dashboard():
    if g.user is None:
        return redirect(url_for("login"))
    location = query_db("SELECT * FROM locations WHERE user_id = ?", (g.user["id"],), one=True)
    if location is None:
        return redirect(url_for("setup"))
    fish_list = query_db("SELECT * FROM fish WHERE location_id = ? ORDER BY id", (location["id"],))
    labels = []
    dataset_map = {}
    rows = query_db(
        "SELECT date, fish_id, pellets FROM food_logs WHERE fish_id IN (SELECT id FROM fish WHERE location_id = ?) ORDER BY date", (location["id"],)
    )
    for row in rows:
        if row["date"] not in labels:
            labels.append(row["date"])
        dataset_map.setdefault(row["fish_id"], {})[row["date"]] = row["pellets"]
    labels.sort()
    datasets = []
    colors = ["#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f", "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ac"]
    for idx, fish in enumerate(fish_list):
        series = [dataset_map.get(fish["id"], {}).get(day, 0) for day in labels]
        datasets.append({
            "label": fish["name"],
            "data": series,
            "borderColor": colors[idx % len(colors)],
            "backgroundColor": colors[idx % len(colors)],
            "fill": False,
        })
    return render_template("dashboard.html", location=location, labels=labels, datasets=datasets)


@app.route("/api/log", methods=["POST"])
def save_log():
    if g.user is None:
        return jsonify({"error": "Unauthorized"}), 401
    payload = request.json or {}
    logs = []
    if payload.get("fish_logs"):
        logs = payload["fish_logs"]
    else:
        logs = [{
            "fish_id": payload.get("fish_id"),
            "pellets": payload.get("pellets", 0),
            "date": payload.get("date", date.today().isoformat()),
        }]
    db = get_db()
    saved = []
    for item in logs:
        fish_id = item.get("fish_id")
        try:
            pellets = int(item.get("pellets", 0))
        except (TypeError, ValueError):
            pellets = 0
        log_date = item.get("date") or payload.get("date") or date.today().isoformat()
        fish = query_db(
            "SELECT fish.* FROM fish JOIN locations ON fish.location_id = locations.id WHERE fish.id = ? AND locations.user_id = ?",
            (fish_id, g.user["id"]),
            one=True,
        )
        if fish is None:
            continue
        existing = query_db(
            "SELECT id FROM food_logs WHERE fish_id = ? AND date = ?", (fish_id, log_date), one=True
        )
        if existing:
            db.execute(
                "UPDATE food_logs SET pellets = ? WHERE id = ?", (pellets, existing["id"])
            )
        else:
            db.execute(
                "INSERT INTO food_logs (fish_id, date, pellets) VALUES (?, ?, ?)",
                (fish_id, log_date, pellets),
            )
        saved.append({"fish_id": fish_id, "pellets": pellets})
    db.commit()
    return jsonify({"success": True, "saved": saved})


if __name__ == "__main__":
    if not os.path.exists(DATABASE):
        init_db()
    app.run(host="0.0.0.0", port=5000)
