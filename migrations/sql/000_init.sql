-- 000_init.sql
-- Initial ExTerminus schema for a new database.

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT,
    last_name TEXT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'tech',
    must_reset_password INTEGER NOT NULL DEFAULT 0,
    last_password_change TEXT
);

CREATE TABLE IF NOT EXISTS technicians (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    start_time TEXT,
    end_time TEXT,
    time_range TEXT,
    job_type TEXT,
    price REAL,
    fumigation_type TEXT,
    target_pest TEXT,
    exclusion_subtype TEXT,
    notes TEXT,
    rei_zip TEXT,
    rei_quantity INTEGER,
    rei_city_name TEXT,
    technician_id INTEGER,
    twoman INTEGER NOT NULL DEFAULT 0,
    is_multiday INTEGER NOT NULL DEFAULT 0,
    created_by INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    last_modified TEXT,
    last_modified_by INTEGER,
    FOREIGN KEY (technician_id)
        REFERENCES technicians(id)
        ON DELETE SET NULL,
    FOREIGN KEY (created_by)
        REFERENCES users(id)
        ON DELETE SET NULL,
    FOREIGN KEY (last_modified_by)
        REFERENCES users(id)
        ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS locks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT UNIQUE NOT NULL,
    locked_by INTEGER,
    locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (locked_by)
        REFERENCES users(id)
        ON DELETE SET NULL
        );

CREATE TABLE IF NOT EXISTS time_off (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    technician_id INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    reason TEXT,
    FOREIGN KEY (technician_id)
        REFERENCES technicians(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jobs_start
    ON jobs(start_date);

CREATE INDEX IF NOT EXISTS idx_jobs_end
    ON jobs(end_date);

CREATE INDEX IF NOT EXISTS idx_timeoff_start
    ON time_off(start_date);

CREATE INDEX IF NOT EXISTS idx_timeoff_end
    ON time_off(end_date);

CREATE INDEX IF NOT EXISTS idx_locks_date
    ON locks(date);


