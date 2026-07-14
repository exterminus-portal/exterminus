-- Snapshot of the live ExTerminus schema as of 2026.07.13
-- Used to create disposable development and characterization-test databases.
-- This records the current schema; it is not the intended final schema.

CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        first_name TEXT,
        last_name TEXT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'tech',
        must_reset_password INTEGER NOT NULL DEFAULT 0,
        last_password_change TEXT
    );
CREATE TABLE jobs (
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
        custom_pest TEXT,
        exclusion_subtype TEXT,
        notes TEXT,
        rei_zip TEXT,
        rei_quantity INTEGER,
        rei_city_name TEXT,
        technician_id INTEGER,
        two_man INTEGER NOT NULL DEFAULT 0,
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        last_modified TEXT,
        last_modified_by INTEGER, updated_at TEXT, updated_by INTEGER, assignment_mode TEXT DEFAULT 'single', is_multiday INTEGER DEFAULT 0, date TEXT,
        FOREIGN KEY (technician_id) REFERENCES technicians(id) ON DELETE SET NULL,
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY (last_modified_by) REFERENCES users(id) ON DELETE SET NULL
    );
CREATE TABLE locks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT UNIQUE NOT NULL,
        locked_by INTEGER,
        locked_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (locked_by) REFERENCES users(id) ON DELETE SET NULL
    );
CREATE TABLE time_off (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        technician_id INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        reason TEXT,
        FOREIGN KEY (technician_id) REFERENCES technicians(id) ON DELETE CASCADE
    );
CREATE INDEX idx_jobs_start ON jobs(start_date);
CREATE INDEX idx_jobs_end ON jobs(end_date);
CREATE INDEX idx_timeoff_start ON time_off(start_date);
CREATE INDEX idx_timeoff_end ON time_off(end_date);
CREATE INDEX idx_locks_date ON locks(date);
CREATE INDEX idx_jobs_created_by ON jobs(created_by);
CREATE TRIGGER trg_jobs_created_by_not_null_ins
BEFORE INSERT ON jobs
WHEN NEW.created_by IS NULL
BEGIN
	SELECT RAISE(ABORT, 'jobs.created_by required');
END;
CREATE INDEX idx_jobs_date ON jobs(date);
CREATE INDEX idx_jobs_range ON jobs(start_date, end_date);
CREATE TABLE day_locks(date TEXT PRIMARY KEY);
CREATE TABLE audit_log(
                id INTEGER PRIMARY KEY,
                actor_id INTEGER,
                action TEXT NOT NULL,
                subject_type TEXT,
                subject_id INTEGER,
                metadata TEXT,
                ts INTEGER NOT NULL
            );
CREATE TABLE IF NOT EXISTS "schema_migrations"(
  id TEXT PRIMARY KEY,
  applied_at INTEGER NOT NULL,
  meta TEXT
);
