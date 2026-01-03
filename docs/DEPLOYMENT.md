# ExTerminus Deployment (yggdrasil)

This document describes how ExTerminus is deployed on the host `yggdrasil`.  It reflects the **current, working production setup** and should be treated as the canonical reference for recovery, migration, or reinstallation.

## Host Overview

- Hostname: `yggdrasil`
- OS: Debian
- Install path: `/srv/exterminus`
- Python: system Python with virtualenv
- Web server: gunicorn
- Process manager: systemd
- Public access: ngrok tunnel

---

## Users and Permissions

### Admin user
- Primary login user (human)
- Owns the ExTerminus source code
- Used for development, editing, and git operations

### Service user
- User: `exterminus`
- Purpose: runs gunicorn + ngrok
- Does **not** own the codebase
- Owns runtime artifacts:
  - SQLite database
  - logs
  - backups
  - `.env` file

---

## Directory Layout (Top Level)
/srv/exterminus
    |--app.py # Flask app entry point (app = create_app())
    |--config.py # Application configuration
    |--db.py # Database helpers / connection logic
    |--instance/ # Instance-specific data (SQLite DB)
    |--migrations/ # SQL migration scripts
    |--routes/ # Flask route modules
    |--services/ # Business logic / domain services
    |--templates/ # Jinja templates
    |--static/ # CSS / JS / assets
    |--backups/ # DB backups
    |--logs/ # Application logs (if not using journald only)
    |--deploy/ # Deployment-related scripts/templates
    |--scripts/ # Utility/ maintenance scripts
    |--utils/ # Shared helpers
    |--requirements.txt # Python dependencies
    |--pyproject.toml # Packaging/tooling metadata
    |--README.md # Project overview
    |--CHANGELOG.md # Release history

---

## Virtual Environment

- Location: `/srv/exterminus/.venv`
- Owned by: `admin` user
- Used by systemd service directly

Activate manually:
```bash
source /srv/exterminus/.venv/bin/activate
```

---

## Systemd Services

### ExTerminus (gunicorn)
Service file:
```bash
/etc/systemd/system/exterminus.service
```

Key characteristics:
- Runs as user `exterminus`
- Working directory: `/srv/exterminus`
- Uses gunicorn
- Binds to `0.0.0.0:5000`
- Entry point: `app:app`

Typical management commands:
```bash
sudo systemctl status exterminus
sudo systemctl restart exterminus
journalctl -u exterminus -n 200
```

### ExTerminus-ngrok (ngrok tunnel)
Service file:
```bash
/etc/systemd/system/exterminus-ngrok.service
```

Purpose:
- Exposes ExTerminus publicly via ngrok
- Forwards to `http://127.0.0.1:5000`

Management commands:
```bash
sudo systemctl status exterminus-ngrok
sudo systemctl restart exterminus-ngrok
journalctl -u exterminus-ngrok -n 200
```

---

## Environment Configuration
### `/srv/exterminus/.env`
- Owner: `exterminus`
- Mode: `640`
- Contains:
  - `SERVICE_PORT`
  - `DOMAIN` (ngrok domain, if used)
  - Secrets/tokens

**This file is not committed to git.**
A template should live at `deploy/config.example.env`.

---

## Database
- Type: SQLite
- Location: `/srv/exterminus/instance/*.db`
- Owned by: `exterminus`
- Migrations:
  - Stored in `/migrations`
  - Applied manually or via scripts
- Backups:
  - Stored in `/backups`
  - Backup process TBD

---

## Health Checks

### Local
```bash
curl http://127.0.0.1:5000/
```

### Port Check
```bash
ss -tulnp | grep :5000
```

### If ExTerminus is down:
1. Check `systemctl status exterminus`
2. Check logs via `journalctl`
3. Confirm DB permissions
4. Restart service


