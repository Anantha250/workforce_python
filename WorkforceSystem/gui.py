#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from config.db_config import DatabaseConfig
from modules.crud import (
    add_employee,
    add_time_record,
    count_burnout_view,
    count_employees_by_time_records,
    delete_time_record,
    delete_employee,
    department_exists,
    list_departments,
    fetch_table_rows,
    fetch_time_records,
    fetch_view_rows,
    get_all_employees,
    list_database_tables,
    list_database_views,
    summarize_payroll,
    summarize_ot,
    summarize_ot_by_department,
    summarize_ot_department_view,
    summarize_revenue_by_department,
    update_employee,
)
from modules.db import Database
from modules.textlog import LOG_PATH, get_logger

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

logger = get_logger("workforce.gui")

PALETTE = {
    "bg": "#f8f9fb",
    "panel": "#fdfdfd",
    "card": "#ffffff",
    "card_alt": "#f4f7f7",
    "accent": "#f3a6c6",  # blush
    "accent_hover": "#f7b9d3",
    "accent2": "#9ed4d6",  # mint
    "accent2_hover": "#b0dfe0",
    "accent3": "#c7c5f6",  # lavender
    "accent3_hover": "#d6d5fa",
    "accent4": "#f9d984",  # lemon
    "accent4_hover": "#fbe5a6",
    "muted": "#7a6f73",
    "text": "#000000",
    "border": "#dfe5e6",
    "danger": "#f18ba8",
    "neutral": "#eef2f3",
    "table_bg": "#fbfdfe",
    "selection": "#e9f4f4",
    "chart_face": "#fbfefe",
}


def _style_treeview(tv: tk.Widget) -> None:
    style = tk.ttk.Style()
    style.configure(
        "Petal.Treeview",
        background=PALETTE["table_bg"],
        foreground=PALETTE["text"],
        fieldbackground=PALETTE["table_bg"],
        bordercolor=PALETTE["border"],
        borderwidth=1,
        rowheight=24,
        font=("Segoe UI", 12),
    )
    style.configure("Petal.Treeview.Heading", font=("Segoe UI", 13, "bold"))
    style.map(
        "Petal.Treeview",
        background=[("selected", PALETTE["selection"])],
        foreground=[("selected", PALETTE["text"])],
    )
    tv.configure(style="Petal.Treeview")


class DashboardCard(ctk.CTkFrame):
    def __init__(self, master, title: str, value_var: tk.StringVar):
        super().__init__(
            master,
            fg_color=PALETTE["card"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["border"],
        )
        ctk.CTkLabel(self, text=title, text_color=PALETTE["text"], font=("Segoe UI", 12)).pack(pady=(10, 0))
        ctk.CTkLabel(self, textvariable=value_var, font=("Segoe UI", 24, "bold"), text_color=PALETTE["text"]).pack(
            pady=(4, 12)
        )


class WorkforceGUI:
    def __init__(self, root: ctk.CTk, db: Database):
        self.root = root
        self.db = db
        self.admin_user = os.getenv("WORKFORCE_ADMIN_USER", "admin")
        self.admin_pass = os.getenv("WORKFORCE_ADMIN_PASS", "admin")
        # Temp: keep user always logged in
        self.current_user: str | None = "auto"

        self.root.title("Workforce Analytics - Petal")
        self.root.geometry("1280x800")
        self.root.configure(fg_color=PALETTE["bg"])

        self.status_user = tk.StringVar(value="Logged in (temporary)")
        self.burnout_view = os.getenv("WORKFORCE_BURNOUT_VIEW", "v_weekly_hours_summary")
        self.revenue_view = os.getenv("WORKFORCE_REVENUE_VIEW", "v_daily_payroll")
        self.ot_pay_view = os.getenv("WORKFORCE_OT_PAY_VIEW", "v_daily_payroll")
        self.ot_trend_view: str | None = None
        self.current_view_rows: list[dict] = []
        self.current_view_name: str = ""
        self._build_layout()

    # Layout
    def _build_layout(self) -> None:
        # Sidebar
        sidebar = ctk.CTkFrame(self.root, width=220, fg_color=PALETTE["panel"])
        sidebar.pack(side="left", fill="y")

        ctk.CTkLabel(sidebar, text="Workforce Analytics", font=("Segoe UI", 16, "bold"), text_color=PALETTE["text"]).pack(
            pady=(20, 10)
        )
        ctk.CTkLabel(sidebar, textvariable=self.status_user, text_color=PALETTE["text"]).pack(pady=(0, 10))

        ctk.CTkButton(
            sidebar,
            text="Login",
            command=self._login,
            fg_color=PALETTE["accent2"],
            hover_color=PALETTE["accent2_hover"],
            text_color=PALETTE["text"],
        ).pack(padx=12, pady=4, fill="x")
        ctk.CTkButton(
            sidebar,
            text="Logout",
            command=self._logout,
            fg_color=PALETTE["neutral"],
            hover_color=PALETTE["selection"],
            text_color=PALETTE["text"],
        ).pack(padx=12, pady=4, fill="x")

        ctk.CTkLabel(sidebar, text="Menu", text_color=PALETTE["text"]).pack(pady=(16, 4))
        buttons = [
            ("Dashboard", self._show_dashboard),
            ("Employees", self._show_employees),
            ("Time Records", self._show_time),
            ("Analytics", self._show_analytics),
            ("Daily Payroll", self._show_daily_payroll),
            ("Monthly Payroll", self._show_monthly_payroll),
            ("OT Alerts", self._show_ot_alerts),
            ("Views", self._show_views),
            ("Export Logs", self._export_logs),
        ]
        btn_cycle = [
            (PALETTE["accent"], PALETTE["accent_hover"]),
            (PALETTE["accent2"], PALETTE["accent2_hover"]),
            (PALETTE["accent3"], PALETTE["accent3_hover"]),
            (PALETTE["accent4"], PALETTE["accent4_hover"]),
        ]
        for idx, (text, cmd) in enumerate(buttons):
            fg, hover = btn_cycle[idx % len(btn_cycle)]
            ctk.CTkButton(
                sidebar,
                text=text,
                command=cmd,
                fg_color=fg,
                hover_color=hover,
                text_color=PALETTE["text"],
            ).pack(padx=12, pady=4, fill="x")

        # Main area with notebook
        main_frame = ctk.CTkFrame(self.root, fg_color=PALETTE["bg"])
        main_frame.pack(side="left", fill="both", expand=True)

        self.notebook = ctk.CTkTabview(main_frame, fg_color=PALETTE["bg"])
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.dashboard_tab = self.notebook.add("Dashboard")
        self.emp_tab = self.notebook.add("Employees")
        self.time_tab = self.notebook.add("Time Records")
        self.analytics_tab = self.notebook.add("Analytics")
        self.daily_payroll_tab = self.notebook.add("Daily Payroll")
        self.monthly_payroll_tab = self.notebook.add("Monthly Payroll")
        self.ot_alerts_tab = self.notebook.add("OT Alerts")
        self.view_tab = self.notebook.add("Views")
        self._hide_tab_headers()

        self._build_dashboard_tab()
        self._build_employee_tab()
        self._build_time_tab()
        self._build_analytics_tab()
        self._build_daily_payroll_tab()
        self._build_monthly_payroll_tab()
        self._build_ot_alerts_tab()
        self._build_view_tab()

    # Auth helpers
    def _require_auth(self, action: str) -> bool:
        # Temporarily disabled auth gate
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
            logger.info("GUI admin login %s", user)
            messagebox.showinfo("Success", "Login successful.")
            self._refresh_dashboard()
            self._refresh_employees()
            self._refresh_time_records()
        else:
            logger.warning("GUI admin login failed for user=%s", user)
            messagebox.showerror("Error", "Invalid credentials.")

    def _logout(self) -> None:
        if not self.current_user:
            messagebox.showinfo("Not logged in", "No admin session.")
            return
        logger.info("GUI admin logout %s", self.current_user)
        self.current_user = None
        self.status_user.set("Not logged in")
        self._refresh_dashboard()
        self._refresh_employees()
        self._refresh_time_records()

    # Navigation
    def _show_dashboard(self) -> None:
        self.notebook.set("Dashboard")

    def _show_employees(self) -> None:
        self.notebook.set("Employees")

    def _show_time(self) -> None:
        self.notebook.set("Time Records")

    def _show_analytics(self) -> None:
        self.notebook.set("Analytics")

    def _show_daily_payroll(self) -> None:
        self.notebook.set("Daily Payroll")

    def _show_monthly_payroll(self) -> None:
        self.notebook.set("Monthly Payroll")

    def _show_ot_alerts(self) -> None:
        self.notebook.set("OT Alerts")

    def _show_views(self) -> None:
        self.notebook.set("Views")

    def _hide_tab_headers(self) -> None:
        """
        Hide the tabview segmented button so the top menu bar is removed; left sidebar buttons still switch tabs.
        """
        # CTkTabview renders its tab buttons in an internal segmented button.
        # Removing it keeps tab content functional while navigation is handled by the sidebar.
        try:
            self.notebook._segmented_button.grid_forget()
        except Exception:
            try:
                self.notebook._segmented_button.pack_forget()
            except Exception:
                pass

    # Dashboard
    def _build_dashboard_tab(self) -> None:
        cards_frame = ctk.CTkFrame(self.dashboard_tab, fg_color=PALETTE["bg"])
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
            (self.burnout_var, "Burnout Risk (>60 ชม.)"),
        ]:
            DashboardCard(cards_frame, title, var).pack(side="left", padx=6, fill="x", expand=True)

        controls = ctk.CTkFrame(self.dashboard_tab, fg_color=PALETTE["panel"])
        controls.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(controls, text="Year:", text_color=PALETTE["text"]).pack(side="left", padx=(12, 4))
        ctk.CTkComboBox(
            controls,
            variable=self.year_var,
            values=["", "2024", "2025"],
            width=90,
        ).pack(side="left", padx=4)
        ctk.CTkLabel(controls, text="Month:", text_color=PALETTE["text"]).pack(side="left", padx=(12, 4))
        ctk.CTkComboBox(
            controls,
            variable=self.month_var,
            values=[""] + [f"{m:02d}" for m in range(1, 13)],
            width=80,
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            controls,
            text="Apply",
            command=self._refresh_dashboard,
            fg_color=PALETTE["accent3"],
            hover_color=PALETTE["accent3_hover"],
        ).pack(
            side="left", padx=6
        )

        self.fig = Figure(figsize=(7, 3), facecolor=PALETTE["chart_face"])
        self.ax_bar = self.fig.add_subplot(211, facecolor=PALETTE["chart_face"])
        self.ax_line = self.fig.add_subplot(212, facecolor=PALETTE["chart_face"])
        self.canvas_fig = FigureCanvasTkAgg(self.fig, master=self.dashboard_tab)
        self.canvas_fig.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=6)

        ctk.CTkButton(
            self.dashboard_tab,
            text="Refresh dashboard",
            command=self._refresh_dashboard,
            fg_color=PALETTE["accent4"],
            hover_color=PALETTE["accent4_hover"],
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
            logger.error("Error fetching employees: %s", exc)

        period = (self.ot_period_var.get() or "month").lower()
        year_filter = int(self.year_var.get()) if self.year_var.get() else None
        month_filter = int(self.month_var.get()) if self.month_var.get() else None
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
            logger.error("Error summarizing OT (%s): %s", period, exc)

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
            logger.error("Error summarizing revenue (%s): %s", period, exc)

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
            logger.error("Error summarizing revenue trend (%s): %s", period, exc)

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
            logger.error("Error counting burnout view %s: %s", self.burnout_view, exc)

        try:
            dept_summary = summarize_ot_by_department(
                self.db,
                limit=20,
                year=year_filter,
                month=month_filter,
            )
        except Exception as exc:  # noqa: BLE001
            dept_summary = []
            logger.error("Error summarizing OT by department: %s", exc)

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
            logger.error("Error summarizing revenue by department: %s", exc)

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
                # Keep current selection if still valid
                if self.department_var.get() not in names:
                    self.department_var.set("All")
        except Exception as exc:  # noqa: BLE001
            logger.error("Error loading departments: %s", exc)

    def _render_ot_charts(self, revenue_trend, dept_summary, revenue_dept, period: str) -> None:
        self.ax_bar.clear()
        self.ax_line.clear()
        self.ax_bar.set_facecolor(PALETTE["chart_face"])
        self.ax_line.set_facecolor(PALETTE["chart_face"])

        # Bar: OT by department
        if dept_summary:
            dept_labels = [str(row.get("department")) for row in dept_summary]
            dept_hours = [float(row.get("ot_hours") or 0) for row in dept_summary]
            self.ax_bar.bar(dept_labels, dept_hours, color=PALETTE["accent"])
            self.ax_bar.tick_params(axis="x", rotation=45, colors=PALETTE["text"])
            self.ax_bar.tick_params(axis="y", colors=PALETTE["text"])
            self.ax_bar.set_facecolor(PALETTE["chart_face"])
            self.ax_bar.spines["bottom"].set_color(PALETTE["border"])
            self.ax_bar.spines["left"].set_color(PALETTE["border"])
            self.ax_bar.set_title("OT by department (filtered)", color=PALETTE["text"])
        else:
            self.ax_bar.set_title("No OT by department data", color=PALETTE["text"])

        # Bar: Revenue by department
        if revenue_dept:
            rev_labels = [str(row.get("department")) for row in revenue_dept]
            rev_vals = [float(row.get("total_pay") or 0) for row in revenue_dept]
            self.ax_line.bar(rev_labels, rev_vals, color=PALETTE["accent"])
            self.ax_line.tick_params(axis="x", rotation=45, colors=PALETTE["text"])
            self.ax_line.tick_params(axis="y", colors=PALETTE["text"])
            self.ax_line.set_facecolor(PALETTE["chart_face"])
            self.ax_line.spines["bottom"].set_color(PALETTE["border"])
            self.ax_line.spines["left"].set_color(PALETTE["border"])
            self.ax_line.set_title("Revenue by department (filtered)", color=PALETTE["text"])
        else:
            self.ax_line.set_title("Revenue by department (no data)", color=PALETTE["text"])

        self.fig.tight_layout()
        self.canvas_fig.draw_idle()

    # Employees tab
    def _build_employee_tab(self) -> None:
        form = ctk.CTkFrame(self.emp_tab, fg_color=PALETTE["panel"])
        form.pack(fill="x", padx=10, pady=10)

        self.emp_fields = {k: tk.StringVar() for k in ["emp_id", "department", "position", "base_salary", "start_date", "dept_id"]}
        labels = [
            ("Employee ID", "emp_id"),
            ("Department", "department"),
            ("Position", "position"),
            ("Base salary", "base_salary"),
            ("Start date (YYYY-MM-DD)", "start_date"),
            ("Dept ID", "dept_id"),
        ]
        for idx, (text, key) in enumerate(labels):
            ctk.CTkLabel(form, text=text, text_color=PALETTE["text"]).grid(row=idx, column=0, sticky="w", pady=4, padx=4)
            ctk.CTkEntry(form, textvariable=self.emp_fields[key], width=260).grid(row=idx, column=1, sticky="w", pady=4)

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=len(labels), column=0, columnspan=2, pady=8, sticky="w")
        ctk.CTkButton(
            btns, text="Add", command=self._add_employee, fg_color=PALETTE["accent"], hover_color=PALETTE["accent_hover"]
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btns, text="Update", command=self._update_employee, fg_color=PALETTE["accent2"], hover_color=PALETTE["accent2_hover"]
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btns,
            text="Delete",
            command=self._delete_employee,
            fg_color=PALETTE["danger"],
            hover_color=PALETTE["accent_hover"],
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btns,
            text="Refresh",
            command=self._refresh_employees,
            fg_color=PALETTE["accent3"],
            hover_color=PALETTE["accent3_hover"],
            text_color=PALETTE["text"],
        ).pack(side="left", padx=4)

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
            logger.info("GUI add employee %s", emp_id)
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
                logger.info("GUI update employee %s", emp_id)
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
                logger.info("GUI delete employee %s", emp_id)
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

    # Time records tab
    def _build_time_tab(self) -> None:
        form = ctk.CTkFrame(self.time_tab, fg_color=PALETTE["panel"])
        form.pack(fill="x", padx=10, pady=10)
        keys = ["emp_id", "work_date", "shift_code", "clock_in", "clock_out", "job_type", "department", "bf_ot", "af_ot", "bt_ot"]
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
            ctk.CTkLabel(form, text=text, text_color=PALETTE["text"]).grid(row=idx, column=0, sticky="w", pady=3, padx=4)
            ctk.CTkEntry(form, textvariable=self.time_fields[key], width=260).grid(row=idx, column=1, sticky="w", pady=3)

        btns = ctk.CTkFrame(form, fg_color="transparent")
        btns.grid(row=len(labels), column=0, columnspan=2, pady=8, sticky="w")
        ctk.CTkButton(
            btns,
            text="Add record",
            command=self._add_time_record,
            fg_color=PALETTE["accent2"],
            hover_color=PALETTE["accent2_hover"],
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btns,
            text="Delete record",
            command=self._delete_time_record,
            fg_color=PALETTE["danger"],
            hover_color=PALETTE["accent_hover"],
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btns,
            text="Refresh",
            command=self._refresh_time_records,
            fg_color=PALETTE["accent4"],
            hover_color=PALETTE["accent4_hover"],
            text_color=PALETTE["text"],
        ).pack(side="left", padx=4)

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
            logger.info("GUI add time record emp_id=%s date=%s", data["emp_id"], data["work_date"])
            self._refresh_time_records()
            messagebox.showinfo("Success", "Time record added.")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))

    def _delete_time_record(self) -> None:
        if not self._require_auth("delete time records"):
            return
        # Prefer selection from table
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
                logger.info("GUI delete time record emp_id=%s date=%s", emp_id, work_date)
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

    # Analytics tab
    def _build_analytics_tab(self) -> None:
        frame = ctk.CTkFrame(self.analytics_tab, fg_color=PALETTE["panel"])
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
        self.ot_daily_btn = ctk.CTkButton(
            frame,
            text="Load OT daily",
            command=self._show_ot_avg_trend,
            fg_color=PALETTE["accent3"],
            hover_color=PALETTE["accent3_hover"],
        )
        self.ot_daily_btn.grid(row=0, column=6, padx=(12, 4))
        self._refresh_ot_trend_view()

        plot_frame = ctk.CTkFrame(self.analytics_tab, fg_color=PALETTE["card_alt"])
        plot_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.analytics_fig = Figure(figsize=(6, 3), facecolor=PALETTE["chart_face"])
        self.analytics_ax = self.analytics_fig.add_subplot(111, facecolor=PALETTE["chart_face"])
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
        try:
            rows = self._fetch_ot_trend_rows()
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
            # Disable the button to avoid repeated failures
            self.ot_daily_btn.configure(state="disabled", text="Load OT daily (view missing)")
            return
        rows = self._filter_rows_by_period(rows)
        self._render_insight_chart(
            rows,
            metrics=["ot_daily", "total_ot_hours", "total_ot_pay"],
            title="Daily OT by department",
            top_n=None,
        )

    def _fetch_ot_trend_rows(self) -> list[dict]:
        """
        Fetch OT trend rows from a preferred view when available; otherwise fall back to a safe grouped query.
        """
        # Try view first if it exists
        view = self.ot_trend_view
        if view:
            try:
                return fetch_view_rows(self.db, view, limit=500)
            except Exception as exc:  # noqa: BLE001
                logger.warning("OT trend view '%s' failed, falling back to direct query: %s", view, exc)

        # Fallback: direct grouped query that is compatible with ONLY_FULL_GROUP_BY
        query = """
            SELECT
                COALESCE(tr.department, 'Unknown') AS department,
                DATE(tr.work_date) AS work_date,
                SUM(
                    COALESCE(
                        CASE
                            WHEN tr.bf_ot IS NULL OR tr.bf_ot = '' THEN 0
                            WHEN tr.bf_ot LIKE '%:%' THEN TIME_TO_SEC(tr.bf_ot) / 3600
                            ELSE CAST(tr.bf_ot AS DECIMAL(10,2))
                        END, 0
                    ) +
                    COALESCE(
                        CASE
                            WHEN tr.af_ot IS NULL OR tr.af_ot = '' THEN 0
                            WHEN tr.af_ot LIKE '%:%' THEN TIME_TO_SEC(tr.af_ot) / 3600
                            ELSE CAST(tr.af_ot AS DECIMAL(10,2))
                        END, 0
                    ) +
                    COALESCE(
                        CASE
                            WHEN tr.bt_ot IS NULL OR tr.bt_ot = '' THEN 0
                            WHEN tr.bt_ot LIKE '%:%' THEN TIME_TO_SEC(tr.bt_ot) / 3600
                            ELSE CAST(tr.bt_ot AS DECIMAL(10,2))
                        END, 0
                    )
                ) AS ot_daily,
                SUM(
                    COALESCE(
                        CASE
                            WHEN tr.bf_ot IS NULL OR tr.bf_ot = '' THEN 0
                            WHEN tr.bf_ot LIKE '%:%' THEN TIME_TO_SEC(tr.bf_ot) / 3600
                            ELSE CAST(tr.bf_ot AS DECIMAL(10,2))
                        END, 0
                    ) +
                    COALESCE(
                        CASE
                            WHEN tr.af_ot IS NULL OR tr.af_ot = '' THEN 0
                            WHEN tr.af_ot LIKE '%:%' THEN TIME_TO_SEC(tr.af_ot) / 3600
                            ELSE CAST(tr.af_ot AS DECIMAL(10,2))
                        END, 0
                    ) +
                    COALESCE(
                        CASE
                            WHEN tr.bt_ot IS NULL OR tr.bt_ot = '' THEN 0
                            WHEN tr.bt_ot LIKE '%:%' THEN TIME_TO_SEC(tr.bt_ot) / 3600
                            ELSE CAST(tr.bt_ot AS DECIMAL(10,2))
                        END, 0
                    )
                ) AS total_ot_hours,
                SUM(
                    COALESCE(
                        CASE
                            WHEN tr.bf_ot IS NULL OR tr.bf_ot = '' THEN 0
                            WHEN tr.bf_ot LIKE '%:%' THEN TIME_TO_SEC(tr.bf_ot) / 3600
                            ELSE CAST(tr.bf_ot AS DECIMAL(10,2))
                        END, 0
                    ) +
                    COALESCE(
                        CASE
                            WHEN tr.af_ot IS NULL OR tr.af_ot = '' THEN 0
                            WHEN tr.af_ot LIKE '%:%' THEN TIME_TO_SEC(tr.af_ot) / 3600
                            ELSE CAST(tr.af_ot AS DECIMAL(10,2))
                        END, 0
                    ) +
                    COALESCE(
                        CASE
                            WHEN tr.bt_ot IS NULL OR tr.bt_ot = '' THEN 0
                            WHEN tr.bt_ot LIKE '%:%' THEN TIME_TO_SEC(tr.bt_ot) / 3600
                            ELSE CAST(tr.bt_ot AS DECIMAL(10,2))
                        END, 0
                    )
                ) * 60 AS total_ot_pay
            FROM time_records tr
            GROUP BY department, DATE(tr.work_date)
            ORDER BY work_date DESC
            LIMIT 500
        """
        with self.db.connect() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(query)
            return list(cur.fetchall())

    def _refresh_ot_trend_view(self) -> None:
        """Pick an available view for OT trend, preferring v_ot_trend then v_weekly_hours_summary."""
        try:
            views = set(list_database_views(self.db))
        except Exception as exc:  # noqa: BLE001
            logger.error("Error listing database views: %s", exc)
            views = set()

        preferred = ["v_ot_trend", "v_weekly_hours_summary"]
        self.ot_trend_view = next((v for v in preferred if v in views), None)

        if self.ot_trend_view:
            self.ot_daily_btn.configure(state="normal", text="Load OT daily")
        else:
            self.ot_daily_btn.configure(state="disabled", text="Load OT daily (view missing)")

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
        self.analytics_ax.set_facecolor(PALETTE["chart_face"])
        if not rows:
            self.analytics_ax.set_title("No data", color=PALETTE["text"])
            self.analytics_canvas.draw_idle()
            return

        # Determine department key and metric to use
        dept_key = None
        for key in ("department_name", "department"):
            if key in rows[0]:
                dept_key = key
                break
        if dept_key is None:
            self.analytics_ax.set_title("No department field", color=PALETTE["text"])
            self.analytics_canvas.draw_idle()
            return

        metric_key = None
        for m in metrics:
            if m in rows[0]:
                metric_key = m
                break
        if metric_key is None:
            self.analytics_ax.set_title("Metric not found", color=PALETTE["text"])
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
            self.analytics_ax.set_title("No data", color=PALETTE["text"])
            self.analytics_canvas.draw_idle()
            return

        sorted_pairs = sorted(agg.items(), key=lambda x: x[1], reverse=True)
        if top_n:
            sorted_pairs = sorted_pairs[:top_n]
        labels, vals = zip(*sorted_pairs)

        self.analytics_ax.bar(labels, vals, color=PALETTE["accent"])
        self.analytics_ax.tick_params(axis="x", rotation=45, colors=PALETTE["text"])
        self.analytics_ax.tick_params(axis="y", colors=PALETTE["text"])
        self.analytics_ax.set_facecolor(PALETTE["chart_face"])
        self.analytics_ax.spines["bottom"].set_color(PALETTE["border"])
        self.analytics_ax.spines["left"].set_color(PALETTE["border"])
        self.analytics_ax.set_title(f"{title} (top {top_n})", color=PALETTE["text"])
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
                # if key not present, skip filtering by year
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
        return filtered or rows  # fallback to all rows if filter removes everything

    # Daily payroll tab
    def _build_daily_payroll_tab(self) -> None:
        wrapper = ctk.CTkFrame(self.daily_payroll_tab, fg_color=PALETTE["bg"])
        wrapper.pack(fill="both", expand=True, padx=10, pady=10)

        controls = ctk.CTkFrame(wrapper, fg_color=PALETTE["panel"])
        controls.pack(fill="x", pady=(0, 6))

        self.daily_emp_var = tk.StringVar(value="")
        ctk.CTkLabel(controls, text="Employee:", text_color=PALETTE["text"]).pack(side="left", padx=(6, 4))
        self.daily_emp_combo = ctk.CTkComboBox(controls, variable=self.daily_emp_var, width=200)
        self.daily_emp_combo.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            controls,
            text="Load",
            command=self._refresh_daily_payroll,
            fg_color=PALETTE["accent4"],
            hover_color=PALETTE["accent4_hover"],
        ).pack(side="left")

        table_frame = ctk.CTkFrame(wrapper, fg_color=PALETTE["card_alt"])
        table_frame.pack(fill="both", expand=True)
        self.daily_tree = tk.ttk.Treeview(table_frame, show="headings", height=18)
        vsb = tk.Scrollbar(table_frame, orient="vertical", command=self.daily_tree.yview)
        hsb = tk.Scrollbar(table_frame, orient="horizontal", command=self.daily_tree.xview)
        self.daily_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.daily_tree.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=6)
        vsb.pack(side="left", fill="y")
        hsb.pack(side="bottom", fill="x")
        _style_treeview(self.daily_tree)

        self._load_daily_emp_options()
        self._refresh_daily_payroll()

    def _load_daily_emp_options(self) -> None:
        try:
            employees = get_all_employees(self.db)
            values = [""] + [emp.get("emp_id") for emp in employees if emp.get("emp_id")]
            self.daily_emp_combo.configure(values=values)
            if values:
                self.daily_emp_combo.set(values[0])
        except Exception as exc:  # noqa: BLE001
            logger.error("Error loading employees for daily payroll: %s", exc)

    def _refresh_daily_payroll(self) -> None:
        emp_id = self.daily_emp_var.get().strip() or None
        rows = []
        try:
            rows = self._fetch_daily_payroll(emp_id)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
            return
        self._render_table_data(self.daily_tree, rows)

    def _fetch_daily_payroll(self, emp_id: str | None) -> list[dict]:
        query = "SELECT * FROM v_daily_payroll"
        params: list = []
        if emp_id:
            query += " WHERE emp_id = %s"
            params.append(emp_id)
        query += " ORDER BY work_date DESC, emp_id LIMIT 200"
        with self.db.connect() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(query, params)
            return list(cur.fetchall())

    # Monthly payroll tab
    def _build_monthly_payroll_tab(self) -> None:
        wrapper = ctk.CTkFrame(self.monthly_payroll_tab, fg_color=PALETTE["bg"])
        wrapper.pack(fill="both", expand=True, padx=10, pady=10)

        controls = ctk.CTkFrame(wrapper, fg_color=PALETTE["panel"])
        controls.pack(fill="x", pady=(0, 6))

        self.monthly_emp_var = tk.StringVar(value="")
        ctk.CTkLabel(controls, text="Employee:", text_color=PALETTE["text"]).pack(side="left", padx=(6, 4))
        self.monthly_emp_combo = ctk.CTkComboBox(controls, variable=self.monthly_emp_var, width=200)
        self.monthly_emp_combo.pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            controls,
            text="Load",
            command=self._refresh_monthly_payroll,
            fg_color=PALETTE["accent2"],
            hover_color=PALETTE["accent2_hover"],
        ).pack(side="left")

        table_frame = ctk.CTkFrame(wrapper, fg_color=PALETTE["card_alt"])
        table_frame.pack(fill="both", expand=True)
        self.monthly_tree = tk.ttk.Treeview(table_frame, show="headings", height=18)
        vsb = tk.Scrollbar(table_frame, orient="vertical", command=self.monthly_tree.yview)
        hsb = tk.Scrollbar(table_frame, orient="horizontal", command=self.monthly_tree.xview)
        self.monthly_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.monthly_tree.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=6)
        vsb.pack(side="left", fill="y")
        hsb.pack(side="bottom", fill="x")
        _style_treeview(self.monthly_tree)

        self._load_monthly_emp_options()
        self._refresh_monthly_payroll()

    def _load_monthly_emp_options(self) -> None:
        try:
            employees = get_all_employees(self.db)
            values = [""] + [emp.get("emp_id") for emp in employees if emp.get("emp_id")]
            self.monthly_emp_combo.configure(values=values)
            if values:
                self.monthly_emp_combo.set(values[0])
        except Exception as exc:  # noqa: BLE001
            logger.error("Error loading employees for monthly payroll: %s", exc)

    def _refresh_monthly_payroll(self) -> None:
        emp_id = self.monthly_emp_var.get().strip() or None
        rows = []
        try:
            rows = self._fetch_monthly_payroll(emp_id)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
            return
        self._render_table_data(self.monthly_tree, rows)

    def _fetch_monthly_payroll(self, emp_id: str | None) -> list[dict]:
        query = "SELECT * FROM payroll"
        params: list = []
        if emp_id:
            query += " WHERE emp_id = %s"
            params.append(emp_id)
        query += " ORDER BY month DESC, emp_id LIMIT 200"
        with self.db.connect() as conn, conn.cursor(dictionary=True) as cur:
            cur.execute(query, params)
            return list(cur.fetchall())

    def _render_table_data(self, tree: tk.ttk.Treeview, rows: list[dict]) -> None:
        for col in tree["columns"]:
            tree.heading(col, text="")
            tree.column(col, width=120)
        tree.delete(*tree.get_children())
        if not rows:
            tree["columns"] = ["message"]
            tree.heading("message", text="No data found")
            tree.column("message", width=200, anchor="w")
            return
        cols = list(rows[0].keys())
        tree["columns"] = cols
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=140, anchor="w")
        for row in rows:
            tree.insert("", "end", values=[row.get(col) for col in cols])

    def _export_logs(self) -> None:
        """Export the current log file as a text file."""
        if not LOG_PATH.exists():
            messagebox.showwarning("No log file", f"Log file not found at {LOG_PATH}")
            return
        default_name = LOG_PATH.with_suffix(".txt").name
        dest = filedialog.asksaveasfilename(
            title="Export logs",
            initialfile=default_name,
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not dest:
            return
        try:
            shutil.copyfile(LOG_PATH, dest)
            messagebox.showinfo("Exported", f"Logs saved to:\n{dest}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", f"Could not export logs:\n{exc}")

    # OT Alerts tab (burnout view)
    def _build_ot_alerts_tab(self) -> None:
        wrapper = ctk.CTkFrame(self.ot_alerts_tab, fg_color=PALETTE["bg"])
        wrapper.pack(fill="both", expand=True, padx=10, pady=10)

        controls = ctk.CTkFrame(wrapper, fg_color=PALETTE["panel"])
        controls.pack(fill="x", pady=(0, 6))
        ctk.CTkLabel(
            controls,
            text="OT Alerts",
            text_color=PALETTE["text"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side="left", padx=(6, 8))
        ctk.CTkButton(
            controls,
            text="Refresh",
            command=self._refresh_ot_alerts,
            fg_color=PALETTE["accent3"],
            hover_color=PALETTE["accent3_hover"],
        ).pack(side="left")

        self.ot_sections_frame = ctk.CTkFrame(wrapper, fg_color=PALETTE["bg"])
        self.ot_sections_frame.pack(fill="both", expand=True)

        self._refresh_ot_alerts()

    def _refresh_ot_alerts(self) -> None:
        view_name = self.burnout_view or "v_burnout_ranking"
        rows: list[dict] = []
        try:
            rows = fetch_view_rows(self.db, view_name, limit=200)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", f"Unable to load view '{view_name}': {exc}")
            return

        # Split rows into buckets similar to the pastel UI: 49-59 and 60+ hours.
        low_rows = [r for r in rows if self._ot_hours(r) is not None and 49 <= self._ot_hours(r) < 60]
        high_rows = [r for r in rows if self._ot_hours(r) is not None and self._ot_hours(r) >= 60]

        # Clear previous content
        for child in self.ot_sections_frame.winfo_children():
            child.destroy()

        self._render_ot_section(
            parent=self.ot_sections_frame,
            title="คนที่ทำ OT อยู่ในช่วง 49 - 59 ชั่วโมง",
            rows=low_rows,
        )
        self._render_ot_section(
            parent=self.ot_sections_frame,
            title="คนที่ทำ OT มากกว่าหรือเท่ากับ 60 ชั่วโมง",
            rows=high_rows,
        )

    def _render_ot_section(self, parent: ctk.CTkFrame, title: str, rows: list[dict]) -> None:
        card = ctk.CTkFrame(
            parent,
            fg_color=PALETTE["card"],
            corner_radius=12,
            border_width=1,
            border_color=PALETTE["border"],
        )
        card.pack(fill="both", expand=True, padx=4, pady=6)

        header = ctk.CTkFrame(card, fg_color=PALETTE["card"])
        header.pack(fill="x", padx=10, pady=(10, 4))
        ctk.CTkLabel(header, text=title, text_color=PALETTE["text"], font=("Segoe UI", 14, "bold")).pack(side="left")
        ctk.CTkLabel(
            header,
            text=f"{len(rows):,} คน",
            text_color=PALETTE["muted"],
            font=("Segoe UI", 12, "bold"),
        ).pack(side="right")

        table_frame = ctk.CTkFrame(card, fg_color=PALETTE["card_alt"], corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        tree = tk.ttk.Treeview(table_frame, show="headings", height=10)
        vsb = tk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        hsb = tk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        tree.pack(side="left", fill="both", expand=True, padx=(0, 4), pady=6)
        vsb.pack(side="left", fill="y")
        hsb.pack(side="bottom", fill="x")
        _style_treeview(tree)

        self._render_table_data(tree, rows)

    def _ot_hours(self, row: dict) -> float | None:
        try:
            return float(row.get("total_ot_hours"))
        except Exception:
            return None

    # Views tab
    def _build_view_tab(self) -> None:
        wrapper = ctk.CTkFrame(self.view_tab, fg_color=PALETTE["bg"])
        wrapper.pack(fill="both", expand=True, padx=10, pady=10)

        view_frame = ctk.CTkFrame(wrapper, fg_color=PALETTE["panel"])
        view_frame.pack(fill="x", pady=4)
        ctk.CTkLabel(view_frame, text="View:", text_color=PALETTE["text"]).pack(side="left", padx=4)
        self.view_var = tk.StringVar()
        self.view_combo = ctk.CTkComboBox(view_frame, variable=self.view_var, width=240)
        self.view_combo.pack(side="left", padx=4)
        ctk.CTkButton(
            view_frame,
            text="Refresh",
            command=self._refresh_views,
            fg_color=PALETTE["accent4"],
            hover_color=PALETTE["accent4_hover"],
            text_color=PALETTE["text"],
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            view_frame,
            text="Fetch",
            command=self._fetch_view,
            fg_color=PALETTE["accent2"],
            hover_color=PALETTE["accent2_hover"],
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            view_frame,
            text="Export as text",
            command=self._export_view_as_text,
            fg_color=PALETTE["accent"],
            hover_color=PALETTE["accent_hover"],
        ).pack(
            side="left", padx=4
        )

        table_wrapper = ctk.CTkFrame(wrapper, fg_color=PALETTE["card_alt"])
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
            self.current_view_rows = rows
            self.current_view_name = view
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", str(exc))
            return
        self._render_table(rows)
        # Refresh trend view resolution in case views list changed
        self._refresh_ot_trend_view()

    def _export_view_as_text(self) -> None:
        """Export the last fetched view rows to a formatted text file."""
        if not self.current_view_rows:
            messagebox.showwarning("No data", "Please fetch a view first.")
            return
        view_name = self.current_view_name or "view_export"
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"{view_name}_{ts}.txt"
        dest = filedialog.asksaveasfilename(
            title="Export view as text",
            defaultextension=".txt",
            initialfile=default_name,
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not dest:
            return
        try:
            content = self._format_view_text(self.current_view_rows, view_name)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            messagebox.showinfo("Exported", f"Saved to:\n{dest}")
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Error", f"Could not export:\n{exc}")

    def _format_view_text(self, rows: list[dict], view_name: str) -> str:
        if not rows:
            return "No rows to export."
        cols = list(rows[0].keys())
        col_widths = {
            col: max(len(col), *(len(str(r.get(col, ""))) for r in rows))
            for col in cols
        }
        def _fmt_row(row: dict) -> str:
            return " | ".join(str(row.get(col, "")).ljust(col_widths[col]) for col in cols)

        header = "=" * 46
        lines = [
            header,
            "           WORKFORCE ANALYTICS REPORT         ",
            header,
            f"Export Time : {datetime.now():%Y-%m-%d %H:%M:%S}",
            f"Source View : {view_name}",
            f"Rows Count  : {len(rows)}",
            header,
            "",
            " | ".join(col.ljust(col_widths[col]) for col in cols),
            "-" * sum(col_widths.values()) + "-" * (3 * (len(cols) - 1)),
        ]
        lines.extend(_fmt_row(r) for r in rows)
        lines.append("")
        lines.append(header)
        lines.append("                  END REPORT                  ")
        lines.append(header)
        return "\n".join(lines)

    def _render_table(self, rows) -> None:
        # Clear existing
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


def main() -> None:
    config = DatabaseConfig.from_env()
    db = Database(config)
    root = ctk.CTk()
    WorkforceGUI(root, db)
    root.mainloop()


if __name__ == "__main__":
    main()
