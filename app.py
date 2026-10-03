from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
app.config["SECRET_KEY"] = "spendly-dev-secret-key"

with app.app_context():
    init_db()
    seed_db()


def get_logged_in_user():
    user_id = session.get("user_id")
    if not user_id:
        return None

    conn = get_db()
    user = conn.execute(
        "SELECT id, name, email FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    return user


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("profile"))
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or not password:
            return render_template("register.html", error="Please fill in all fields."), 400

        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters long."), 400

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,),
        ).fetchone()

        if existing:
            conn.close()
            return render_template("register.html", error="An account with that email already exists."), 400

        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT id, name, email, password_hash FROM users WHERE email = ?",
            (email,),
        ).fetchone()
        conn.close()

        if user is None or not check_password_hash(user["password_hash"], password):
            return render_template("login.html", error="Invalid email or password."), 401

        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        return redirect(url_for("profile"))

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/profile")
def profile():
    user = get_logged_in_user()
    if user is None:
        return redirect(url_for("login"))

    conn = get_db()
    expenses = conn.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user["id"],),
    ).fetchall()
    total = sum(float(item["amount"]) for item in expenses)
    conn.close()

    return render_template("profile.html", user=user, expenses=expenses, total=total)


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    user = get_logged_in_user()
    if user is None:
        return redirect(url_for("login"))

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        date = request.form.get("date", "").strip()

        if not category or not amount or not date:
            return render_template(
                "expense_form.html",
                expense=None,
                action="Add",
                error="Category, amount, and date are required.",
            ), 400

        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (user_id, category, amount, description, date) VALUES (?, ?, ?, ?, ?)",
            (user["id"], category, float(amount), description, date),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("profile"))

    return render_template("expense_form.html", expense=None, action="Add")


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    user = get_logged_in_user()
    if user is None:
        return redirect(url_for("login"))

    conn = get_db()
    expense = conn.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (id, user["id"]),
    ).fetchone()
    conn.close()

    if expense is None:
        return redirect(url_for("profile"))

    if request.method == "POST":
        category = request.form.get("category", "").strip()
        amount = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()
        date = request.form.get("date", "").strip()

        if not category or not amount or not date:
            return render_template(
                "expense_form.html",
                expense=expense,
                action="Edit",
                error="Category, amount, and date are required.",
            ), 400

        conn = get_db()
        conn.execute(
            "UPDATE expenses SET category = ?, amount = ?, description = ?, date = ? WHERE id = ? AND user_id = ?",
            (category, float(amount), description, date, id, user["id"]),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("profile"))

    return render_template("expense_form.html", expense=expense, action="Edit")


@app.route("/expenses/<int:id>/delete", methods=["GET", "POST"])
def delete_expense(id):
    user = get_logged_in_user()
    if user is None:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM expenses WHERE id = ? AND user_id = ?",
        (id, user["id"]),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
