# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
pip install -r requirements.txt       # Flask, Werkzeug, pytest, pytest-flask
python3 app.py                        # dev server on http://127.0.0.1:5001 (debug=True, auto-reloads)
python3 -m pytest                     # run all tests
python3 -m pytest tests/test_app.py::test_profile_page_shows_expenses   # single test
```

There is no linter, build step, or JS bundler configured.

**Tests hit the real dev database.** `tests/test_app.py` imports `app`, which runs `init_db()`/`seed_db()` against `database/expense_tracker.db`; there is no temp-DB fixture. `test_register_and_login_flow` registers `alice@example.com`, so it passes on a fresh DB and fails with `400 == 200` on every later run until that user is deleted.

## Architecture

Spendly is a small server-rendered Flask expense tracker. There's no JS framework: pages are Jinja2 templates, and any interactivity is vanilla JS placed inline in a template's `{% block scripts %}` (`static/js/main.js` is an empty placeholder).

- **`app.py`** holds every route. There are no blueprints and no ORM. Each handler opens a connection with `get_db()`, runs raw parameterized SQL, and closes it explicitly.
- **Auth** is session-based: `session["user_id"]` and `session["user_name"]` are set on login, and passwords are hashed with Werkzeug. Protected routes call `get_logged_in_user()` and redirect to `/login` when it returns `None`. Expense queries always filter by `user_id` so users only see their own rows. `/` redirects logged-in users to `/profile`.
- **Expense CRUD:** `/expenses/add` and `/expenses/<id>/edit` share `expense_form.html`, which is driven by the `expense` variable (`None` when adding) and `action` (`"Add"` or `"Edit"`). If a form fails validation, the route re-renders the form with `error=...` and status 400. Edit and delete match on both `id` and `user_id`, so a request for another user's expense silently redirects to `/profile`. `/profile` computes the total in Python, not SQL.
- **`database/db.py`**:
  - `get_db()` returns a SQLite connection with `sqlite3.Row` and foreign keys enabled.
  - `init_db()` creates the `users` and `expenses` tables (`expenses.user_id` cascades on delete).
  - `seed_db()` inserts a demo user (`demo@spendly.com` / `demo123`) with sample expenses if that user is missing.
  - Both `init_db()` and `seed_db()` run when `app.py` is imported. The `.db` file is gitignored.
- **Templates:** everything extends `templates/base.html`, which provides the navbar, footer (including the Terms/Privacy links) and the blocks `title`, `head`, `content` and `scripts`. The legal pages (`terms.html`, `privacy.html`) reuse the profile-page layout classes plus the `.legal-*` classes.
- **Styling:**
  - `static/css/style.css` is the global stylesheet. It defines the design tokens as CSS variables in `:root`:
    - colors: `--ink*`, `--paper*`, `--accent*` and `--border*`
    - radii: `--radius-sm/md/lg`
    - fonts: `--font-display` (DM Serif Display) and `--font-body` (DM Sans)
  - It also has a global reset (`* { margin: 0; padding: 0 }`, and unstyled `a`), so new markup needs explicit spacing.
  - Page-specific CSS goes in its own file, loaded through `{% block head %}`. For example, `landing.css` holds the `lh-*` hero classes and the "See how it works" video modal.
  - The older `.hero` and `.mock-*` rules in `style.css` are no longer used by the landing page.

## Working conventions

- Keep changes scoped to exactly what is asked. Requests often say "do not modify any other part of the page", so don't refactor surrounding markup or CSS.
- Match the existing theme by using the CSS variables rather than hard-coded colors where possible.
- Commit messages follow the `area: short description` style (e.g. `landing: add privacy policy page and route`).
