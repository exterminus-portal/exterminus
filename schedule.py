"""Read-only schedule queries shared by HTML and API routes."""

import sqlite3
from datetime import date


def read_day_schedule(
    connection: sqlite3.Connection,
    selected_date: date,
) -> dict:
    selected_date_text = selected_date.isoformat()

    locked = (
        connection.execute(
            "SELECT 1 FROM locks WHERE date = ?",
            (selected_date_text,),
        ).fetchone()
        is not None
    )

    jobs = connection.execute(
        """
        SELECT
            j.*,
            j.job_type AS type,
            t.name AS technician_name,
            cu.username AS created_by_name,
            mu.username AS modified_by_name,

            CASE
                WHEN LOWER(COALESCE(j.job_type, '')) = 'rei'
                    THEN 'REIs'
                ELSE COALESCE(NULLIF(j.title, ''), '(Untitled)')
             END AS display_title,
            CASE
                WHEN j.is_multiday == 1
                    AND date(j.start_date) = date(?1)
                    THEN 1
                ELSE 0
            END AS is_first,

            CASE
                WHEN j.is_multiday = 1
                    AND date(
                        COALESCE(j.end_date, j.start_date)
                        ) = date(?1)
                    THEN 1
                    ELSE 0
            END AS is_last,

            CASE
                WHEN j.is_multiday = 1
                    AND date(?1) > date(j.start_date)
                    AND date(?1) < date(
                        COALESCE(j.end_date, j.start_date)
                    )
                    THEN 1
                ELSE 0
            END AS is_mid,

            CASE
                WHEN j.is_multiday = 0 THEN 1
                WHEN date(j.start_date) = date(?1) THEN 1
                ELSE 0
            END AS show_price

            FROM jobs AS j
            LEFT JOIN technicians AS t
                ON t.id = j.technician_id
            LEFT JOIN users AS cu
                ON cu.id = j.created_by
            LEFT JOIN users AS mu
                ON mu.id = j.last_modified_by

            WHERE
                (
                    j.is_multiday = 0
                    AND date(j.start_date) = date(?1)
                )
                OR
                (
                    j.is_multiday = 1
                    AND date(j.start_date) <= date(?1)
                    AND date(
                    COALESCE(j.end_date, j.start_date)
                    ) >= date(?1)
                )

            ORDER BY date(j.start_date), j.id
            """,
        (selected_date_text,),
    ).fetchall()

    time_off = connection.execute(
        """
            SELECT
                toff.*,
                toff.technician_id AS owner_id,
                tech.name AS tech_name

            FROM time_off AS toff
            LEFT JOIN technicians AS tech
                ON tech.id = toff.technician_id

            WHERE date(?1) BETWEEN
                date(toff.start_date)
                AND date(
                    COALESCE(toff.end_date, toff.start_date)
                )

            ORDER BY tech.name, toff.id
            """,
        (selected_date_text,),
    ).fetchall()

    return {
        "date": selected_date_text,
        "locked": locked,
        "jobs": [dict(job) for job in jobs],
        "time_off": [dict(entry) for entry in time_off],
    }
