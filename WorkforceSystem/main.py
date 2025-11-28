from __future__ import annotations

import os
import argparse
from typing import Any, Dict, Optional

from config.db_config import DatabaseConfig
from modules.analytics import active_headcount
from modules.crud import (
    add_employee,
    add_time_record,
    count_burnout_view,
    count_employees_by_time_records,
    delete_time_record,
    delete_employee,
    list_departments,
    fetch_time_records,
    get_all_employees,
    list_database_views,
    fetch_view_rows,
    list_database_tables,
    fetch_table_rows,
    update_employee,
    department_exists,
    summarize_payroll,
    summarize_ot,
    summarize_ot_by_department,
    summarize_ot_department_view,
    summarize_revenue_by_department,
)
from modules.db import Database
from modules.textlog import get_logger

logger = get_logger()

# Simple admin credentials from environment (fallback to defaults).
ADMIN_USERNAME = os.getenv("WORKFORCE_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("WORKFORCE_ADMIN_PASS", "admin")
current_user: Optional[str] = None


def connect_db() -> Database:
    config = DatabaseConfig.from_env()
    logger.info("Connecting to MySQL %s@%s:%s/%s", config.user, config.host, config.port, config.database)
    return Database(config)


def init_db(db: Database) -> None:
    db.initialize()
    logger.info("Database schema ensured")
    print("Database initialized.")


def prompt_float(prompt: str, default: float) -> float:
    raw = input(prompt).strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        print("Invalid number, using default.")
        return default


def require_auth(action: str) -> bool:
    if current_user is None:
        print("Please login as admin first.")
        return False
    return True


def login_flow() -> None:
    global current_user
    if current_user:
        print(f"Already logged in as {current_user}")
        return
    username = input("Admin username: ").strip()
    password = input("Admin password: ").strip()
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        current_user = username
        logger.info("Admin logged in: %s", username)
        print("Login successful.")
    else:
        logger.warning("Failed admin login for user=%s", username)
        print("Invalid credentials.")


def logout_flow() -> None:
    global current_user
    if not current_user:
        print("Not logged in.")
        return
    logger.info("Admin logged out: %s", current_user)
    current_user = None
    print("Logged out.")


def prompt_str(label: str, required: bool = False) -> Optional[str]:
    val = input(label).strip()
    if required and not val:
        print("This field is required.")
        return None
    return val or None


def add_employee_flow(db: Database) -> None:
    if not require_auth("add employee"):
        return
    emp_id = prompt_str("Employee ID: ", required=True)
    department = prompt_str("Department: ")
    position = prompt_str("Position: ")
    base_salary = prompt_float("Base salary (decimal, default 0): ", 0.0)
    start_date = prompt_str("Start date (YYYY-MM-DD): ")
    dept_id = prompt_str("Dept ID: ")

    if not emp_id:
        return

    if dept_id and not department_exists(db, dept_id):
        print(f"Dept ID '{dept_id}' does not exist. Please create it first or leave blank.")
        return

    add_employee(
        db,
        emp_id=emp_id,
        department=department,
        position=position,
        base_salary=base_salary,
        start_date=start_date,
        dept_id=dept_id,
    )
    logger.info("Employee created emp_id=%s dept=%s position=%s", emp_id, department, position)
    print(f"Created employee {emp_id}")


def update_employee_flow(db: Database) -> None:
    if not require_auth("update employee"):
        return
    emp_id = prompt_str("Employee ID to update: ", required=True)
    if not emp_id:
        return

    department = prompt_str("New department (blank keep): ")
    position = prompt_str("New position (blank keep): ")
    salary_raw = prompt_str("New base salary (blank keep): ")
    base_salary = float(salary_raw) if salary_raw else None
    start_date = prompt_str("New start date YYYY-MM-DD (blank keep): ")
    dept_id = prompt_str("New dept_id (blank keep): ")

    updated = update_employee(
        db,
        emp_id,
        department=department,
        position=position,
        base_salary=base_salary,
        start_date=start_date,
        dept_id=dept_id,
    )
    if updated:
        logger.info("Employee updated emp_id=%s", emp_id)
        print("Employee updated.")
    else:
        print("No updates applied (check ID or fields).")


def delete_employee_flow(db: Database) -> None:
    if not require_auth("delete employee"):
        return
    emp_id = prompt_str("Employee ID to delete: ", required=True)
    if not emp_id:
        return

    confirm = input(f"Are you sure you want to delete employee {emp_id}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return

    removed = delete_employee(db, emp_id)
    if removed:
        logger.info("Employee deleted emp_id=%s", emp_id)
        print("Employee deleted.")
    else:
        print("Employee not found.")


def list_employees_flow(db: Database) -> None:
    if not require_auth("list employees"):
        return
    employees = get_all_employees(db)
    if not employees:
        print("No employees found.")
        return
    print("\nEmployees:")
    for emp in employees:
        print(
            f"  {emp['emp_id']} | dept: {emp.get('department')} | position: {emp.get('position')} | "
            f"base_salary: {emp.get('base_salary')} | start: {emp.get('start_date')} | dept_id: {emp.get('dept_id')}"
        )
    print("")


def log_time_record_flow(db: Database) -> None:
    if not require_auth("log time"):
        return
    emp_id = prompt_str("Employee ID: ", required=True)
    work_date = prompt_str("Work date (YYYY-MM-DD): ", required=True)
    shift_code = prompt_str("Shift code: ")
    clock_in = prompt_str("Clock in (HH:MM:SS): ")
    clock_out = prompt_str("Clock out (HH:MM:SS): ")
    job_type = prompt_str("Job type: ")
    department = prompt_str("Department: ")
    bf_ot = prompt_str("Before OT (Y/N/blank): ")
    af_ot = prompt_str("After OT (Y/N/blank): ")
    bt_ot = prompt_str("Between OT (Y/N/blank): ")

    if not emp_id or not work_date:
        return

    add_time_record(
        db,
        emp_id=emp_id,
        work_date=work_date,
        shift_code=shift_code,
        clock_in=clock_in,
        clock_out=clock_out,
        job_type=job_type,
        department=department,
        bf_ot=bf_ot,
        af_ot=af_ot,
        bt_ot=bt_ot,
    )
    logger.info("Time record added emp_id=%s date=%s shift=%s", emp_id, work_date, shift_code)
    print("Time record added.")


def analytics_flow(db: Database) -> None:
    if not require_auth("run analytics"):
        return
    employees = get_all_employees(db)
    print("Active headcount:", active_headcount(employees))
    records = fetch_time_records(db, limit=10)
    print("\nRecent time records (10 rows):")
    for rec in records:
        print(rec)
    logger.info("Analytics summary headcount=%s records_shown=%s", len(employees), len(records))

    def preview_view(label: str, view_name: str, limit: int) -> None:
        print(f"\n{label} (view: {view_name}, top {limit})")
        try:
            rows = fetch_view_rows(db, view_name, limit=limit)
        except ValueError as err:
            print(err)
            return
        if not rows:
            print("No rows returned.")
            return
        for row in rows:
            print(row)

    try:
        n_raw = input("\nTop N for rankings (default 5): ").strip()
        top_n = int(n_raw) if n_raw else 5
    except ValueError:
        print("Invalid number, using 5.")
        top_n = 5

    preview_view("Burnout ranking", "v_burnout_ranking", limit=top_n)
    preview_view("OT ranking by department", "v_department_ot_ranking", limit=top_n)
    preview_view("Daily payroll summary", "v_daily_payroll", limit=20)


def views_flow(db: Database) -> None:
    if not require_auth("view database views"):
        return
    views = list_database_views(db)
    if not views:
        print("No views found in this database.")
        return

    print("\nAvailable views:")
    for idx, view in enumerate(views, start=1):
        print(f"  {idx}) {view}")

    choice = input("Enter view name to preview (blank to cancel): ").strip()
    if not choice:
        print("Cancelled.")
        return

    try:
        limit_raw = input("Rows to fetch (default 20, max 500): ").strip()
        limit = int(limit_raw) if limit_raw else 20
    except ValueError:
        print("Invalid limit, using 20.")
        limit = 20

    try:
        rows = fetch_view_rows(db, choice, limit=limit)
    except ValueError as err:
        print(err)
        return

    if not rows:
        print("No rows returned.")
        return

    print(f"\nPreview of {choice} (up to {limit} rows):")
    for row in rows:
        print(row)

    logger.info("Previewed view=%s rows=%s", choice, len(rows))


def featured_views_flow(db: Database) -> None:
    if not require_auth("view featured views"):
        return
    """Quick access to key views: burnout ranking, daily payroll, weekly hours summary."""
    featured = [
        "v_burnout_ranking",
        "v_daily_payroll",
        "v_weekly_hours_summary",
    ]
    for view in featured:
        print(f"\n=== {view} ===")
        try:
            rows = fetch_view_rows(db, view, limit=20)
        except ValueError as err:
            print(err)
            continue
        if not rows:
            print("No rows returned.")
            continue
        for row in rows:
            print(row)
        logger.info("Previewed featured view=%s rows=%s", view, len(rows))


def tables_flow(db: Database) -> None:
    if not require_auth("view database tables"):
        return
    tables = list_database_tables(db)
    if not tables:
        print("No tables found in this database.")
        return

    print("\nAvailable tables:")
    for idx, table in enumerate(tables, start=1):
        print(f"  {idx}) {table}")

    choice = input("Enter table name to preview (blank to cancel): ").strip()
    if not choice:
        print("Cancelled.")
        return

    try:
        limit_raw = input("Rows to fetch (default 20, max 500): ").strip()
        limit = int(limit_raw) if limit_raw else 20
    except ValueError:
        print("Invalid limit, using 20.")
        limit = 20

    try:
        rows = fetch_table_rows(db, choice, limit=limit)
    except ValueError as err:
        print(err)
        return

    if not rows:
        print("No rows returned.")
        return

    print(f"\nPreview of {choice} (up to {limit} rows):")
    for row in rows:
        print(row)

    logger.info("Previewed table=%s rows=%s", choice, len(rows))


def print_menu() -> None:
    print(
        """
Workforce CLI Menu
1) Admin login
2) Admin logout
3) Initialize database
4) Add employee (login required)
5) Update employee (login required)
6) Delete employee (login required)
7) List employees (login required)
8) Log time attendance (login required)
9) Run analytics (login required)
10) Show database views (login required)
11) Show database tables (login required)
12) Show featured views (login required)
0) Exit
"""
    )


def run_gui(db: Database) -> None:
    """Launch the GUI dashboard (imports GUI deps lazily to keep CLI lightweight)."""
    import tkinter as tk
    from tkinter import messagebox

    import customtkinter as ctk
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    gui_logger = get_logger("workforce.gui")

    def _style_treeview(tv: tk.Widget) -> None:
        style = tk.ttk.Style()
        style.configure(
            "Dark.Treeview",
            background="#121212",
            foreground="white",
            fieldbackground="#121212",
            bordercolor="#1f1f1f",
            borderwidth=1,
            rowheight=24,
        )
        style.map("Dark.Treeview", background=[("selected", "#2b7de9")])
        tv.configure(style="Dark.Treeview")

    class DashboardCard(ctk.CTkFrame):
        def __init__(self, master, title: str, value_var: tk.StringVar):
            super().__init__(master, fg_color="#1f1f1f", corner_radius=12)
            ctk.CTkLabel(self, text=title, text_color="#b0b0b0", font=("Segoe UI", 12)).pack(pady=(10, 0))
            ctk.CTkLabel(self, textvariable=value_var, font=("Segoe UI", 24, "bold"), text_color="white").pack(
                pady=(4, 12)
            )

    class WorkforceGUI:
        def __init__(self, root: ctk.CTk, db: Database):
            self.root = root
            self.db = db
            self.admin_user = os.getenv("WORKFORCE_ADMIN_USER", "admin")
            self.admin_pass = os.getenv("WORKFORCE_ADMIN_PASS", "admin")
            self.current_user: str | None = "auto"

            self.root.title("Workforce Analytics - Dark")
            self.root.geometry("1280x800")

            self.status_user = tk.StringVar(value="Logged in (temporary)")
            self.burnout_view = os.getenv("WORKFORCE_BURNOUT_VIEW", "v_weekly_hours_summary")
            self.revenue_view = os.getenv("WORKFORCE_REVENUE_VIEW", "v_daily_payroll")
            self.ot_pay_view = os.getenv("WORKFORCE_OT_PAY_VIEW", "v_daily_payroll")
            self._build_layout()

        def _build_layout(self) -> None:
            sidebar = ctk.CTkFrame(self.root, width=220, fg_color="#0f0f0f")
            sidebar.pack(side="left", fill="y")

            ctk.CTkLabel(sidebar, text="Workforce Analytics", font=("Segoe UI", 16, "bold"), text_color="white").pack(
                pady=(20, 10)
            )
            ctk.CTkLabel(sidebar, textvariable=self.status_user, text_color="#8fa5ff").pack(pady=(0, 10))

            ctk.CTkButton(sidebar, text="Login", command=self._login, fg_color="#2b7de9").pack(padx=12, pady=4, fill="x")
            ctk.CTkButton(sidebar, text="Logout", command=self._logout, fg_color="#444").pack(padx=12, pady=4, fill="x")

            ctk.CTkLabel(sidebar, text="Menu", text_color="#b0b0b0").pack(pady=(16, 4))
            buttons = [
                ("Dashboard", self._show_dashboard),
                ("Employees", self._show_employees),
                ("Time Records", self._show_time),
                ("Analytics", self._show_analytics),
                ("Views", self._show_views),
            ]
            for text, cmd in buttons:
                ctk.CTkButton(sidebar, text=text, command=cmd, fg_color="#2b7de9").pack(padx=12, pady=4, fill="x")

            main_frame = ctk.CTkFrame(self.root, fg_color="#171717")
            main_frame.pack(side="left", fill="both", expand=True)

            self.notebook = ctk.CTkTabview(main_frame)
            self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

            self.dashboard_tab = self.notebook.add("Dashboard")
            self.emp_tab = self.notebook.add("Employees")
            self.time_tab = self.notebook.add("Time Records")
            self.analytics_tab = self.notebook.add("Analytics")
            self.view_tab = self.notebook.add("Views")

            self._build_dashboard_tab()
            self._build_employee_tab()
            self._build_time_tab()
            self._build_analytics_tab()
            self._build_view_tab()

        def _require_auth(self, action: str) -> bool:
            return True

        def _login(self) -> None:
            if self.current_user:
                messagebox.showinfo("Already logged in", f"Current admin: {self.current_user}")
                return
            user = ctk.CTkInputDialog(text="Username", title="Admin login").get_input()
            if user is None:
                return
            pwd = ctk.CTkInputDialog(text="Password", title="Admin login").get_input()
            if user == self.admin_user and pwd == self.admin_pass:
                self.current_user = user
                self.status_user.set(f"Logged in as {user}")
                gui_logger.info("GUI admin login %s", user)
                messagebox.showinfo("Success", "Login successful.")
                self._refresh_dashboard()
                self._refresh_employees()
                self._refresh_time_records()
            else:
                gui_logger.warning("GUI admin login failed for user=%s", user)
                messagebox.showerror("Error", "Invalid credentials.")

        def _logout(self) -> None:
            if not self.current_user:
                messagebox.showinfo("Not logged in", "No admin session.")
                return
            gui_logger.info("GUI admin logout %s", self.current_user)
            self.current_user = None
            self.status_user.set("Not logged in")
            self._refresh_dashboard()
            self._refresh_employees()
            self._refresh_time_records()

        def _show_dashboard(self) -> None:
            self.notebook.set("Dashboard")

        def _show_employees(self) -> None:
            self.notebook.set("Employees")

        def _show_time(self) -> None:
            self.notebook.set("Time Records")

        def _show_analytics(self) -> None:
            self.notebook.set("Analytics")

        def _show_views(self) -> None:
            self.notebook.set("Views")

        def _build_dashboard_tab(self) -> None:
            cards_frame = ctk.CTkFrame(self.dashboard_tab, fg_color="#171717")
            cards_frame.pack(fill="x", padx=10, pady=10)

            self.headcount_var = tk.StringVar(value="-")
            self.revenue_var = tk.StringVar(value="-")
            self.ot_var = tk.StringVar(value="-")
            self.burnout_var = tk.StringVar(value="-")
            self.ot_period_var = tk.StringVar(value="month")
            self.department_var = tk.StringVar(value="All")
            self.year_var = tk.StringVar(value="")
            self.month_var = tk.StringVar(value="")

            for var, title in [
                (self.headcount_var, "Total Employee"),
                (self.ot_var, "Total OT"),
                (self.revenue_var, "Total Revenue"),
                (self.burnout_var, "Burnout Risk (>60 hrs)"),
            ]:
                DashboardCard(cards_frame, title, var).pack(side="left", padx=6, fill="x", expand=True)

            controls = ctk.CTkFrame(self.dashboard_tab, fg_color="#171717")
            controls.pack(fill="x", padx=10, pady=(0, 6))
            ctk.CTkLabel(controls, text="Year:").pack(side="left", padx=(12, 4))
            ctk.CTkComboBox(
                controls,
                variable=self.year_var,
                values=["", "2024", "2025"],
                width=90,
            ).pack(side="left", padx=4)
            ctk.CTkLabel(controls, text="Month:").pack(side="left", padx=(12, 4))
            ctk.CTkComboBox(
                controls,
                variable=self.month_var,
                values=[""] + [f"{m:02d}" for m in range(1, 13)],
                width=80,
            ).pack(side="left", padx=4)
            ctk.CTkButton(controls, text="Apply", command=self._refresh_dashboard, fg_color="#2b7de9").pack(
                side="left", padx=6
            )

            self.fig = Figure(figsize=(7, 3), facecolor="#101010")
            self.ax_bar = self.fig.add_subplot(211, facecolor="#101010")
            self.ax_line = self.fig.add_subplot(212, facecolor="#101010")
            self.canvas_fig = FigureCanvasTkAgg(self.fig, master=self.dashboard_tab)
            self.canvas_fig.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)

            ctk.CTkButton(
                self.dashboard_tab, text="Refresh dashboard", command=self._refresh_dashboard, fg_color="#2b7de9"
            ).pack(pady=6)

            self._refresh_dashboard()

        def _refresh_dashboard(self) -> None:
            if not self._require_auth("view dashboard"):
                self.headcount_var.set("-")
                self.revenue_var.set("-")
                self.ot_var.set("-")
                self.burnout_var.set("-")
                self._clear_fig()
                return

            year_filter = int(self.year_var.get()) if self.year_var.get() else None
            month_filter = int(self.month_var.get()) if self.month_var.get() else None
            period = (self.ot_period_var.get() or "month").lower()

            try:
                if year_filter is None and month_filter is None:
                    employees = get_all_employees(self.db)
                    headcount = len(employees)
                else:
                    headcount = count_employees_by_time_records(self.db, year=year_filter, month=month_filter)
                    if headcount == 0:
                        employees = get_all_employees(self.db)
                        headcount = len(employees)
                self.headcount_var.set(f"{headcount:,}")
            except Exception as exc:  # noqa: BLE001
                try:
                    employees = get_all_employees(self.db)
                    self.headcount_var.set(f"{len(employees):,}")
                except Exception:
                    self.headcount_var.set("error")
                gui_logger.error("Error fetching employees: %s", exc)

            try:
                ot_summary = summarize_ot(
                    self.db,
                    period=period,
                    limit=12,
                    department=None,
                    year=year_filter,
                    month=month_filter,
                )
            except Exception as exc:  # noqa: BLE001
                ot_summary = []
                gui_logger.error("Error summarizing OT (%s): %s", period, exc)

            if ot_summary:
                total_hours = sum(float(row.get("ot_hours") or 0) for row in ot_summary)
                self.ot_var.set(f"{total_hours:,.2f}")
            else:
                self.ot_var.set("-")
                self.burnout_var.set("-")

            try:
                revenue_summary = summarize_payroll(
                    self.db,
                    view_name=self.revenue_view,
                    period=period,
                    limit=12,
                    year=year_filter,
                    month=month_filter,
                )
            except Exception as exc:  # noqa: BLE001
                revenue_summary = []
                gui_logger.error("Error summarizing revenue (%s): %s", period, exc)

            try:
                revenue_trend = summarize_payroll(
                    self.db,
                    view_name=self.revenue_view,
                    period=period,
                    limit=12,
                    year=year_filter,
                    month=month_filter,
                )
            except Exception as exc:  # noqa: BLE001
                revenue_trend = []
                gui_logger.error("Error summarizing revenue trend (%s): %s", period, exc)

            if revenue_summary:
                total_revenue = sum(float(row.get("total_pay") or 0) for row in revenue_summary)
                self.revenue_var.set(f"{total_revenue:,.2f}")
            else:
                self.revenue_var.set("-")

            try:
                burnout_count = count_burnout_view(
                    self.db,
                    self.burnout_view,
                    column="total_ot_hours",
                    threshold_hours=60.0,
                )
                self.burnout_var.set(f"{burnout_count:,}")
            except Exception as exc:  # noqa: BLE001
                self.burnout_var.set("-")
                gui_logger.error("Error counting burnout view %s: %s", self.burnout_view, exc)

            try:
                dept_summary = summarize_ot_by_department(
                    self.db,
                    limit=20,
                    year=year_filter,
                    month=month_filter,
                )
            except Exception as exc:  # noqa: BLE001
                dept_summary = []
                gui_logger.error("Error summarizing OT by department: %s", exc)

            try:
                revenue_dept = summarize_revenue_by_department(
                    self.db,
                    view_name=self.revenue_view,
                    limit=20,
                    year=year_filter,
                    month=month_filter,
                )
            except Exception as exc:  # noqa: BLE001
                revenue_dept = []
                gui_logger.error("Error summarizing revenue by department: %s", exc)

            self._render_ot_charts(revenue_trend, dept_summary, revenue_dept, period)

        def _clear_fig(self) -> None:
            self.ax_bar.clear()
            self.ax_line.clear()
            self.canvas_fig.draw_idle()

        def _load_departments(self) -> None:
            if not self.current_user:
                return
            try:
                dept_rows = list_departments(self.db)
                names = ["All"] + [row.get("dept_name") or row.get("dept_id") for row in dept_rows if row]
                if hasattr(self, "dept_combo"):
                    self.dept_combo.configure(values=names)
                    if self.department_var.get() not in names:
                        self.department_var.set("All")
            except Exception as exc:  # noqa: BLE001
                gui_logger.error("Error loading departments: %s", exc)

        def _render_ot_charts(self, revenue_trend, dept_summary, revenue_dept, period: str) -> None:
            self.ax_bar.clear()
            self.ax_line.clear()

            if dept_summary:
                dept_labels = [str(row.get("department")) for row in dept_summary]
                dept_hours = [float(row.get("ot_hours") or 0) for row in dept_summary]
                self.ax_bar.bar(dept_labels, dept_hours, color="#2b7de9")
                self.ax_bar.tick_params(axis="x", rotation=45, colors="white")
                self.ax_bar.tick_params(axis="y", colors="white")
                self.ax_bar.set_facecolor("#101010")
                self.ax_bar.spines["bottom"].set_color("white")
                self.ax_bar.spines["left"].set_color("white")
                self.ax_bar.set_title("OT by department (filtered)", color="white")
            else:
                self.ax_bar.set_title("No OT by department data", color="white")

            if revenue_dept:
                rev_labels = [str(row.get("department")) for row in revenue_dept]
                rev_vals = [float(row.get("total_pay") or 0) for row in revenue_dept]
                self.ax_line.bar(rev_labels, rev_vals, color="#2b7de9")
                self.ax_line.tick_params(axis="x", rotation=45, colors="white")
                self.ax_line.tick_params(axis="y", colors="white")
                self.ax_line.set_facecolor("#101010")
                self.ax_line.spines["bottom"].set_color("white")
                self.ax_line.spines["left"].set_color("white")
                self.ax_line.set_title("Revenue by department (filtered)", color="white")
            else:
                self.ax_line.set_title("Revenue by department (no data)", color="white")

            self.fig.tight_layout()
            self.canvas_fig.draw_idle()

        def _build_employee_tab(self) -> None:
            form = ctk.CTkFrame(self.emp_tab, fg_color="#121212")
            form.pack(fill="x", padx=10, pady=10)

            self.emp_fields = {
                k: tk.StringVar() for k in ["emp_id", "department", "position", "base_salary", "start_date", "dept_id"]
            }
            labels = [
                ("Employee ID", "emp_id"),
                ("Department", "department"),
                ("Position", "position"),
                ("Base salary", "base_salary"),
                ("Start date (YYYY-MM-DD)", "start_date"),
                ("Dept ID", "dept_id"),
            ]
            for idx, (text, key) in enumerate(labels):
                ctk.CTkLabel(form, text=text).grid(row=idx, column=0, sticky="w", pady=4, padx=4)
                ctk.CTkEntry(form, textvariable=self.emp_fields[key], width=260).grid(row=idx, column=1, sticky="w", pady=4)

            btns = ctk.CTkFrame(form, fg_color="transparent")
            btns.grid(row=len(labels), column=0, columnspan=2, pady=8, sticky="w")
            ctk.CTkButton(btns, text="Add", command=self._add_employee, fg_color="#2b7de9").pack(side="left", padx=4)
            ctk.CTkButton(btns, text="Update", command=self._update_employee, fg_color="#2b7de9").pack(
                side="left", padx=4
            )
            ctk.CTkButton(btns, text="Delete", command=self._delete_employee, fg_color="#aa2e2e").pack(
                side="left", padx=4
            )
            ctk.CTkButton(btns, text="Refresh", command=self._refresh_employees, fg_color="#444").pack(
                side="left", padx=4
            )

            columns = ("emp_id", "department", "position", "base_salary", "start_date", "dept_id")
            self.emp_tree = tk.ttk.Treeview(self.emp_tab, columns=columns, show="headings", height=12)
            for col in columns:
                self.emp_tree.heading(col, text=col)
                self.emp_tree.column(col, width=140, anchor="w")
            self.emp_tree.pack(fill="both", expand=True, padx=10, pady=10)
            _style_treeview(self.emp_tree)
            self.emp_tree.bind("<<TreeviewSelect>>", self._on_emp_select)

            self._refresh_employees()

        def _on_emp_select(self, event):
            sel = self.emp_tree.selection()
            if not sel:
                return
            values = self.emp_tree.item(sel[0], "values")
            for key, val in zip(self.emp_fields.keys(), values):
                self.emp_fields[key].set(val or "")

        def _add_employee(self) -> None:
            if not self._require_auth("add employees"):
                return
            data = {k: v.get().strip() or None for k, v in self.emp_fields.items()}
            emp_id = data["emp_id"]
            if not emp_id:
                messagebox.showerror("Error", "Employee ID is required.")
                return
            dept_id = data.get("dept_id")
            if dept_id and not department_exists(self.db, dept_id):
                messagebox.showerror("Error", f"Dept ID '{dept_id}' not found.")
                return
            try:
                base_salary_val = float(data["base_salary"]) if data["base_salary"] else None
            except ValueError:
                messagebox.showerror("Error", "Base salary must be numeric.")
                return
            try:
                add_employee(
                    self.db,
                    emp_id=emp_id,
                    department=data.get("department"),
                    position=data.get("position"),
                    base_salary=base_salary_val,
                    start_date=data.get("start_date"),
                    dept_id=dept_id,
                )
                gui_logger.info("GUI add employee %s", emp_id)
                self._refresh_employees()
                messagebox.showinfo("Success", f"Employee {emp_id} added.")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))

        def _update_employee(self) -> None:
            if not self._require_auth("update employees"):
                return
            data = {k: v.get().strip() or None for k, v in self.emp_fields.items()}
            emp_id = data["emp_id"]
            if not emp_id:
                messagebox.showerror("Error", "Employee ID is required.")
                return
            dept_id = data.get("dept_id")
            if dept_id and not department_exists(self.db, dept_id):
                messagebox.showerror("Error", f"Dept ID '{dept_id}' not found.")
                return
            try:
                base_salary_val = float(data["base_salary"]) if data["base_salary"] else None
            except ValueError:
                messagebox.showerror("Error", "Base salary must be numeric.")
                return
            try:
                updated = update_employee(
                    self.db,
                    emp_id=emp_id,
                    department=data.get("department"),
                    position=data.get("position"),
                    base_salary=base_salary_val,
                    start_date=data.get("start_date"),
                    dept_id=dept_id,
                )
                if updated:
                    gui_logger.info("GUI update employee %s", emp_id)
                    self._refresh_employees()
                    messagebox.showinfo("Success", "Employee updated.")
                else:
                    messagebox.showwarning("No change", "No fields changed or employee not found.")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))

        def _delete_employee(self) -> None:
            if not self._require_auth("delete employees"):
                return
            emp_id = self.emp_fields["emp_id"].get().strip()
            if not emp_id:
                messagebox.showerror("Error", "Employee ID is required.")
                return
            if not messagebox.askyesno("Confirm", f"Delete employee {emp_id}?"):
                return
            try:
                removed = delete_employee(self.db, emp_id)
                if removed:
                    gui_logger.info("GUI delete employee %s", emp_id)
                    self._refresh_employees()
                    messagebox.showinfo("Deleted", "Employee removed.")
                else:
                    messagebox.showwarning("Not found", "Employee not found.")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))

        def _refresh_employees(self) -> None:
            if not self.current_user:
                for row in self.emp_tree.get_children():
                    self.emp_tree.delete(row)
                return
            for row in self.emp_tree.get_children():
                self.emp_tree.delete(row)
            try:
                employees = get_all_employees(self.db)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))
                return
            for emp in employees:
                self.emp_tree.insert(
                    "",
                    "end",
                    values=(
                        emp.get("emp_id"),
                        emp.get("department"),
                        emp.get("position"),
                        emp.get("base_salary"),
                        emp.get("start_date"),
                        emp.get("dept_id"),
                    ),
                )

        def _build_time_tab(self) -> None:
            form = ctk.CTkFrame(self.time_tab, fg_color="#121212")
            form.pack(fill="x", padx=10, pady=10)
            keys = [
                "emp_id",
                "work_date",
                "shift_code",
                "clock_in",
                "clock_out",
                "job_type",
                "department",
                "bf_ot",
                "af_ot",
                "bt_ot",
            ]
            self.time_fields = {k: tk.StringVar() for k in keys}
            labels = [
                ("Employee ID", "emp_id"),
                ("Work date (YYYY-MM-DD)", "work_date"),
                ("Shift code", "shift_code"),
                ("Clock in (HH:MM:SS)", "clock_in"),
                ("Clock out (HH:MM:SS)", "clock_out"),
                ("Job type", "job_type"),
                ("Department", "department"),
                ("Before OT", "bf_ot"),
                ("After OT", "af_ot"),
                ("Between OT", "bt_ot"),
            ]
            for idx, (text, key) in enumerate(labels):
                ctk.CTkLabel(form, text=text).grid(row=idx, column=0, sticky="w", pady=3, padx=4)
                ctk.CTkEntry(form, textvariable=self.time_fields[key], width=260).grid(row=idx, column=1, sticky="w", pady=3)

            btns = ctk.CTkFrame(form, fg_color="transparent")
            btns.grid(row=len(labels), column=0, columnspan=2, pady=8, sticky="w")
            ctk.CTkButton(btns, text="Add record", command=self._add_time_record, fg_color="#2b7de9").pack(
                side="left", padx=4
            )
            ctk.CTkButton(btns, text="Delete record", command=self._delete_time_record, fg_color="#aa2e2e").pack(
                side="left", padx=4
            )
            ctk.CTkButton(btns, text="Refresh", command=self._refresh_time_records, fg_color="#444").pack(
                side="left", padx=4
            )

            columns = tuple(keys)
            self.time_tree = tk.ttk.Treeview(self.time_tab, columns=columns, show="headings", height=12)
            for col in columns:
                self.time_tree.heading(col, text=col)
                self.time_tree.column(col, width=120, anchor="w")
            self.time_tree.pack(fill="both", expand=True, padx=10, pady=10)
            _style_treeview(self.time_tree)
            self.time_tree.bind("<<TreeviewSelect>>", self._on_time_select)

            self._refresh_time_records()

        def _add_time_record(self) -> None:
            if not self._require_auth("add time records"):
                return
            data = {k: v.get().strip() or None for k, v in self.time_fields.items()}
            if not data["emp_id"] or not data["work_date"]:
                messagebox.showerror("Error", "Employee ID and Work date are required.")
                return
            try:
                add_time_record(
                    self.db,
                    emp_id=data["emp_id"],
                    work_date=data["work_date"],
                    shift_code=data.get("shift_code"),
                    clock_in=data.get("clock_in"),
                    clock_out=data.get("clock_out"),
                    job_type=data.get("job_type"),
                    department=data.get("department"),
                    bf_ot=data.get("bf_ot"),
                    af_ot=data.get("af_ot"),
                    bt_ot=data.get("bt_ot"),
                )
                gui_logger.info("GUI add time record emp_id=%s date=%s", data["emp_id"], data["work_date"])
                self._refresh_time_records()
                messagebox.showinfo("Success", "Time record added.")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))

        def _delete_time_record(self) -> None:
            if not self._require_auth("delete time records"):
                return
            sel = self.time_tree.selection()
            if sel:
                values = self.time_tree.item(sel[0], "values")
                emp_id = values[0]
                work_date = values[1]
            else:
                emp_id = self.time_fields["emp_id"].get().strip()
                work_date = self.time_fields["work_date"].get().strip()
            if not emp_id or not work_date:
                messagebox.showerror("Error", "Select a row or fill Employee ID and Work date.")
                return
            if not messagebox.askyesno("Confirm", f"Delete time record for {emp_id} on {work_date}?"):
                return
            try:
                removed = delete_time_record(self.db, emp_id, work_date)
                if removed:
                    gui_logger.info("GUI delete time record emp_id=%s date=%s", emp_id, work_date)
                    self._refresh_time_records()
                    messagebox.showinfo("Deleted", "Time record removed.")
                else:
                    messagebox.showwarning("Not found", "Time record not found.")
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))

        def _refresh_time_records(self) -> None:
            if not self.current_user:
                for row in self.time_tree.get_children():
                    self.time_tree.delete(row)
                return
            for row in self.time_tree.get_children():
                self.time_tree.delete(row)
            try:
                records = fetch_time_records(self.db, limit=100)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))
                return
            for rec in records:
                self.time_tree.insert(
                    "",
                    "end",
                    values=tuple(rec.get(col) for col in self.time_tree["columns"]),
                )

        def _on_time_select(self, event):
            sel = self.time_tree.selection()
            if not sel:
                return
            values = self.time_tree.item(sel[0], "values")
            for key, val in zip(self.time_fields.keys(), values):
                self.time_fields[key].set(val or "")

        def _build_analytics_tab(self) -> None:
            frame = ctk.CTkFrame(self.analytics_tab, fg_color="#121212")
            frame.pack(fill="x", padx=10, pady=10)
            self.top_n_var = tk.StringVar(value="1000")
            self.analytics_period = tk.StringVar(value="week")
            self.analytics_year = tk.StringVar(value="")
            self.analytics_month = tk.StringVar(value="")
            self.analytics_week = tk.StringVar(value="")

            ctk.CTkLabel(frame, text="Year:").grid(row=0, column=0, padx=(12, 4))
            ctk.CTkEntry(frame, textvariable=self.analytics_year, width=70).grid(row=0, column=1, padx=4)
            ctk.CTkLabel(frame, text="Month:").grid(row=0, column=2, padx=(12, 4))
            ctk.CTkEntry(frame, textvariable=self.analytics_month, width=70).grid(row=0, column=3, padx=4)
            ctk.CTkLabel(frame, text="Week:").grid(row=0, column=4, padx=(12, 4))
            ctk.CTkEntry(frame, textvariable=self.analytics_week, width=70).grid(row=0, column=5, padx=4)
            ctk.CTkButton(frame, text="Load OT daily", command=self._show_ot_avg_trend, fg_color="#2b7de9").grid(
                row=0, column=6, padx=(12, 4)
            )

            plot_frame = ctk.CTkFrame(self.analytics_tab, fg_color="#101010")
            plot_frame.pack(fill="both", expand=True, padx=10, pady=10)
            self.analytics_fig = Figure(figsize=(6, 3), facecolor="#101010")
            self.analytics_ax = self.analytics_fig.add_subplot(111, facecolor="#101010")
            self.analytics_canvas = FigureCanvasTkAgg(self.analytics_fig, master=plot_frame)
            self.analytics_canvas.get_tk_widget().pack(fill="both", expand=True)

        def _get_top_n(self) -> int:
            try:
                return max(1, min(int(self.top_n_var.get() or "5"), 500))
            except ValueError:
                return 5

        def _show_burnout_insight(self) -> None:
            self._render_insight(
                view="v_burnout_ranking",
                metrics=["burnout_score", "burnout_rank"],
                title="Burnout ranking (score)",
            )

        def _show_ot_insight(self) -> None:
            self._render_insight(
                view="v_weekly_ot_department",
                metrics=["total_ot_hours", "avg_ot_hours_per_employee"],
                title="OT ranking by department",
            )

        def _show_ot_pay_insight(self) -> None:
            self._render_insight(
                view=self.ot_pay_view,
                metrics=["total_ot_pay", "total_pay"],
                title="OT pay by department",
            )

        def _show_ot_avg_trend(self) -> None:
            if not self._require_auth("view analytics"):
                return
            view = "v_ot_trend"
            try:
                rows = fetch_view_rows(self.db, view, limit=500)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))
                return
            rows = self._filter_rows_by_period(rows)
            self._render_insight_chart(
                rows,
                metrics=["ot_daily", "total_ot_hours", "total_ot_pay"],
                title="Daily OT by department",
                top_n=None,
            )

        def _render_insight(self, view: str, metrics: list[str], title: str) -> None:
            if not self._require_auth("view analytics"):
                return
            limit = self._get_top_n()
            try:
                rows = fetch_view_rows(self.db, view, limit=500)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))
                return
            rows = self._filter_rows_by_period(rows)
            self._render_insight_chart(rows, metrics, title, top_n=limit)

        def _render_insight_chart(self, rows, metrics: list[str], title: str, top_n: int | None = 10) -> None:
            self.analytics_ax.clear()
            if not rows:
                self.analytics_ax.set_title("No data", color="white")
                self.analytics_canvas.draw_idle()
                return

            dept_key = None
            for key in ("department_name", "department"):
                if key in rows[0]:
                    dept_key = key
                    break
            if dept_key is None:
                self.analytics_ax.set_title("No department field", color="white")
                self.analytics_canvas.draw_idle()
                return

            metric_key = None
            for m in metrics:
                if m in rows[0]:
                    metric_key = m
                    break
            if metric_key is None:
                self.analytics_ax.set_title("Metric not found", color="white")
                self.analytics_canvas.draw_idle()
                return

            agg = {}
            for row in rows:
                dept = row.get(dept_key) or "Unknown"
                val = row.get(metric_key)
                if val is None:
                    continue
                try:
                    agg[dept] = agg.get(dept, 0.0) + float(val)
                except Exception:
                    continue

            if not agg:
                self.analytics_ax.set_title("No data", color="white")
                self.analytics_canvas.draw_idle()
                return

            sorted_pairs = sorted(agg.items(), key=lambda x: x[1], reverse=True)
            if top_n:
                sorted_pairs = sorted_pairs[:top_n]
            labels, vals = zip(*sorted_pairs)

            self.analytics_ax.bar(labels, vals, color="#2b7de9")
            self.analytics_ax.tick_params(axis="x", rotation=45, colors="white")
            self.analytics_ax.tick_params(axis="y", colors="white")
            self.analytics_ax.set_facecolor("#101010")
            self.analytics_ax.spines["bottom"].set_color("white")
            self.analytics_ax.spines["left"].set_color("white")
            self.analytics_ax.set_title(f"{title} (top {top_n})", color="white")
            self.analytics_fig.tight_layout()
            self.analytics_canvas.draw_idle()

        def _filter_rows_by_period(self, rows):
            if not rows:
                return rows
            year_val = self.analytics_year.get().strip()
            month_val = self.analytics_month.get().strip()
            week_val = self.analytics_week.get().strip()
            if not (year_val or month_val or week_val):
                return rows

            def matches(row):
                if year_val:
                    for key in ("year", "yr"):
                        if key in row:
                            try:
                                if int(row[key]) != int(year_val):
                                    return False
                            except Exception:
                                return False
                if month_val:
                    for key in ("month", "mn"):
                        if key in row:
                            try:
                                if int(row[key]) != int(month_val):
                                    return False
                            except Exception:
                                return False
                if week_val:
                    for key in ("week", "week_num", "wk"):
                        if key in row:
                            try:
                                if int(row[key]) != int(week_val):
                                    return False
                            except Exception:
                                return False
                return True

            filtered = [r for r in rows if matches(r)]
            return filtered or rows

        def _build_view_tab(self) -> None:
            wrapper = ctk.CTkFrame(self.view_tab, fg_color="#121212")
            wrapper.pack(fill="both", expand=True, padx=10, pady=10)

            view_frame = ctk.CTkFrame(wrapper, fg_color="#171717")
            view_frame.pack(fill="x", pady=4)
            ctk.CTkLabel(view_frame, text="View:").pack(side="left", padx=4)
            self.view_var = tk.StringVar()
            self.view_combo = ctk.CTkComboBox(view_frame, variable=self.view_var, width=240)
            self.view_combo.pack(side="left", padx=4)
            ctk.CTkButton(view_frame, text="Refresh", command=self._refresh_views, fg_color="#444").pack(
                side="left", padx=4
            )
            ctk.CTkButton(view_frame, text="Fetch", command=self._fetch_view, fg_color="#2b7de9").pack(
                side="left", padx=4
            )

            table_wrapper = ctk.CTkFrame(wrapper, fg_color="#101010")
            table_wrapper.pack(fill="both", expand=True, pady=8)
            style = tk.ttk.Style()
            style.configure("View.Treeview", font=("Segoe UI", 13))
            style.configure("View.Treeview.Heading", font=("Segoe UI", 13, "bold"))

            self.view_tree = tk.ttk.Treeview(table_wrapper, show="headings", style="View.Treeview")
            vsb = tk.Scrollbar(table_wrapper, orient="vertical", command=self.view_tree.yview)
            hsb = tk.Scrollbar(table_wrapper, orient="horizontal", command=self.view_tree.xview)
            self.view_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set, height=18)
            self.view_tree.pack(side="left", fill="both", expand=True)
            vsb.pack(side="right", fill="y")
            hsb.pack(side="bottom", fill="x")
            _style_treeview(self.view_tree)

            self._refresh_views()

        def _refresh_views(self) -> None:
            if not self.current_user:
                self.view_combo.set("")
                self.view_combo.configure(values=[])
                return
            try:
                views = list_database_views(self.db)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))
                return
            self.view_combo.configure(values=views)
            if views:
                self.view_combo.set(views[0])

        def _fetch_view(self) -> None:
            if not self._require_auth("fetch views"):
                return
            view = self.view_var.get()
            if not view:
                messagebox.showwarning("Select view", "Please select a view.")
                return
            try:
                rows = fetch_view_rows(self.db, view, limit=200)
            except Exception as exc:  # noqa: BLE001
                messagebox.showerror("Error", str(exc))
                return
            self._render_table(rows)

        def _render_table(self, rows) -> None:
            for col in self.view_tree["columns"]:
                self.view_tree.heading(col, text="")
                self.view_tree.column(col, width=100)
            self.view_tree.delete(*self.view_tree.get_children())

            if not rows:
                self.view_tree["columns"] = ["message"]
                self.view_tree.heading("message", text="No rows returned")
                self.view_tree.column("message", width=200, anchor="w")
                return

            columns = list(rows[0].keys())
            self.view_tree["columns"] = columns
            for col in columns:
                self.view_tree.heading(col, text=col)
                self.view_tree.column(col, width=120, anchor="w")

            for row in rows:
                vals = [row.get(col) for col in columns]
                self.view_tree.insert("", "end", values=vals)

    root = ctk.CTk()
    WorkforceGUI(root, db)
    root.mainloop()


def run_cli(db: Database) -> None:
    while True:
        print_menu()
        choice = input("Select an option: ").strip()
        if choice == "1":
            login_flow()
        elif choice == "2":
            logout_flow()
        elif choice == "3":
            init_db(db)
        elif choice == "4":
            add_employee_flow(db)
        elif choice == "5":
            update_employee_flow(db)
        elif choice == "6":
            delete_employee_flow(db)
        elif choice == "7":
            list_employees_flow(db)
        elif choice == "8":
            log_time_record_flow(db)
        elif choice == "9":
            analytics_flow(db)
        elif choice == "10":
            views_flow(db)
        elif choice == "11":
            tables_flow(db)
        elif choice == "12":
            featured_views_flow(db)
        elif choice == "0":
            print("Goodbye.")
            break
        else:
            print("Unknown option. Please choose again.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Workforce system CLI/GUI launcher.")
    parser.add_argument(
        "--gui",
        action="store_true",
        help="Launch the GUI dashboard (requires tkinter, customtkinter, matplotlib).",
    )
    args = parser.parse_args()

    db = connect_db()
    if args.gui:
        try:
            run_gui(db)
        except ImportError as exc:
            print(f"GUI dependencies missing: {exc}. Falling back to CLI.")
            run_cli(db)
    else:
        run_cli(db)


if __name__ == "__main__":
    main()
