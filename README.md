# Secure IT Helpdesk Ticketing System

A clean, portfolio-ready Django MVP for internal IT helpdesk and incident ticket workflow management. The project is designed to run as a normal Django app first, with SQLite for the easiest local setup. Docker/PostgreSQL support is optional for people who want it later. The project focuses on role-based access control, audit logging, secure-by-default configuration, email notifications, and a professional Bootstrap 5 interface with dark green security-oriented branding.

## Features

- Built-in Django authentication with login, logout, and registration.
- Profile-based roles: `user`, `support`, and `admin`.
- Normal users can create tickets, view only their own tickets, and comment on their own tickets.
- Support and admin users can view all tickets, filter tickets, assign staff, update status/priority, comment, and review audit logs.
- Ticket workflow statuses: open, in progress, pending, resolved, and closed.
- Priority levels: low, medium, high, and critical.
- Category management through Django Admin.
- Console email notification when a ticket status changes, with SMTP-ready environment variables.
- Audit logging for ticket creation, comments, status changes, priority changes, and assignment changes.
- File attachment validation with a 5 MB limit and common document/image type allowlist.
- Seed command for realistic demo data.
- Local-first SQLite setup that only requires Django; optional Docker Compose/PostgreSQL setup remains available.
- GitHub Actions workflow for checks, migrations, and tests.

## Screenshots

> Add screenshots here after running the app locally.

- Dashboard: `docs/screenshots/dashboard.png`
- Ticket detail and audit log: `docs/screenshots/ticket-detail.png`
- Ticket list filters: `docs/screenshots/ticket-list.png`

## Tech Stack

- **Backend:** Django
- **Frontend:** Django Templates
- **Styling:** Bootstrap 5 and custom CSS
- **Database:** SQLite by default for local Django setup; optional PostgreSQL with `DATABASE_URL`
- **Testing:** Django `TestCase`
- **Automation:** GitHub Actions
- **Containerization:** Optional Docker and Docker Compose
- **Configuration:** environment variables via `.env` / `.env.example`

## Architecture Overview

```text
config/      Django settings, URLs, ASGI/WSGI
accounts/    Registration and Profile role model
tickets/     Ticket models, forms, views, tests, admin, seed command
templates/   Shared and app-specific Django templates
static/      Custom CSS and static assets
media/       Local upload target for ticket attachments
```

The app intentionally uses simple function-based views and Django forms so the business rules are easy to inspect. Permission checks are enforced in views rather than only by hiding buttons in templates.

## Quick Start: Fully Django, No Docker Required

> **Important:** run Django commands from the project folder that contains `manage.py`. The most common command form is `python manage.py migrate` or `py manage.py migrate` on Windows. A detailed Windows troubleshooting guide is available at [`docs/WINDOWS_SETUP.md`](docs/WINDOWS_SETUP.md).

### Windows PowerShell

```powershell
cd D:\HOC\secure-IT-helpdesk-ticketing-system
py -m venv .venv
.\.venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements-local.txt
Copy-Item .env.example .env
py manage.py migrate
py manage.py seed_demo
py manage.py runserver
```

Then open <http://127.0.0.1:8000/>.

If your terminal command starts with `python -m manage.py`, it will fail because `manage.py` is a script filename, not a Python package path. The most common command is:

```powershell
py manage.py migrate
```

If `py` is not available on your Windows machine, use `python` instead:

```powershell
python manage.py migrate
```

### macOS / Linux

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements-local.txt
   ```

3. Create your local environment file:

   ```bash
   cp .env.example .env
   ```

4. For quick local setup, leave `DATABASE_URL` blank to use SQLite.

5. Run migrations and seed demo data:

   ```bash
   python manage.py migrate
   python manage.py seed_demo
   ```

6. Start the development server:

   ```bash
   python manage.py runserver
   ```

7. Open <http://127.0.0.1:8000/>.

## Optional Setup With Docker

Docker is not required for normal local use. If you already know Docker and want PostgreSQL, build and start the app with:

   ```bash
   docker compose up --build
   ```

2. In another terminal, seed demo data if desired:

   ```bash
   docker compose exec web python manage.py seed_demo
   ```

3. Open <http://127.0.0.1:8000/>.

## Environment Variables

| Variable | Purpose | Default / Notes |
| --- | --- | --- |
| `SECRET_KEY` | Django secret key | Must be changed for production |
| `DEBUG` | Enables debug mode | Use `False` for production |
| `ALLOWED_HOSTS` | Comma-separated hosts | `localhost,127.0.0.1` |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated trusted origins | Blank by default |
| `DATABASE_URL` | PostgreSQL connection string | Blank uses SQLite |
| `EMAIL_BACKEND` | Django email backend | Console backend by default |
| `EMAIL_HOST` / `EMAIL_PORT` | SMTP server details | SMTP-ready |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | SMTP credentials | Do not commit real secrets |
| `EMAIL_USE_TLS` | SMTP TLS toggle | `True` |
| `DEFAULT_FROM_EMAIL` | Sender address | Helpdesk default |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | Secure cookie flags | Enable behind HTTPS |

## Common Command Mistakes

### `No module named manage`

This usually means one of two things:

1. You are not inside the project folder that contains `manage.py`. Run `dir` on Windows or `ls` on macOS/Linux and confirm that `manage.py` is visible.
2. You used the wrong command form or are not in the project root. Use `python manage.py migrate` or `py manage.py migrate`. Do **not** use `python -m manage.py migrate`.

Correct Windows example:

```powershell
cd D:\HOC\secure-IT-helpdesk-ticketing-system
py manage.py migrate
```

Correct macOS/Linux example:

```bash
cd /path/to/secure-IT-helpdesk-ticketing-system
python manage.py migrate
```

### `ModuleNotFoundError: No module named 'dj_database_url'`

The current local SQLite setup does not require `dj_database_url`. If you see an error pointing to `import dj_database_url` in `config/settings.py`, your local copy is stale or Python is running a different copy of the project. Pull the latest code and confirm that the top of `config/settings.py` imports only standard-library settings helpers. See [`docs/WINDOWS_SETUP.md`](docs/WINDOWS_SETUP.md) for the exact fix.

### Python 3.14 note

If dependency installation fails with a brand-new Python version, install a stable Python version commonly supported by Django, such as Python 3.12, create a fresh virtual environment, and rerun the local setup commands.

## Demo Accounts

Run `python manage.py seed_demo` first.

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin12345` |
| Support | `support` | `support12345` |
| User | `user1` | `user12345` |
| User | `user2` | `user12345` |

Admin users can also access Django Admin at `/admin/`.

## Running Tests

After activating your virtual environment and installing dependencies:

```bash
python manage.py check
python manage.py test
```

The tests cover ticket creation, ticket access control, support visibility, status updates, audit log creation, email notification, comments, and basic list filtering.

## Security Features

This MVP applies OWASP ASVS Level 1 inspired basics:

- Django CSRF protection on forms.
- Login required for all protected ticket pages.
- View-level role and ownership checks for ticket access.
- Server-side enforcement for support/admin ticket management.
- Environment-driven secrets, debug mode, database, and email settings.
- No real secrets committed to the repository.
- HTTP-only session and CSRF cookies.
- Clickjacking protection with `X_FRAME_OPTIONS = DENY`.
- Content type sniffing protection.
- Attachment size and type validation.
- Audit logs for important ticket actions.

## Project Scope

This is intentionally an MVP. It does **not** include chat, real-time notifications, payment features, React, complex analytics, or enterprise workflow automation. The goal is a professional, understandable Django codebase that demonstrates secure backend logic and complete end-to-end ticket handling.

## Future Improvements

- Password reset email flow.
- Pagination for large ticket queues.
- More advanced reporting exports.
- Per-team assignment queues.
- Production static file serving with WhiteNoise or object storage.
- Optional virus scanning for attachments.
- More granular permission model using Django groups.

## Portfolio Summary

Secure IT Helpdesk Ticketing System is a Django portfolio MVP demonstrating role-based access control, audit logging, status workflow management, secure configuration practices, simple SQLite-first local development, optional Dockerized PostgreSQL deployment, and meaningful automated tests. It is designed to be easy to run, easy to review, and realistic enough to represent an internal IT support application.
