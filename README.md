# Secure IT Helpdesk Ticketing System

A clean, beginner-friendly Django app for internal IT support and incident ticketing. The project uses Django, Django Templates, SQLite, console email, and custom CSS only, making it easy to run locally.

## Features

- Registration, login, logout, and authenticated change-password flow using Django authentication.
- Profile-based roles: `user`, `support`, and `admin`, with support staff kept out of admin-only Django Admin tools.
- Normal users can create tickets, view their own tickets, and comment on their own tickets.
- Support/admin users can view all tickets, filter queues, update status/priority, assign tickets to staff, comment, add internal notes, tag tickets, and view audit logs.
- Admin users can manage profiles, user roles, active/inactive categories, tickets, comments, and audit logs in Django Admin. Superusers can view password-hash metadata, but plaintext passwords and full stored hashes are never exposed.
- Ticket statuses: open, in progress, pending, resolved, closed.
- Priority badges: low, medium, high, critical.
- Optional ticket attachments with a 5 MB limit and safe extension allowlist.
- Console email notification when staff/admin changes ticket status.
- Audit logs for ticket creation, public comments, internal notes, first responses, status changes, priority changes, assignment changes, tags, and resolution note changes.
- SLA due dates are generated from ticket priority, with overdue indicators for staff queues.
- Support staff can use active canned responses and private internal notes to speed up common workflows.
- Admins can deactivate old categories without deleting historical ticket data.
- Support/admin users must provide a resolution note when resolving or closing a ticket.
- Demo data seed command with repeat-safe user/category creation.
- Real Django `TestCase` coverage for roles, permissions, workflow, filters, audit logs, and email.

## Tech Stack

- **Backend:** Django
- **Frontend:** Django Templates
- **Database:** SQLite
- **Styling:** Custom CSS
- **Testing:** Django `TestCase`
- **Email:** Django console email backend
- **Configuration:** small `.env.example` with optional local overrides

## Screenshots

Add screenshots after running the app locally:

- Dashboard: `docs/screenshots/dashboard.png`
- Ticket list filters: `docs/screenshots/ticket-list.png`
- Ticket detail with audit log: `docs/screenshots/ticket-detail.png`

## Project Structure

```text
secure_helpdesk/
├── manage.py
├── secure_helpdesk/        # Django project settings and URLs
├── accounts/               # Profile role model, registration, permission helpers
├── tickets/                # Ticket models, forms, views, admin, tests, seed command
├── templates/              # Base, auth, and ticket templates
├── static/css/style.css    # Custom white/green UI styling
├── media/                  # Local uploaded attachments (ignored by git)
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Local Setup

### 1. Create and activate a virtual environment

Windows:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Mac/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. Optional environment file

```bash
cp .env.example .env
```

The app runs without this file because safe local defaults are provided in settings.

### 4. Run migrations

```bash
python manage.py migrate
```

> Tip: `python manage.py runserver` also checks for pending migrations and applies them before the local development server starts.
> If you pulled new code and see a database column error, stop the server and run either `python manage.py migrate` or `python manage.py runserver` again.

### 5. Seed demo data

```bash
python manage.py seed_demo
```

### 6. Start the server

```bash
python manage.py runserver
```

Open <http://127.0.0.1:8000/>.

## Create a Superuser

```bash
python manage.py createsuperuser
```

Superusers automatically receive an admin profile role when created.

## Demo Accounts

Run `python manage.py seed_demo` first.

| Role | Username | Password |
| --- | --- | --- |
| Admin | `admin` | `admin12345` |
| Support | `support` | `support12345` |
| User | `user1` | `user12345` |
| User | `user2` | `user12345` |

Django Admin is available at `/admin/`.

## Role Separation

Roles are stored on `accounts.Profile.role` and are intentionally separate from Django's built-in `is_staff` flag:

| Profile role | Purpose | Ticket access | Django Admin access |
| --- | --- | --- | --- |
| `user` | Requester/end user | Own tickets only | No |
| `support` | Helpdesk staff | All tickets, ticket management, internal notes, canned responses | No |
| `admin` | Helpdesk administrator | All support workflow features | Yes |

In code, `is_support_or_admin(user)` grants helpdesk workflow access to support and admin roles, while `is_admin_role(user)` gates `/admin/` to admin-role users and superusers only. The ticket assignment queryset intentionally includes only active `support` users so admins stay separate from day-to-day ticket ownership.

## Run Tests

```bash
python manage.py check
python manage.py test
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'django'`

This means your virtual environment is active but Django has not been installed into it yet, or your terminal is using a different Python interpreter than the one where dependencies were installed. From the project root, run:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
```

On Windows, if you use the Python launcher, make sure it points at the same environment. The easiest option after activation is usually:

```bash
python manage.py migrate
```

If dependency installation fails on a very new Python version, use a stable Python version supported by Django 5.2, such as Python 3.12 or 3.13.

### `OperationalError: no such column` after pulling updates

This means your local SQLite database schema is behind the Django models. Stop the development server, run migrations, and start it again.
The development server now applies pending migrations automatically, but running `migrate` explicitly is always safe:

```bash
python manage.py migrate
python manage.py runserver
```

For the latest demo data after migrations, you can also run:

```bash
python manage.py seed_demo
```

## Security Features

- CSRF protection is enabled through Django middleware and template tokens.
- Baseline request anomaly filtering blocks common injection/XSS/path-traversal signatures before view processing.
- Login is required for ticket pages.
- Role and ownership checks are enforced inside views, not only in templates.
- Normal users receive HTTP 403 if they attempt to access another user's ticket.
- Only support/admin users can reach ticket management views; only admin-role users or superusers can enter Django Admin.
- Django messages provide clear success and error feedback.
- Attachments are optional, size-limited, and extension-validated.
- Attachments are also constrained by content type, and executable (`MZ`) signatures are rejected.
- No real secrets are committed; `.env` is ignored.
- Rate limiting applies globally and also per-account on auth routes; production deployments can use a shared cache backend (for example Redis) for multi-instance consistency.
- SQLite database and uploaded media are ignored by git.
- Audit logs record important ticket actions.
- Admins manage user roles through Django Admin profile records, not through a public user-facing page. Authenticated users can change their own passwords from the navigation bar.
- Django stores password hashes only; admins cannot view plaintext user passwords and should reset passwords when access recovery is needed.
- Inactive categories are hidden from new ticket forms while existing tickets keep their historical category.
- Resolution notes are required before staff/admin users can resolve or close tickets.
- Internal notes stay hidden from normal users and are audit logged for staff collaboration.

## OWASP Top 10 Mitigation Snapshot

- **A01 Broken Access Control:** Enforced object-level ownership checks and role-based guards in views/admin.
- **A02 Cryptographic Failures:** Secret key required in non-debug mode; secrets are environment-driven.
- **A03 Injection:** ORM usage plus baseline anomaly filtering for obvious injection patterns.
- **A04 Insecure Design:** Explicit auth throttling, request-size limits, and auditable workflow controls.
- **A05 Security Misconfiguration:** Secure headers/cookie options and environment-configurable security settings.
- **A06 Vulnerable Components:** Dependency management via `requirements.txt` (run periodic dependency scans).
- **A07 Identification and Authentication Failures:** Auth route throttling per-IP and per-username.
- **A08 Software and Data Integrity Failures:** Controlled seed/demo behavior via environment and least default exposure.
- **A09 Security Logging and Monitoring Failures:** Audit logs for key ticket actions and workflow state changes.
- **A10 SSRF:** No outbound URL-fetch feature exists in app workflows; avoid adding unsafely proxied fetch features.

## Project Scope

This project is intentionally focused, not an enterprise helpdesk suite. It does not use React, Docker, PostgreSQL, Django REST Framework, Celery, Redis, real-time chat, or advanced analytics. The code focuses on Django fundamentals, readable forms/views, role-based access control, and a complete ticket workflow.

## Future Improvements

- Password reset flow for forgotten passwords.
- Pagination for large ticket lists.
- Richer notification preferences.
- Saved filters for support staff.
- Exportable ticket reports.
- Team queues and SLA tracking.
- Virus scanning for uploaded attachments.

## Summary

Secure IT Helpdesk Ticketing System includes authentication, profile roles, secure ticket ownership rules, support staff workflow, audit logging, email notifications, file validation, custom template styling, seed data, and meaningful automated tests.
