#!/usr/bin/env python
import importlib.util
import os
import sys


def should_auto_migrate(argv):
    disabled_values = {"1", "true", "yes", "on"}
    auto_migrate_disabled = os.getenv("DISABLE_AUTO_MIGRATE", "").lower() in disabled_values
    return len(argv) > 1 and argv[1] == "runserver" and not auto_migrate_disabled


def run_pending_migrations_for_local_server():
    import django
    from django.core.management import call_command
    from django.db import DEFAULT_DB_ALIAS, connections
    from django.db.migrations.executor import MigrationExecutor

    django.setup()
    connection = connections[DEFAULT_DB_ALIAS]
    executor = MigrationExecutor(connection)
    targets = executor.loader.graph.leaf_nodes()
    plan = executor.migration_plan(targets)
    if plan:
        print("Applying pending migrations before starting the development server...")
        call_command("migrate", interactive=False)


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secure_helpdesk.settings")
    if importlib.util.find_spec("django") is None:
        raise ModuleNotFoundError(
            "Django is not installed in this Python environment. "
            "Activate your virtual environment and run: python -m pip install -r requirements.txt"
        )
    if should_auto_migrate(sys.argv):
        run_pending_migrations_for_local_server()

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
