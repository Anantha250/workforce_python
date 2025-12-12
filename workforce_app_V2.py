# -------------------------------------------------------------
# workforce_app_v3.py — Professional UX Edition (Dark + Neon)
# -------------------------------------------------------------
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import pandas as pd
import mysql.connector
import math
import matplotlib

matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import customtkinter as ctk

DB = dict(
    host="localhost",
    user="root",
    password="Sic300445!",
    database="workforceV2",
)
ADMIN_PASSWORD = "admin123"

THEME_BG = "#000000"
THEME_CARD = "#0d0d0d"
THEME_ACCENT = "#00A8FF"
THEME_TABLE_BG = "#111111"
THEME_TABLE_FG = "#FFFFFF"


# ------------------------------
# DATABASE QUERY WRAPPER (PANDAS)
# สำหรับพวกหน้ารายงาน / dashboard
# ------------------------------
def db(sql, params=None):
    conn = mysql.connector.connect(**DB)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


# ------------------------------
# SIMPLE DB HELPER FOR EXEC/FETCH
# ใช้กับส่วน admin / time-entry
# ------------------------------
class DBConn:
    def __init__(self):
        self.conn = mysql.connector.connect(**DB)
        self.cur = self.conn.cursor(buffered=True)

    def run(self, sql, params=None):
        self.cur.execute(sql, params or ())
        self.conn.commit()

    def fetch(self, sql, params=None):
        self.cur.execute(sql, params or ())
        return self.cur.fetchall()

    def fetch_one(self, sql, params=None):
        self.cur.execute(sql, params or ())
        return self.cur.fetchone()

    def close(self):
        try:
            self.cur.close()
        except Exception:
            pass
        try:
            self.conn.close()
        except Exception:
            pass


# ------------------------------
# MAIN APPLICATION CLASS
# ------------------------------
class WorkforceApp:
    def __init__(self, root):
        self.root = root
        root.title("Workforce Analytics V3 — Black Professional Edition")
        root.geometry("1600x950")
        root.config(bg=THEME_BG)

        # DB helper สำหรับ operation insert/update/delete
        self.db = DBConn()

        # สีสำหรับ CTk
        self.card_color = THEME_CARD
        self.text_color = "white"
        self.accent_color = THEME_ACCENT

        self.create_sidebar()

        # Main container
        self.main = tk.Frame(root, bg=THEME_BG)
        self.main.pack(side="right", fill="both", expand=True)

        # Frame: Filter + Content
        self.filter_frame = tk.Frame(self.main, bg=THEME_BG)
        self.filter_frame.pack(fill="x")

        self.content_frame = tk.Frame(self.main, bg=THEME_BG)
        self.content_frame.pack(fill="both", expand=True)

        # ให้ body ชี้ไปที่ content_frame สำหรับใช้กับ customtkinter
        self.body = self.content_frame

        self.show_dashboard()

    # --------------------------
    # SIDEBAR MENU
    # --------------------------
    def create_sidebar(self):
        side = tk.Frame(self.root, bg=THEME_BG, width=200)
        side.pack(side="left", fill="y", padx=5)

        title = tk.Label(
            side,
            text="WORKFORCE",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 18, "bold"),
        )
        title.pack(pady=20)

        # ปุ่มแบบ label + hover
        def btn(name, cmd):
            b = tk.Label(
                side,
                text=name,
                fg="white",
                bg="#110A65",
                font=("Roboto", 12, "bold"),
                padx=18,
                pady=10,
                cursor="hand2",
                bd=0,
                width=16,
                anchor="w",
            )

            def on_enter(e):
                b.config(bg="#2D2D2D")

            def on_leave(e):
                b.config(bg="#110A65")

            b.bind("<Button-1>", lambda e: cmd())
            b.bind("<Enter>", on_enter)
            b.bind("<Leave>", on_leave)
            return b

        # ปุ่มทั้งหมด
        btn("Dashboard", self.show_dashboard).pack(pady=5, padx=10)
        btn("Department", self.show_department).pack(pady=5, padx=10)
        btn("Department Analytics", self.show_dept_analytics).pack(pady=5, padx=10)
        btn("Daily Payroll", self.show_daily).pack(pady=5, padx=10)
        btn("Monthly Payroll", self.show_monthly).pack(pady=5, padx=10)
        btn("OT Alerts", self.show_ot_alerts).pack(pady=5, padx=10)
        btn("Employee (admin)", self.show_employees_admin).pack(pady=5, padx=10)

        # ปุ่ม Export (แยกดีไซน์)
        export_btn = tk.Label(
            side,
            text="Export CSV",
            fg="white",
            bg="#333333",
            font=("Roboto", 12, "bold"),
            padx=18,
            pady=10,
            cursor="hand2",
            width=16,
            anchor="w",
        )
        export_btn.pack(pady=35, padx=10)

        export_btn.bind("<Button-1>", lambda e: self.export_csv())
        export_btn.bind("<Enter>", lambda e: export_btn.config(bg="#444444"))
        export_btn.bind("<Leave>", lambda e: export_btn.config(bg="#333333"))

    # --------------------------
    # INTERNAL HELPERS
    # --------------------------
    def clear_content(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def clear_filter(self):
        for w in self.filter_frame.winfo_children():
            w.destroy()

    def clear_body(self):
        if self.body is not None:
            for widget in self.body.winfo_children():
                widget.destroy()

    def card(self, parent, title, value):
        box = tk.Frame(parent, bg=THEME_CARD, bd=1)
        box.pack(side="left", padx=20, pady=10, ipadx=35, ipady=25)

        tk.Label(
            box,
            text=title,
            fg=THEME_ACCENT,
            bg=THEME_CARD,
            font=("Roboto", 14, "bold"),
        ).pack()

        tk.Label(
            box,
            text=value,
            fg="white",
            bg=THEME_CARD,
            font=("Roboto", 16),
        ).pack()

    def build_table(self, parent, df):
        style = ttk.Style()
        style.configure(
            "Treeview",
            background=THEME_TABLE_BG,
            foreground=THEME_TABLE_FG,
            rowheight=28,
            fieldbackground=THEME_TABLE_BG,
        )
        style.configure(
            "Treeview.Heading",
            background=THEME_ACCENT,
            foreground="white",
            font=("Roboto", 12, "bold"),
        )

        table = ttk.Treeview(parent, show="headings")
        table.pack(fill="both", expand=True, pady=10)

        table["columns"] = list(df.columns)
        for col in df.columns:
            table.heading(col, text=col)
            table.column(col, width=150)

        for _, row in df.iterrows():
            table.insert("", "end", values=list(row))

        return table

    # ----------------------------------------------------------
    # DASHBOARD OVERVIEW (DATA REAL ONLY)
    # ----------------------------------------------------------
    def show_dashboard(self):
        self.clear_filter()
        self.clear_content()

        tk.Label(
            self.content_frame,
            text="Dashboard (Overview)",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 22, "bold"),
        ).pack(pady=10)

        # KPI ROW
        row = tk.Frame(self.content_frame, bg=THEME_BG)
        row.pack()

        # Total Employees
        emp = db("SELECT COUNT(*) total FROM employees")["total"][0] or 0

        # Total OT Hours
        df_ot = db("SELECT SUM(total_ot_hours) ot FROM monthly_summary")
        ot = df_ot["ot"][0] if df_ot["ot"][0] is not None else 0

        # Avg Monthly Hours
        df_avg = db("SELECT AVG(total_hours) hrs FROM monthly_summary")
        avg = df_avg["hrs"][0] if df_avg["hrs"][0] is not None else 0

        # Burnout Risk
        df_burn = db("SELECT risk FROM v_burnout_risk")
        if len(df_burn) == 0:
            burn = 0
        else:
            high = len(df_burn[df_burn["risk"] == "High"])
            burn = round((high / len(df_burn)) * 100, 2)

        self.card(row, "Total Employees", emp)
        self.card(row, "Total OT Hours", round(ot, 2))
        self.card(row, "Avg Monthly Hours", round(avg, 2))
        self.card(row, "Burnout Risk", f"{burn}%")

        # TOP 10 OT
        tk.Label(
            self.content_frame,
            text="Top 10 OT Employees",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 16, "bold"),
        ).pack(pady=10)

        df_top = db(
            """
            SELECT emp_id, SUM(ot_hours) total_ot
            FROM daily_summary
            GROUP BY emp_id
            ORDER BY total_ot DESC
            LIMIT 10
        """
        )

        self.build_table(self.content_frame, df_top)

        # MONTHLY CHART
        df_chart = db(
            """
            SELECT month, SUM(total_hours) hrs
            FROM monthly_summary
            GROUP BY month
            ORDER BY month
        """
        )

        fig = plt.Figure(figsize=(6, 3), facecolor=THEME_BG)
        ax = fig.add_subplot(111)
        if len(df_chart) > 0:
            ax.plot(df_chart["month"], df_chart["hrs"], color=THEME_ACCENT, linewidth=3)

        ax.set_facecolor(THEME_BG)
        ax.tick_params(colors="white")
        for e in ["left", "right", "top", "bottom"]:
            ax.spines[e].set_color("white")

        canvas = FigureCanvasTkAgg(fig, master=self.content_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    # ----------------------------------------------------------
    # DEPARTMENT VIEW (dropdown stays)
    # ----------------------------------------------------------
    def show_department(self):
        self.clear_filter()
        self.clear_content()

        tk.Label(
            self.filter_frame,
            text="Select Department:",
            fg="white",
            bg=THEME_BG,
            font=("Roboto", 14),
        ).pack(side="left", padx=10)

        deps = db("SELECT DISTINCT department FROM employees")["department"].tolist()
        combo = ttk.Combobox(self.filter_frame, values=deps, width=20)
        combo.pack(side="left")

        tk.Button(
            self.filter_frame,
            text="Load",
            fg="white",
            bg=THEME_ACCENT,
            command=lambda: self.load_department(combo.get()),
        ).pack(side="left", padx=10)

    def load_department(self, dep):
        self.clear_content()

        if dep == "":
            return

        tk.Label(
            self.content_frame,
            text=f"Department: {dep}",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 20, "bold"),
        ).pack(pady=10)

        row = tk.Frame(self.content_frame, bg=THEME_BG)
        row.pack()

        df = db(
            """
            SELECT *
            FROM monthly_summary
            WHERE department=%s
        """,
            (dep,),
        )

        # cards
        self.card(row, "Employees", df["emp_id"].nunique())
        self.card(
            row,
            "Total OT Hours",
            round(df["total_ot_hours"].sum() or 0, 2),
        )
        self.card(row, "Total Hours", round(df["total_hours"].sum() or 0, 2))

        avg = df["total_hours"].mean()
        self.card(row, "Avg Hours", round(avg, 2) if avg is not None else 0)

        # table
        tk.Label(
            self.content_frame,
            text="Top 10 Department Employees",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 16, "bold"),
        ).pack()

        df_top = db(
            """
            SELECT emp_id, SUM(total_hours) hrs
            FROM monthly_summary
            WHERE department=%s
            GROUP BY emp_id
            ORDER BY hrs DESC
            LIMIT 10
        """,
            (dep,),
        )

        self.build_table(self.content_frame, df_top)

        # chart
        df_chart = db(
            """
            SELECT month, SUM(total_hours) hrs
            FROM monthly_summary
            WHERE department=%s
            GROUP BY month
            ORDER BY month
        """,
            (dep,),
        )

        fig = plt.Figure(figsize=(6, 3), facecolor=THEME_BG)
        ax = fig.add_subplot(111)

        if len(df_chart) > 0:
            ax.plot(df_chart["month"], df_chart["hrs"], color=THEME_ACCENT, linewidth=3)

        ax.set_facecolor(THEME_BG)
        ax.tick_params(colors="white")
        canvas = FigureCanvasTkAgg(fig, master=self.content_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    # ----------------------------------------------------------
    # DEPARTMENT ANALYTICS
    # ----------------------------------------------------------
    def show_dept_analytics(self):
        self.clear_filter()
        self.clear_content()

        tk.Label(
            self.content_frame,
            text="Department Analytics",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 22, "bold"),
        ).pack(pady=20)

        df = db(
            """
            SELECT department, SUM(total_hours) hrs, SUM(total_ot_hours) ot
            FROM monthly_summary
            GROUP BY department
        """
        )

        self.build_table(self.content_frame, df)

    # ----------------------------------------------------------
    # DAILY PAYROLL
    # ----------------------------------------------------------
    def show_daily(self):
        self.clear_filter()
        self.clear_content()

        tk.Label(
            self.filter_frame,
            text="Select Employee:",
            fg="white",
            bg=THEME_BG,
            font=("Roboto", 14),
        ).pack(side="left", padx=10)

        emps = db("SELECT DISTINCT emp_id FROM employees")["emp_id"].tolist()
        combo = ttk.Combobox(self.filter_frame, values=emps, width=20)
        combo.pack(side="left")

        tk.Button(
            self.filter_frame,
            text="Load",
            fg="white",
            bg=THEME_ACCENT,
            command=lambda: self.load_daily(combo.get()),
        ).pack(side="left", padx=10)

    def load_daily(self, emp):
        self.clear_content()

        tk.Label(
            self.content_frame,
            text=f"Daily Payroll — {emp}",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 20, "bold"),
        ).pack(pady=10)

        df = db("SELECT * FROM v_daily_payroll WHERE emp_id=%s", (emp,))
        self.build_table(self.content_frame, df)

    # ----------------------------------------------------------
    # MONTHLY PAYROLL
    # ----------------------------------------------------------
    def show_monthly(self):
        self.clear_filter()
        self.clear_content()

        tk.Label(
            self.filter_frame,
            text="Select Employee:",
            fg="white",
            bg=THEME_BG,
            font=("Roboto", 14),
        ).pack(side="left", padx=10)

        emps = db("SELECT DISTINCT emp_id FROM employees")["emp_id"].tolist()
        combo = ttk.Combobox(self.filter_frame, values=emps, width=20)
        combo.pack(side="left")

        tk.Button(
            self.filter_frame,
            text="Load",
            fg="white",
            bg=THEME_ACCENT,
            command=lambda: self.load_monthly(combo.get()),
        ).pack(side="left", padx=10)

    def load_monthly(self, emp):
        self.clear_content()

        tk.Label(
            self.content_frame,
            text=f"Monthly Payroll — {emp}",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 20, "bold"),
        ).pack(pady=10)

        df = db("SELECT * FROM v_monthly_payroll WHERE emp_id=%s", (emp,))
        self.build_table(self.content_frame, df)

    # ----------------------------------------------------------
    # OT ALERTS (with Cards + Weekly Risk Chart + Trend Line)
    # ----------------------------------------------------------
    def show_ot_alerts(self):
        self.clear_filter()
        self.clear_content()

        tk.Label(
            self.content_frame,
            text="OT Alerts",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 22, "bold"),
        ).pack(pady=10)

        # CARDS: Risk Level Count
        df = db("SELECT * FROM v_burnout_risk")

        row = tk.Frame(self.content_frame, bg=THEME_BG)
        row.pack()

        if len(df) == 0:
            high = medium = low = 0
        else:
            high = len(df[df["risk"] == "High"])
            medium = len(df[df["risk"] == "Medium"])
            low = len(df[df["risk"] == "Low"])

        self.card(row, "High Risk", high)
        self.card(row, "Medium Risk", medium)
        self.card(row, "Low Risk", low)

        # TOP 10 OT RISK TABLE
        tk.Label(
            self.content_frame,
            text="Top 10 OT Risks",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 16, "bold"),
        ).pack(pady=10)

        df_ab = db(
            """
            SELECT * FROM ot_abnormal
            ORDER BY deviation DESC
            LIMIT 10
        """
        )

        self.build_table(self.content_frame, df_ab)

        # RISK WEEKLY TREND CHART
        df_trend = db(
            """
            SELECT week_no, AVG(week_hours) hrs
            FROM v_burnout_risk
            GROUP BY week_no
            ORDER BY week_no
        """
        )

        fig = plt.Figure(figsize=(6, 3), facecolor=THEME_BG)
        ax = fig.add_subplot(111)

        if len(df_trend) > 0:
            ax.plot(df_trend["week_no"], df_trend["hrs"], color=THEME_ACCENT, linewidth=3)

        ax.set_facecolor(THEME_BG)
        ax.tick_params(colors="white")
        for e in ["left", "right", "top", "bottom"]:
            ax.spines[e].set_color("white")

        tk.Label(
            self.content_frame,
            text="Weekly Risk Trend",
            fg=THEME_ACCENT,
            bg=THEME_BG,
            font=("Roboto", 16, "bold"),
        ).pack(pady=10)

        canvas = FigureCanvasTkAgg(fig, master=self.content_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(pady=20)

    # ----------------------------------------------------------
    # EXPORT CSV
    # ----------------------------------------------------------
    def export_csv(self):
        df = db("SELECT * FROM employees")
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
        )
        if not path:
            return
        df.to_csv(path, index=False)

    # ----------------------------------------------------------
    # ADMIN AUTH
    # ----------------------------------------------------------
    def check_admin_password(self) -> bool:
        try:
            dialog = ctk.CTkInputDialog(
                title="Admin Authentication",
                text="กรุณากรอกรหัสผ่านผู้ดูแลระบบ:",
            )
            pwd = dialog.get_input()
        except AttributeError:
            messagebox.showerror(
                "Error",
                "เวอร์ชัน customtkinter นี้ไม่รองรับ CTkInputDialog\nกรุณาอัปเกรด customtkinter ก่อน",
            )
            return False

        if pwd is None:
            return False

        if pwd != ADMIN_PASSWORD:
            messagebox.showerror("Access Denied", "รหัสผ่านไม่ถูกต้อง")
            return False

        return True

    # ----------------------------------------------------------
    # EMPLOYEES ADMIN PAGE
    # ----------------------------------------------------------
    def show_employees_admin(self):
        if not self.check_admin_password():
            return

        self.clear_filter()
        self.clear_body()

        container = ctk.CTkFrame(self.body, fg_color=self.card_color, corner_radius=14)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            container,
            text="Manage Employees",
            font=("Helvetica", 18, "bold"),
            text_color=self.text_color,
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        form_frame = ctk.CTkFrame(container, fg_color=self.card_color)
        form_frame.grid(row=1, column=0, sticky="nw", padx=(0, 20), pady=10)

        table_frame = ctk.CTkFrame(container, fg_color=self.card_color)
        table_frame.grid(row=1, column=1, sticky="nsew", pady=10)

        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(1, weight=1)

        form_entries = {}

        def add_form_row(row, label, key, placeholder=""):
            ctk.CTkLabel(form_frame, text=label, text_color=self.text_color).grid(
                row=row,
                column=0,
                sticky="e",
                padx=5,
                pady=4,
            )
            ent = ctk.CTkEntry(form_frame, width=180, placeholder_text=placeholder)
            ent.grid(row=row, column=1, sticky="w", padx=5, pady=4)
            form_entries[key] = ent

        add_form_row(0, "Employee ID", "emp_id")
        add_form_row(1, "Department Name", "department")
        add_form_row(2, "Position", "position")
        add_form_row(3, "Base Salary", "base_salary", "30000.00")
        add_form_row(4, "Start Date", "start_date", "YYYY-MM-DD")
        add_form_row(5, "Dept ID", "dept_id")

        cols = ("emp_id", "department", "position", "base_salary", "start_date", "dept_id")
        tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=15)
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=120, anchor="center")

        yscroll = ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(table_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        def refresh_table():
            for i in tree.get_children():
                tree.delete(i)
            rows = self.db.fetch(
                """
                SELECT emp_id, department, position, base_salary, start_date, dept_id
                FROM employees
                ORDER BY emp_id
                """
            )
            for r in rows:
                tree.insert("", "end", values=r)

        def clear_form():
            for ent in form_entries.values():
                ent.delete(0, "end")

        def add_employee():
            data = {k: v.get().strip() for k, v in form_entries.items()}

            if not data["emp_id"]:
                messagebox.showwarning("Missing Data", "กรุณากรอก Employee ID")
                return

            base_salary = None
            if data["base_salary"]:
                try:
                    base_salary = float(data["base_salary"])
                except ValueError:
                    messagebox.showwarning("Invalid Salary", "Base Salary ต้องเป็นตัวเลข")
                    return

            if data["start_date"]:
                try:
                    datetime.strptime(data["start_date"], "%Y-%m-%d")
                except ValueError:
                    messagebox.showwarning(
                        "Invalid Date",
                        "Start Date ต้องเป็นรูปแบบ YYYY-MM-DD",
                    )
                    return

            if data["dept_id"]:
                ok = self.db.fetch_one(
                    "SELECT 1 FROM department WHERE dept_id=%s",
                    (data["dept_id"],),
                )
                if not ok:
                    messagebox.showwarning(
                        "Invalid Dept",
                        f"ไม่พบ Dept ID '{data['dept_id']}' ในตาราง department",
                    )
                    return

            try:
                self.db.run(
                    """
                    INSERT INTO employees
                        (emp_id, department, position, base_salary, start_date, dept_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        data["emp_id"],
                        data["department"] or None,
                        data["position"] or None,
                        base_salary,
                        data["start_date"] or None,
                        data["dept_id"] or None,
                    ),
                )
            except Exception as exc:
                messagebox.showerror("Database Error", f"ไม่สามารถเพิ่มพนักงานได้\n{exc}")
                return

            messagebox.showinfo("Saved", "เพิ่มข้อมูลพนักงานเรียบร้อยแล้ว")
            clear_form()
            refresh_table()

        def delete_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("No Selection", "กรุณาเลือกพนักงานที่ต้องการลบ")
                return

            emp_ids = []
            for item in selected:
                vals = tree.item(item, "values")
                if vals:
                    emp_ids.append(vals[0])

            if not emp_ids:
                return

            if not messagebox.askyesno(
                "Confirm Delete",
                f"ต้องการลบพนักงาน {len(emp_ids)} คนใช่หรือไม่?\n"
                f"(ถ้ามีข้อมูลผูกกับ time_records อาจลบไม่ได้)",
            ):
                return

            for emp_id in emp_ids:
                try:
                    self.db.run("DELETE FROM employees WHERE emp_id=%s", (emp_id,))
                except Exception as exc:
                    messagebox.showerror(
                        "Database Error",
                        f"ไม่สามารถลบ emp_id '{emp_id}' ได้\n{exc}",
                    )
            refresh_table()

        form_btn_frame = ctk.CTkFrame(form_frame, fg_color=self.card_color)
        form_btn_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))

        ctk.CTkButton(
            form_btn_frame,
            text="Add Employee",
            command=add_employee,
            width=120,
            fg_color=self.accent_color,
            hover_color="#ff82b7",
            text_color=self.text_color,
            corner_radius=10,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            form_btn_frame,
            text="Clear Form",
            command=clear_form,
            width=100,
            fg_color=self.card_color,
            hover_color="#e4ddff",
            text_color=self.text_color,
            corner_radius=10,
        ).pack(side="left", padx=5)

        del_btn = ctk.CTkButton(
            table_frame,
            text="Delete Selected",
            command=delete_selected,
            fg_color="#ffd166",
            hover_color="#ffb347",
            text_color=self.text_color,
            corner_radius=10,
        )
        del_btn.grid(row=2, column=0, pady=(8, 0), sticky="w")

        refresh_table()

    # ----------------------------------------------------------
    # TIME ENTRY FORM (CHECK IN / OUT)
    # ----------------------------------------------------------
    def show_time_entry_form(self):
        self.clear_filter()
        self.clear_body()

        wrapper = ctk.CTkFrame(self.body, fg_color=self.card_color, corner_radius=14)
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper,
            text="Time Record – Check In / Check Out",
            font=("Helvetica", 18, "bold"),
            text_color=self.text_color,
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        fields = [
            ("Employee ID", "emp_id"),
            ("Work Date (YYYY-MM-DD)", "work_date"),
            ("Job Type (W/L/H/T)", "job_type"),
            ("Shift Code", "shift_code"),
        ]
        entries = {}
        for idx, (label_text, key) in enumerate(fields, start=1):
            ctk.CTkLabel(wrapper, text=label_text, text_color=self.text_color).grid(
                row=idx,
                column=0,
                pady=6,
                padx=5,
                sticky="e",
            )
            entry = ctk.CTkEntry(wrapper, width=200)
            entry.grid(row=idx, column=1, pady=6, padx=5, sticky="w")
            entries[key] = entry

        from datetime import date

        entries["work_date"].insert(0, date.today().strftime("%Y-%m-%d"))

        ctk.CTkLabel(wrapper, text="Clock In (auto)", text_color=self.text_color).grid(
            row=5,
            column=0,
            pady=6,
            padx=5,
            sticky="e",
        )
        clock_in_entry = ctk.CTkEntry(wrapper, width=200)
        clock_in_entry.grid(row=5, column=1, pady=6, padx=5, sticky="w")
        clock_in_entry.configure(state="readonly")
        entries["clock_in"] = clock_in_entry

        ctk.CTkLabel(wrapper, text="Clock Out (auto)", text_color=self.text_color).grid(
            row=6,
            column=0,
            pady=6,
            padx=5,
            sticky="e",
        )
        clock_out_entry = ctk.CTkEntry(wrapper, width=200)
        clock_out_entry.grid(row=6, column=1, pady=6, padx=5, sticky="w")
        clock_out_entry.configure(state="readonly")
        entries["clock_out"] = clock_out_entry

        def parse_time_str(t):
            from datetime import datetime as dt_cls, date as date_cls, time as time_cls

            if t is None:
                raise ValueError("Time string is None")

            if isinstance(t, dt_cls):
                return t
            if isinstance(t, time_cls):
                return dt_cls.combine(date_cls.today(), t)

            s = str(t).strip()
            if not s:
                raise ValueError("Empty time string")

            if " " in s:
                s = s.split()[-1]

            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return dt_cls.strptime(s, fmt)
                except ValueError:
                    continue
            raise ValueError(f"Unrecognized time format: {s}")

        def calc_hours(diff):
            raw = diff.total_seconds() / 3600.0
            if raw <= 0:
                return 0.0
            return float(math.ceil(raw))

        def get_base_info():
            data = {
                k: v.get().strip()
                for k, v in entries.items()
                if k in ["emp_id", "work_date", "job_type", "shift_code"]
            }
            required_keys = ["emp_id", "work_date", "job_type", "shift_code"]
            if any(not data[k] for k in required_keys):
                messagebox.showwarning(
                    "Missing Data",
                    "กรุณากรอก Employee ID, Work Date, Job Type และ Shift Code ให้ครบ",
                )
                return None
            data["job_type"] = data["job_type"].upper()
            return data

        def handle_check_in():
            base = get_base_info()
            if not base:
                return

            emp_id = base["emp_id"]
            work_date = base["work_date"]
            job_type = base["job_type"]
            shift_code = base["shift_code"]

            exists = self.db.fetch_one(
                "SELECT 1 FROM time_records WHERE emp_id=%s AND work_date=%s",
                (emp_id, work_date),
            )
            if exists:
                messagebox.showwarning(
                    "Already Checked In",
                    f"วันนี้ ( {work_date} ) มี Time Record ของ emp_id {emp_id} อยู่แล้ว",
                )
                return

            shift_row = self.db.fetch_one(
                "SELECT start_time, end_time FROM shift WHERE shift_code = %s",
                (shift_code,),
            )
            if not shift_row:
                messagebox.showwarning(
                    "Invalid Shift", f"ไม่พบ Shift code '{shift_code}' ในระบบ"
                )
                return

            schedule_in_db, schedule_out_db = shift_row

            schedule_in_dt = parse_time_str(str(schedule_in_db))
            schedule_out_dt = parse_time_str(str(schedule_out_db))

            schedule_in_str = schedule_in_dt.strftime("%H:%M:%S")
            schedule_out_str = schedule_out_dt.strftime("%H:%M:%S")

            emp_row = self.db.fetch_one(
                "SELECT department FROM employees WHERE emp_id = %s",
                (emp_id,),
            )
            if not emp_row:
                messagebox.showwarning(
                    "Not Found", f"ไม่พบ emp_id '{emp_id}' ในตาราง employees"
                )
                return
            department = emp_row[0]

            clock_in_str = datetime.now().strftime("%H:%M:%S")

            entries["clock_in"].configure(state="normal")
            entries["clock_in"].delete(0, "end")
            entries["clock_in"].insert(0, clock_in_str)
            entries["clock_in"].configure(state="readonly")

            try:
                self.db.run(
                    """
                    INSERT INTO time_records
                        (emp_id, work_date, job_type, shift_code,
                        `in`, `out`, clock_in, department)
                    VALUES (%s, %s, %s, %s,
                            %s, %s, %s, %s)
                    """,
                    (
                        emp_id,
                        work_date,
                        job_type,
                        shift_code,
                        schedule_in_str,
                        schedule_out_str,
                        clock_in_str,
                        department,
                    ),
                )
            except Exception as exc:
                messagebox.showerror("Database Error", f"ไม่สามารถเช็คอินได้\n{exc}")
                return

            messagebox.showinfo("Checked In", f"เช็คอินสำเร็จเวลา {clock_in_str}")

        def handle_check_out():
            base = get_base_info()
            if not base:
                return

            emp_id = base["emp_id"]
            work_date = base["work_date"]

            row = self.db.fetch_one(
                """
                SELECT job_type, shift_code, `in`, `out`, clock_in
                FROM time_records
                WHERE emp_id=%s AND work_date=%s
                """,
                (emp_id, work_date),
            )
            if not row:
                messagebox.showwarning(
                    "No Check-in Found",
                    f"ยังไม่มีการเช็คอินของ emp_id {emp_id} วันที่ {work_date}",
                )
                return

            job_type, shift_code, schedule_in_db, schedule_out_db, clock_in_str = row

            try:
                schedule_in_dt = parse_time_str(str(schedule_in_db))
                schedule_out_dt = parse_time_str(str(schedule_out_db))
                clock_in_dt = parse_time_str(clock_in_str)
            except Exception:
                messagebox.showwarning(
                    "Invalid Time Data",
                    "ข้อมูลเวลาในระบบไม่ถูกต้อง (in/out/clock_in) ตรวจสอบฐานข้อมูล",
                )
                return

            clock_out_str = datetime.now().strftime("%H:%M:%S")

            entries["clock_out"].configure(state="normal")
            entries["clock_out"].delete(0, "end")
            entries["clock_out"].insert(0, clock_out_str)
            entries["clock_out"].configure(state="readonly")

            try:
                clock_out_dt = parse_time_str(clock_out_str)
            except Exception:
                messagebox.showwarning(
                    "Invalid Time", "ไม่สามารถอ่านเวลา Clock Out ปัจจุบันได้"
                )
                return

            from datetime import timedelta

            if schedule_out_dt <= schedule_in_dt:
                schedule_out_dt += timedelta(days=1)
            if clock_out_dt <= clock_in_dt:
                clock_out_dt += timedelta(days=1)

            bf_ot_hours = 0.0
            af_ot_hours = 0.0
            bt_ot_hours = 0.0

            if job_type == "W":
                if clock_in_dt < schedule_in_dt:
                    bf_ot_hours = calc_hours(schedule_in_dt - clock_in_dt)
                if clock_out_dt > schedule_out_dt:
                    af_ot_hours = calc_hours(clock_out_dt - schedule_out_dt)
            elif job_type in ("H", "L", "T"):
                bt_ot_hours = calc_hours(clock_out_dt - clock_in_dt)

            bf_ot = f"{bf_ot_hours:.2f}" if bf_ot_hours > 0 else "0.00"
            af_ot = f"{af_ot_hours:.2f}" if af_ot_hours > 0 else "0.00"
            bt_ot = f"{bt_ot_hours:.2f}" if bt_ot_hours > 0 else "0.00"

            try:
                self.db.run(
                    """
                    UPDATE time_records
                    SET clock_out=%s,
                        bf_ot=%s,
                        af_ot=%s,
                        bt_ot=%s
                    WHERE emp_id=%s AND work_date=%s
                    """,
                    (
                        clock_out_str,
                        bf_ot,
                        af_ot,
                        bt_ot,
                        emp_id,
                        work_date,
                    ),
                )
            except Exception as exc:
                messagebox.showerror("Database Error", f"ไม่สามารถเช็คเอาท์ได้\n{exc}")
                return

            messagebox.showinfo(
                "Checked Out",
                f"เช็คเอาท์สำเร็จเวลา {clock_out_str}\n"
                f"BF OT: {bf_ot or '0.00'}  AF OT: {af_ot or '0.00'}  BT OT: {bt_ot or '0.00'}",
            )

            def update_payroll_total(emp_id: str, work_date: str, ot_hours: float):
                cols = {row[0] for row in self.db.fetch("SHOW COLUMNS FROM payroll")}
                if "total_salary" not in cols or "emp_id" not in cols:
                    return

                ot_field = "total_ot_hours" if "total_ot_hours" in cols else None

                base_salary_row = self.db.fetch_one(
                    "SELECT base_salary FROM employees WHERE emp_id=%s",
                    (emp_id,),
                )
                base_salary_val = (
                    float(base_salary_row[0])
                    if base_salary_row and base_salary_row[0] is not None
                    else 0.0
                )
                hourly_rate = base_salary_val / 160 if base_salary_val else 0.0
                ot_rate = hourly_rate * 1.5
                ot_pay = ot_hours * ot_rate

                existing_total = 0.0
                existing_ot = 0.0

                if "work_date" in cols:
                    existing = self.db.fetch_one(
                        "SELECT total_salary{ot_col} FROM payroll WHERE emp_id=%s AND work_date=%s".format(
                            ot_col=(", " + ot_field) if ot_field else ""
                        ),
                        (emp_id, work_date),
                    )
                else:
                    existing = self.db.fetch_one(
                        "SELECT total_salary{ot_col} FROM payroll WHERE emp_id=%s".format(
                            ot_col=(", " + ot_field) if ot_field else ""
                        ),
                        (emp_id,),
                    )

                if existing:
                    existing_total = float(existing[0] or 0)
                    if ot_field and len(existing) > 1:
                        existing_ot = float(existing[1] or 0)

                new_total_salary = (
                    (existing_total or base_salary_val) + ot_pay
                    if existing
                    else (base_salary_val + ot_pay)
                )
                new_total_ot = existing_ot + ot_hours if ot_field else None

                if "work_date" in cols:
                    if existing:
                        if ot_field:
                            self.db.run(
                                f"UPDATE payroll SET total_salary=%s, {ot_field}=%s WHERE emp_id=%s AND work_date=%s",
                                (new_total_salary, new_total_ot, emp_id, work_date),
                            )
                        else:
                            self.db.run(
                                "UPDATE payroll SET total_salary=%s WHERE emp_id=%s AND work_date=%s",
                                (new_total_salary, emp_id, work_date),
                            )
                    else:
                        sql = f"INSERT INTO payroll (emp_id, work_date, total_salary{',' + ot_field if ot_field else ''}) VALUES (%s, %s, %s{', %s' if ot_field else ''})"
                        params = [emp_id, work_date, new_total_salary]
                        if ot_field:
                            params.append(new_total_ot)
                        self.db.run(sql, params)
                else:
                    if ot_field:
                        self.db.run(
                            f"UPDATE payroll SET total_salary=%s, {ot_field}=%s WHERE emp_id=%s",
                            (new_total_salary, new_total_ot, emp_id),
                        )
                    else:
                        self.db.run(
                            "UPDATE payroll SET total_salary=%s WHERE emp_id=%s",
                            (new_total_salary, emp_id),
                        )

            update_payroll_total(
                emp_id,
                work_date,
                bf_ot_hours + af_ot_hours + bt_ot_hours,
            )

        btn_frame = ctk.CTkFrame(wrapper, fg_color=self.card_color)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=(12, 0))

        ctk.CTkButton(
            btn_frame,
            text="Check In (INSERT)",
            command=handle_check_in,
            width=140,
            fg_color=self.accent_color,
            hover_color="#ff82b7",
            text_color=self.text_color,
            corner_radius=10,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Check Out (UPDATE)",
            command=handle_check_out,
            width=140,
            fg_color=self.card_color,
            hover_color="#e4ddff",
            text_color=self.text_color,
            corner_radius=10,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            btn_frame,
            text="Back to Time Records",
            command=self.show_time_records,
            width=160,
            fg_color=self.card_color,
            hover_color="#e4ddff",
            text_color=self.text_color,
            corner_radius=10,
        ).pack(side="left", padx=5)

    # ----------------------------------------------------------
    # SIMPLE STUB: SHOW TIME RECORDS
    # (ตอนนี้ให้ย้อนกลับ Dashboard ไปก่อน)
    # ----------------------------------------------------------
    def show_time_records(self):
        self.clear_filter()
        self.clear_content()
        self.show_dashboard()


# -------------------------------------------------------------
# RUN APPLICATION
# -------------------------------------------------------------
if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")

    root = ctk.CTk()
    app = WorkforceApp(root)

    def on_close():
        try:
            app.db.close()
        except Exception:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()
