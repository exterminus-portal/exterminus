"""Read-only API routes consumed by Pest Terminal."""

from datetime import date
from re import PatternError
from flask import Blueprint, jsonify
from db import get_database
from schedule import read_day_schedule

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.get("/health")
def health():
    return jsonify(
        {
            "service": "exterminus",
            "status": "ok",
        }
    )


@api_bp.get("/schedule/day/<selected_date>")
def day_schedule(selected_date: str):
    try:
        parsed_date = date.fromisoformat(selected_date)
    except ValueError:
        return (
            jsonify(
                {
                    "error": "selected_date must use YYYY-MM-DD format",
                }
            ),
            400,
        )

    if parsed_date.isoformat() != selected_date:
        return (
            jsonify(
                {
                    "error": "selected_date must use YYYY-MM-DD format",
                }
            ),
            400,
        )

    connection = get_database()

    try:
        schedule = read_day_schedule(
            connection,
            parsed_date,
        )
    finally:
        connection.close()

    return jsonify(schedule)
