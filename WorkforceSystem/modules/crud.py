from __future__ import annotations

from typing import Any, Dict, List, Optional

from modules.db import Database


def _existing_tables(db: Database) -> List[str]:
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(
            "SELECT TABLE_NAME FROM information_schema.tables WHERE TABLE_SCHEMA = %s",
            (db.config.database,),
        )
        return [row["TABLE_NAME"] for row in cur.fetchall()]


def add_employee(
    db: Database,
    emp_id: str,
    department: Optional[str],
    position: Optional[str],
    base_salary: Optional[float],
    start_date: Optional[str],
    dept_id: Optional[str],
) -> None:
    """Create a new employee row in the employees table."""
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(
            """
INSERT INTO employees (emp_id, department, position, base_salary, start_date, dept_id)
VALUES (%s, %s, %s, %s, %s, %s)
""",
            (emp_id, department, position, base_salary, start_date, dept_id),
        )
        conn.commit()


def get_all_employees(db: Database) -> List[Dict[str, Any]]:
    """Return employees as a list of dictionaries."""
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT emp_id, department, position, base_salary, start_date, dept_id FROM employees")
        return list(cur.fetchall())


def update_employee(
    db: Database,
    emp_id: str,
    *,
    department: Optional[str] = None,
    position: Optional[str] = None,
    base_salary: Optional[float] = None,
    start_date: Optional[str] = None,
    dept_id: Optional[str] = None,
) -> bool:
    """Update an employee row."""
    assignments = []
    params: List[Any] = []

    if department is not None:
        assignments.append("department = %s")
        params.append(department)
    if position is not None:
        assignments.append("position = %s")
        params.append(position)
    if base_salary is not None:
        assignments.append("base_salary = %s")
        params.append(base_salary)
    if start_date is not None:
        assignments.append("start_date = %s")
        params.append(start_date)
    if dept_id is not None:
        assignments.append("dept_id = %s")
        params.append(dept_id)

    if not assignments:
        return False

    params.append(emp_id)
    query = f"UPDATE employees SET {', '.join(assignments)} WHERE emp_id = %s"

    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, params)
        conn.commit()
        return cur.rowcount > 0


def delete_employee(db: Database, emp_id: str) -> bool:
    """Delete an employee by id. Returns True when a row was removed."""
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("DELETE FROM employees WHERE emp_id = %s", (emp_id,))
        conn.commit()
        return cur.rowcount > 0


def add_department(db: Database, dept_id: str, dept_name: Optional[str], category: Optional[str]) -> None:
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(
            "INSERT INTO department (dept_id, dept_name, category) VALUES (%s, %s, %s)",
            (dept_id, dept_name, category),
        )
        conn.commit()


def department_exists(db: Database, dept_id: str) -> bool:
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT 1 FROM department WHERE dept_id = %s LIMIT 1", (dept_id,))
        return cur.fetchone() is not None


def list_departments(db: Database) -> List[Dict[str, Any]]:
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT dept_id, dept_name, category FROM department")
        return list(cur.fetchall())


def update_department(
    db: Database,
    dept_id: str,
    *,
    dept_name: Optional[str] = None,
    category: Optional[str] = None,
) -> bool:
    assignments = []
    params: List[Any] = []
    if dept_name is not None:
        assignments.append("dept_name = %s")
        params.append(dept_name)
    if category is not None:
        assignments.append("category = %s")
        params.append(category)
    if not assignments:
        return False
    params.append(dept_id)
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(f"UPDATE department SET {', '.join(assignments)} WHERE dept_id = %s", params)
        conn.commit()
        return cur.rowcount > 0


def delete_department(db: Database, dept_id: str) -> bool:
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("DELETE FROM department WHERE dept_id = %s", (dept_id,))
        conn.commit()
        return cur.rowcount > 0


def add_shift(
    db: Database,
    shift_code: str,
    shift_name: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
    standard_hours: Optional[float],
) -> None:
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(
            """
INSERT INTO shift (shift_code, shift_name, start_time, end_time, standard_hours)
VALUES (%s, %s, %s, %s, %s)
""",
            (shift_code, shift_name, start_time, end_time, standard_hours),
        )
        conn.commit()


def list_shifts(db: Database) -> List[Dict[str, Any]]:
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT shift_code, shift_name, start_time, end_time, standard_hours FROM shift")
        return list(cur.fetchall())


def update_shift(
    db: Database,
    shift_code: str,
    *,
    shift_name: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    standard_hours: Optional[float] = None,
) -> bool:
    assignments = []
    params: List[Any] = []
    if shift_name is not None:
        assignments.append("shift_name = %s")
        params.append(shift_name)
    if start_time is not None:
        assignments.append("start_time = %s")
        params.append(start_time)
    if end_time is not None:
        assignments.append("end_time = %s")
        params.append(end_time)
    if standard_hours is not None:
        assignments.append("standard_hours = %s")
        params.append(standard_hours)
    if not assignments:
        return False
    params.append(shift_code)
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(f"UPDATE shift SET {', '.join(assignments)} WHERE shift_code = %s", params)
        conn.commit()
        return cur.rowcount > 0


def delete_shift(db: Database, shift_code: str) -> bool:
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("DELETE FROM shift WHERE shift_code = %s", (shift_code,))
        conn.commit()
        return cur.rowcount > 0


def add_time_record(
    db: Database,
    emp_id: str,
    work_date: str,
    shift_code: Optional[str],
    clock_in: Optional[str],
    clock_out: Optional[str],
    job_type: Optional[str] = None,
    department: Optional[str] = None,
    bf_ot: Optional[str] = None,
    af_ot: Optional[str] = None,
    bt_ot: Optional[str] = None,
) -> None:
    """Insert a time record row."""
    in_time = clock_in
    out_time = clock_out
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(
            """
INSERT INTO time_records (emp_id, work_date, shift_code, `in`, `out`, clock_in, clock_out, job_type, department, bf_ot, af_ot, bt_ot)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
""",
            (
                emp_id,
                work_date,
                shift_code,
                in_time,
                out_time,
                clock_in,
                clock_out,
                job_type,
                department,
                bf_ot,
                af_ot,
                bt_ot,
            ),
        )
        conn.commit()


def delete_time_record(db: Database, emp_id: str, work_date: str) -> bool:
    """Delete a time record by emp_id and work_date."""
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute("DELETE FROM time_records WHERE emp_id = %s AND work_date = %s", (emp_id, work_date))
        conn.commit()
        return cur.rowcount > 0


def fetch_time_records(db: Database, emp_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """Fetch time records, optionally filtered by employee id."""
    base = "SELECT * FROM time_records"
    params: list = []
    if emp_id is not None:
        base += " WHERE emp_id = %s"
        params.append(emp_id)
    base += " ORDER BY work_date DESC, clock_in DESC LIMIT %s"
    params.append(max(1, min(limit, 500)))
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(base, params)
        return list(cur.fetchall())


def fetch_time_entries(db: Database, employee_id: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Backward-compatible alias to fetch_time_records.
    """
    return fetch_time_records(db, emp_id=employee_id, limit=limit)


def summarize_ot(
    db: Database,
    period: str = "month",
    limit: int = 12,
    year: Optional[int] = None,
    month: Optional[int] = None,
    department: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Summarize overtime from time_records by period (week, month, or year).
    Returns list of dicts with bucket, ot_seconds, and rows_cnt.
    """
    period = (period or "month").lower()
    if period == "week":
        bucket_expr = "YEARWEEK(work_date, 1)"
    elif period == "year":
        bucket_expr = "YEAR(work_date)"
    elif period == "month":
        bucket_expr = "DATE_FORMAT(work_date, '%Y-%m')"
    else:
        raise ValueError("period must be one of: week, month, year")

    safe_limit = max(1, min(limit, 100))
    # Support both HH:MM:SS strings and decimal hour strings (e.g., "2.50") in OT columns.
    def _ot_expr(col: str) -> str:
        return f"""
            COALESCE(
                CASE
                    WHEN {col} IS NULL OR {col} = '' THEN 0
                    WHEN {col} LIKE '%:%' THEN TIME_TO_SEC({col}) / 3600
                    ELSE CAST({col} AS DECIMAL(10,2))
                END,
                0
            )
        """

    bf_expr = _ot_expr("bf_ot")
    af_expr = _ot_expr("af_ot")
    bt_expr = _ot_expr("bt_ot")

    filters = []
    params: List[Any] = []
    if year is not None:
        filters.append("YEAR(work_date) = %s")
        params.append(int(year))
    if month is not None:
        filters.append("MONTH(work_date) = %s")
        params.append(int(month))
    if department:
        filters.append("department = %s")
        params.append(department)
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(safe_limit)

    query = f"""
        SELECT {bucket_expr} AS bucket,
               SUM(({bf_expr}) + ({af_expr}) + ({bt_expr})) AS ot_hours,
               COUNT(*) AS rows_cnt
        FROM time_records
        {where_clause}
        GROUP BY bucket
        ORDER BY bucket DESC
        LIMIT %s
    """
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, tuple(params))
        return list(cur.fetchall())


def summarize_ot_by_department(
    db: Database,
    limit: int = 20,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Summarize OT hours grouped by department from time_records.
    """
    safe_limit = max(1, min(limit, 200))

    def _ot_expr(col: str) -> str:
        return f"""
            COALESCE(
                CASE
                    WHEN {col} IS NULL OR {col} = '' THEN 0
                    WHEN {col} LIKE '%:%' THEN TIME_TO_SEC({col}) / 3600
                    ELSE CAST({col} AS DECIMAL(10,2))
                END,
                0
            )
        """

    bf_expr = _ot_expr("bf_ot")
    af_expr = _ot_expr("af_ot")
    bt_expr = _ot_expr("bt_ot")

    filters = []
    params: List[Any] = []
    if year is not None:
        filters.append("YEAR(work_date) = %s")
        params.append(int(year))
    if month is not None:
        filters.append("MONTH(work_date) = %s")
        params.append(int(month))
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(safe_limit)

    query = f"""
        SELECT COALESCE(department, 'Unknown') AS department,
               SUM(({bf_expr}) + ({af_expr}) + ({bt_expr})) AS ot_hours
        FROM time_records
        {where_clause}
        GROUP BY department
        ORDER BY ot_hours DESC
        LIMIT %s
    """
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, tuple(params))
        return list(cur.fetchall())


def summarize_ot_department_view(
    db: Database,
    view_name: str = "v_weekly_ot_department",
    limit: int = 50,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Summarize OT hours by department from a view (default v_weekly_ot_department).
    Filters by YEAR/MONTH on week_start when provided.
    """
    available = set(list_database_views(db))
    if view_name not in available:
        raise ValueError(f"View '{view_name}' not found in database.")

    safe_limit = max(1, min(limit, 200))
    filters = []
    params: List[Any] = []
    if year is not None:
        filters.append("YEAR(week_start) = %s")
        params.append(int(year))
    if month is not None:
        filters.append("MONTH(week_start) = %s")
        params.append(int(month))
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(safe_limit)

    query = f"""
        SELECT department_name AS department,
               SUM(total_ot_hours) AS ot_hours
        FROM `{view_name}`
        {where_clause}
        GROUP BY department_name
        ORDER BY ot_hours DESC
        LIMIT %s
    """
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, tuple(params))
        return list(cur.fetchall())


def summarize_payroll(
    db: Database,
    view_name: str = "v_daily_payroll",
    period: str = "month",
    limit: int = 12,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Summarize total pay from a payroll view (default v_daily_payroll) by week/month/year.
    The view must have work_date and total_pay columns.
    """
    available = set(list_database_views(db))
    tables = set(list_database_tables(db))
    if view_name not in available and view_name not in tables:
        raise ValueError(f"View/Table '{view_name}' not found in database.")

    period = (period or "month").lower()
    if period == "week":
        bucket_expr = "YEARWEEK(work_date, 1)"
    elif period == "year":
        bucket_expr = "YEAR(work_date)"
    else:
        bucket_expr = "DATE_FORMAT(work_date, '%Y-%m')"

    safe_limit = max(1, min(limit, 100))
    filters = []
    params: List[Any] = []
    if year is not None:
        filters.append("YEAR(work_date) = %s")
        params.append(int(year))
    if month is not None:
        filters.append("MONTH(work_date) = %s")
        params.append(int(month))
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(safe_limit)

    query = f"""
        SELECT {bucket_expr} AS bucket,
               SUM(total_pay) AS total_pay,
               COUNT(*) AS rows_cnt
        FROM `{view_name}`
        {where_clause}
        GROUP BY bucket
        ORDER BY bucket DESC
        LIMIT %s
    """
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, tuple(params))
        return list(cur.fetchall())


def count_employees_by_time_records(
    db: Database,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> int:
    """
    Count distinct employees appearing in time_records filtered by work_date year/month.
    """
    filters = []
    params: List[Any] = []
    if year is not None:
        filters.append("YEAR(work_date) = %s")
        params.append(int(year))
    if month is not None:
        filters.append("MONTH(work_date) = %s")
        params.append(int(month))
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    query = f"SELECT COUNT(DISTINCT emp_id) AS cnt FROM time_records {where_clause}"
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, tuple(params))
        row = cur.fetchone() or {}
        return int(row.get("cnt") or 0)


def summarize_revenue_by_department(
    db: Database,
    view_name: str = "v_daily_payroll",
    limit: int = 50,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    Summarize revenue (total_pay) by department from a payroll view.
    """
    available = set(list_database_views(db))
    tables = set(list_database_tables(db))
    if view_name not in available and view_name not in tables:
        raise ValueError(f"View/Table '{view_name}' not found in database.")

    safe_limit = max(1, min(limit, 200))
    filters = []
    params: List[Any] = []
    if year is not None:
        filters.append("YEAR(work_date) = %s")
        params.append(int(year))
    if month is not None:
        filters.append("MONTH(work_date) = %s")
        params.append(int(month))
    where_clause = f"WHERE {' AND '.join(filters)}" if filters else ""
    params.append(safe_limit)

    query = f"""
        SELECT COALESCE(department, 'Unknown') AS department,
               SUM(total_pay) AS total_pay
        FROM `{view_name}`
        {where_clause}
        GROUP BY department
        ORDER BY total_pay DESC
        LIMIT %s
    """
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, tuple(params))
        return list(cur.fetchall())


def count_burnout_view(
    db: Database,
    view_name: str,
    *,
    column: str = "total_ot_hours",
    threshold_hours: float = 60.0,
    date_column: str = "week_start",
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> int:
    """
    Count rows in a view where a numeric column exceeds threshold_hours,
    with optional year/month filters on a date column (defaults to week_start).
    """
    available = set(list_database_views(db))
    if view_name not in available:
        raise ValueError(f"View '{view_name}' not found in database.")

    filters = [f"`{column}` > %s"]
    params: List[Any] = [threshold_hours]
    if year is not None:
        filters.append(f"YEAR(`{date_column}`) = %s")
        params.append(int(year))
    if month is not None:
        filters.append(f"MONTH(`{date_column}`) = %s")
        params.append(int(month))
    where_clause = " AND ".join(filters)

    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(f"SELECT COUNT(*) AS cnt FROM `{view_name}` WHERE {where_clause}", tuple(params))
        row = cur.fetchone() or {}
        return int(row.get("cnt") or 0)


def list_database_views(db: Database) -> List[str]:
    """Return view names in the current database."""
    schema = db.config.database
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(
            "SELECT TABLE_NAME FROM information_schema.views WHERE TABLE_SCHEMA = %s ORDER BY TABLE_NAME",
            (schema,),
        )
        return [row["TABLE_NAME"] for row in cur.fetchall()]


def fetch_view_rows(db: Database, view_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch rows from a view, capped by limit.
    The view name is validated against the database metadata to avoid injection.
    """
    available = set(list_database_views(db))
    if view_name not in available:
        raise ValueError(f"View '{view_name}' not found in database.")

    safe_limit = max(1, min(limit, 500))
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(f"SELECT * FROM `{view_name}` LIMIT %s", (safe_limit,))
        return list(cur.fetchall())


def list_database_tables(db: Database) -> List[str]:
    """Return table names in the current database."""
    return _existing_tables(db)


def fetch_table_rows(db: Database, table_name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Fetch rows from a table, capped by limit.
    Table name is validated against metadata to avoid injection.
    """
    available = set(list_database_tables(db))
    if table_name not in available:
        raise ValueError(f"Table '{table_name}' not found in database.")

    safe_limit = max(1, min(limit, 500))
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(f"SELECT * FROM `{table_name}` LIMIT %s", (safe_limit,))
        return list(cur.fetchall())


def upsert_payroll(
    db: Database,
    emp_id: str,
    month: str,
    total_work_hours: Optional[float],
    total_ot_hours: Optional[float],
    ot_rate: Optional[float],
    total_salary: Optional[float],
) -> None:
    """Insert or update payroll row."""
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(
            """
INSERT INTO payroll (emp_id, month, total_work_hours, total_ot_hours, ot_rate, total_salary)
VALUES (%s, %s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE
 total_work_hours = VALUES(total_work_hours),
 total_ot_hours = VALUES(total_ot_hours),
 ot_rate = VALUES(ot_rate),
 total_salary = VALUES(total_salary)
""",
            (emp_id, month, total_work_hours, total_ot_hours, ot_rate, total_salary),
        )
        conn.commit()


def list_payroll(db: Database, month: Optional[str] = None) -> List[Dict[str, Any]]:
    """List payroll rows, optionally filtered by month."""
    query = "SELECT emp_id, month, total_work_hours, total_ot_hours, ot_rate, total_salary FROM payroll"
    params: List[Any] = []
    if month:
        query += " WHERE month = %s"
        params.append(month)
    with db.connect() as conn, conn.cursor(dictionary=True) as cur:
        cur.execute(query, params)
        return list(cur.fetchall())


__all__ = [
    "get_all_employees",
    "add_employee",
    "update_employee",
    "delete_employee",
    "add_department",
    "list_departments",
    "update_department",
    "delete_department",
    "department_exists",
    "add_shift",
    "list_shifts",
    "update_shift",
    "delete_shift",
    "add_time_record",
    "delete_time_record",
    "fetch_time_records",
    "fetch_time_entries",
    "summarize_ot",
    "summarize_ot_by_department",
    "summarize_ot_department_view",
    "summarize_payroll",
    "summarize_revenue_by_department",
    "count_burnout_view",
    "list_database_views",
    "fetch_view_rows",
    "list_database_tables",
    "fetch_table_rows",
    "upsert_payroll",
    "list_payroll",
]
