# ExTerminus Architecture

This document explains how ExTerminus is structured internally and how data flows throught he system.  It is intended to reduce cognitive load when making changes or debugging issues.

---

## High-Level Request Flow

1. HTTP request arrives (browser or API)
2. Flask route handles request
3. Route delegates to a service (business logic)
4. Service interacts with database helpers
5. Data returned to route
6. Route renders a template or returns a response

Routes should remain thin.
Services contain logic.
Templates remain mostly presentation-only.

---

## Core Entry Point

### `app.py`

- Defines `create_app()`
- Registers:
  - Flask app
  - context processors
  - routes
- At import time:
  ```python
  app = create_app()
  ```
    This allows gunicorn to load the app via `app:app`.

## Configuration

### `config.py`

- Central location for application configuration
- Reads environment variables where applicable
- Should be the **only** place that knows about environment differences

## Routes Layer

### `/routes`

Purpose:
- HTTP concerns only
- Validate input
- Call services
- Choose templates/responses

Examples:
- authentication routes
- calendar views
- job creation/editing
- admin-only actions

Routes should **not**:
- Contain pricing logic
- Contain scheduling logic
- Contain raw SQL (except in rare edge cases)

---

## Services Layer

### `/services`

Purpose:
- Business logic
- Domain rules
- Cross-route reuse

Examples:
- job creation logic
- scheduling calculations
- pricing rules
- permissions checks

If logic is used in more than one route, it belongs here.

---

## Database Layer

### `db.py`

Purpose:
- Handles database connections
- Creates/handles cursors
- Helpers for queries

SQLite backend

Design intent:
- Routes and services should not manage connections directly
- DB access should be centralized

---

## Templates

### `/templates`

- Jinja2 templates
- Receive fully-prepared data
- Should avoid complex logic

Context processors inject:
- user identity
- role
- current date/time
- app version

---

## Static Assets

### `/static`

- CSS
- JS
- images

No build step assumed (served directly).

---

## Instance Data

### `/instance`

- SQLite database
- Local-only, environment-specific
- Not tracked in git

---

## Migrations

### `/migrations`

- SQL files
- Named sequentially
- Applied manually or via script

This keeps schema changes explicit and auditable.

---

## Design Invariants

These assumptions should remain true unless deliberately changed:
- ExTerminus is a **single-host application**
- Only one process writes to SQLite Database
- gunicorn is the sole WSGI server
- routes are thin, services are fat
- templates are dumb

Violating these invariants requires design changes elsewhere.

---

## Common Change Patterns

### Adding a new job type

1. Add schema changes (migration if needed)
2. Update service logic
3. Update route handling
4. Update templates
5. Update docs if behavior changes

### Debugging a production issue

1. Check `journald` logs
2. Reproduce locally if possible
3. Inspect services layer
4. Verify DB state

