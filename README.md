# Secure IT Helpdesk Ticketing System

A clean, portfolio-ready Django MVP for internal IT helpdesk and incident ticket workflow management. The project focuses on role-based access control, audit logging, secure-by-default configuration, email notifications, and a professional Bootstrap 5 interface with dark green security-oriented branding.

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
- Docker Compose with PostgreSQL and SQLite fallback for local development.
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
- **Database:** PostgreSQL via Docker; SQLite fallback when `DATABASE_URL` is not set
- **Testing:** Django `TestCase`
- **Automation:** GitHub Actions
- **Containerization:** Docker and Docker Compose
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

## Setup Without Docker

1. Create a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
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

## Setup With Docker

1. Build and start the app with PostgreSQL:

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

Secure IT Helpdesk Ticketing System is a Django portfolio MVP demonstrating role-based access control, audit logging, status workflow management, secure configuration practices, Dockerized PostgreSQL deployment, and meaningful automated tests. It is designed to be easy to run, easy to review, and realistic enough to represent an internal IT support application.
