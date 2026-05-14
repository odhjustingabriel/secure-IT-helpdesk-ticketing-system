#!/usr/bin/env python
import importlib.util
import os
import sys


def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "secure_helpdesk.settings")
    if importlib.util.find_spec("django") is None:
        raise ModuleNotFoundError(
            "Django is not installed in this Python environment. "
            "Activate your virtual environment and run: python -m pip install -r requirements.txt"
        )
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
