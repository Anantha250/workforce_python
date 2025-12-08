from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any, Dict, Iterable, Optional

from modules.crud import fetch_time_records
from modules.db import Database

def active_headcount(employees: Iterable[Dict[str, Any]]) -> int:
    """Count active employees in the provided iterable."""
    return sum(1 for employee in employees if employee.get("active"))

def hours_by_employee(time_entries: Iterable[Dict[str, Any]]) -> Dict[int, float]:
    """Aggregate total hours worked keyed by employee id."""
    totals: Dict[int, float] = {}
    for entry in time_entries:
        employee_id = int(entry.get("employee_id") or entry.get("emp_id"))
        hours = float(entry.get("hours_worked", entry.get("hours", 0.0)))
        totals[employee_id] = totals.get(employee_id, 0.0) + hours
    return totals

def payroll_projection(employees: Iterable[Dict[str, Any]], hours_summary: Dict[int, float]) -> Dict[int, float]:
    """
    Calculate projected payroll by multiplying total hours with hourly rates.
    Returns a mapping of employee id to projected payout.
    """
    projection: Dict[int, float] = {}
    for employee in employees:
        employee_id = int(employee["id"])
        rate = float(employee.get("hourly_rate", 0.0))
        hours = hours_summary.get(employee_id, 0.0)
        projection[employee_id] = hours * rate
    return projection


def _normalize_date(raw: Any) -> Optional[date]:
    """Convert stored shift date to a date object when possible."""
    if raw is None:
        return None
    if isinstance(raw, date):
        return raw
    try:
        return datetime.fromisoformat(str(raw)).date()
    except ValueError:
        return None


def calculate_weekly_hours(db: Database, employee_id: int, *, reference: Optional[date] = None) -> float:
    """
    Sum total hours for the last 7 days (inclusive) ending at `reference` date.
    Defaults to today's date when reference is not provided.
    """
    ref_date = reference or date.today()
    window_start = ref_date - timedelta(days=6)
    entries = fetch_time_records(db, emp_id=str(employee_id))

    total = 0.0
    for entry in entries:
        shift_date = _normalize_date(entry.get("shift_date") or entry.get("work_date") or entry.get("date"))
        if shift_date is None:
            continue
        if window_start <= shift_date <= ref_date:
            total += float(entry.get("hours_worked", entry.get("hours", 0.0)))
    return total


def calculate_ot_rate(db: Database, employee_id: int, *, weekly_threshold: float = 40.0) -> float:
    """
    Calculate overtime rate as the fraction of weekly hours above the threshold.
    Returns 0 when the employee has no recorded hours.
    """
    weekly_hours = calculate_weekly_hours(db, employee_id)
    if weekly_hours <= 0:
        return 0.0
    ot_hours = max(weekly_hours - weekly_threshold, 0.0)
    return ot_hours / weekly_hours


def get_burnout_score(db: Database, employee_id: int) -> float:
    """
    Heuristic burnout score (0-100) combining weekly hours and overtime rate.
    Higher weekly hours and higher OT rates increase the score.
    """
    weekly_hours = calculate_weekly_hours(db, employee_id)
    ot_rate = calculate_ot_rate(db, employee_id)

    # Weighted blend: base load plus overtime pressure, capped at 100.
    score = (weekly_hours * 1.25) + (ot_rate * 50.0)
    return max(0.0, min(100.0, score))


__all__ = [
    "active_headcount",
    "hours_by_employee",
    "payroll_projection",
    "calculate_weekly_hours",
    "calculate_ot_rate",
    "get_burnout_score",
]
