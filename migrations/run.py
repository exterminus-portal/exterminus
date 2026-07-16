import argparse
import glob
import os
import sqlite3
import sys


def _connect(db_path: str):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return sqlite3.connect(db_path)


def _ensure_table(conn):
    conn.execute(
        """
    CREATE TABLE IF NOT EXISTS schema_migrations(
        id TEXT PRIMARY KEY,
        applied_at INTEGER NOT NULL,
        meta TEXT
    );
    """
    )
    conn.commit()


def _applied(conn):
    return {row[0] for row in conn.execute("SELECT id FROM schema_migrations")}


def _apply(conn, path):
    sql = open(path, "r", encoding="utf-8").read()
    with conn:
        conn.executescript(sql)
        conn.execute(
            """
            INSERT INTO schema_migrations(id, applied_at, meta)
            VALUES (?, CAST(strftime('%s', 'now') AS INTEGER), NULL)
            """,
            (os.path.basename(path),),
        )


def apply_migrations(
    conn: sqlite3.Connection,
    migration_directory: str | os.PathLike[str],
) -> list[str]:
    """Apply every migration not already recorded."""

    _ensure_table(conn)

    files = sorted(
        glob.glob(
            os.path.join(
                os.fspath(migration_directory),
                "*.sql",
            )
        )
    )
    already_applied = _applied(conn)

    pending = [path for path in files if os.path.basename(path) not in already_applied]

    applied = []

    for path in pending:
        _apply(conn, path)
        applied.append(os.path.basename(path))

    return applied


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True, help="Path to SQLite file")
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(__file__), "sql"))
    args = ap.parse_args()

    conn = _connect(args.db)

    try:
        applied = apply_migrations(
            conn,
            args.dir,
        )
    finally:
        conn.close()

    if not applied:
        print("No new migrations.")
        return 0

    print("Applied:", ", ".join(applied))
    return 0


#    conn = _connect(args.db)
#    _ensure_table(conn)

#    files = sorted(glob.glob(os.path.join(args.dir, "*.sql")))
#    already = _applied(conn)
#    todo = [f for f in files if os.path.basename(f) not in already]

#    if not todo:
#        print("No new migrations.")
#        return 0

#    for f in todo:
#        print(f"Applying {os.path.basename(f)} ...")
#        _apply(conn, f)

#    print("Applied:", ", ".join(os.path.basename(f) for f in todo))
#    return 0


if __name__ == "__main__":
    sys.exit(main())
