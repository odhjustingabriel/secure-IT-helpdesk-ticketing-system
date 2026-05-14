# Windows PowerShell Setup Guide

This project runs as a normal Django application. Docker is optional and is **not** required for the local SQLite setup.

## Correct setup from a fresh clone

Open PowerShell and run these commands from the folder that contains `manage.py`:

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

If the `py` launcher is not available, replace `py` with `python`:

```powershell
python manage.py migrate
```

## About `python -m manage migrate`

`python -m manage migrate` can work only when your current directory is the project root. The more common Django command is:

```powershell
py manage.py migrate
```

Both forms should use the same current project files. If one command works differently from the other, confirm your PowerShell prompt is inside the project folder and that your virtual environment is activated.

## Fix: `ModuleNotFoundError: No module named 'dj_database_url'`

Current versions of this project do **not** require `dj_database_url` for the local SQLite setup. If you see this traceback:

```text
File "...\config\settings.py", line 4, in <module>
    import dj_database_url
ModuleNotFoundError: No module named 'dj_database_url'
```

then your local files are not updated to the current project version, or Python is running an older copy of the project.

Check `config/settings.py`. The top of the current file should look like this:

```python
import os
from pathlib import Path
from urllib.parse import urlparse
```

There should be no `import dj_database_url` line.

### Recommended fix

1. Make sure you are in the correct folder:

   ```powershell
   cd D:\HOC\secure-IT-helpdesk-ticketing-system
   dir manage.py
   dir config\settings.py
   ```

2. If this is a Git clone, pull the latest changes:

   ```powershell
   git pull
   ```

3. Reinstall the local dependencies in your virtual environment:

   ```powershell
   .\.venv\Scripts\Activate.ps1
   py -m pip install -r requirements-local.txt
   ```

4. Run migrations again:

   ```powershell
   py manage.py migrate
   ```

### Alternative fix if you intentionally want the full dependency set

For PostgreSQL or production-style installs, install the full requirements file:

```powershell
py -m pip install -r requirements.txt
```

The simple local path should still use `requirements-local.txt`.

## Python 3.14 note

If Django or database adapter installation fails on Python 3.14, install Python 3.12, recreate the virtual environment, and rerun the setup commands. Python 3.12 is a safe choice for this project.
