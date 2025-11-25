# -------------------------------------------------------------
# workforce_app_v3.py — Professional UX Edition (Dark + Neon)
# -------------------------------------------------------------
import tkinter as tk
from tkinter import ttk, filedialog
import pandas as pd
import mysql.connector
import matplotlib
matplotlib.use("Agg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# ------------------------------
# GLOBAL SETTINGS
# ------------------------------
DB = dict(
    host="localhost",
    user="root",
    password="1234",
    database="workforceV2"
)

THEME_BG = "#000000"
THEME_CARD = "#0d0d0d"
THEME_ACCENT = "#00A8FF"
THEME_TABLE_BG = "#111111"
THEME_TABLE_FG = "#FFFFFF"


# ------------------------------
# DATABASE QUERY WRAPPER
# ------------------------------
def db(sql, params=None):
    conn = mysql.connector.connect(**DB)
    df = pd.read_sql(sql, conn, params=params)
    conn.close()
    return df


# ------------------------------
# MAIN APPLICATION CLASS
# ------------------------------
class WorkforceApp:
    def __init__(self, root):
        self.root = root
        root.title("Workforce Analytics V3 — Black Professional Edition")
        root.geometry("1600x950")
        root.config(bg=THEME_BG)

        self.create_sidebar()

        # Main container
        self.main = tk.Frame(root, bg=THEME_BG)
        self.main.pack(side="right", fill="both", expand=True)

        # Frame: Filter + Content
        self.filter_frame = tk.Frame(self.main, bg=THEME_BG)
        self.filter_frame.pack(fill="x")

        self.content_frame = tk.Frame(self.main, bg=THEME_BG)
        self.content_frame.pack(fill="both", expand=True)

        self.show_dashboard()


    # --------------------------
    # SIDEBAR MENU
    # --------------------------
    def create_sidebar(self):
        side = tk.Frame(self.root, bg=THEME_BG, width=200)
        side.pack(side="left", fill="y", padx=5)

        title = tk.Label(
            side, text="WORKFORCE",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 18, "bold")
        )
        title.pack(pady=20)

    # -------------------------
    # ปุ่มแบบกลมมน + Hover
    # -------------------------
        def btn(name, cmd):
            b = tk.Label(
                side, text=name,
                fg="white", bg="#110A65",
                font=("Roboto", 12, "bold"),
                padx=18, pady=10,
                cursor="hand2",
                bd=0,
                width=16,   # ปรับให้ไม่เต็ม ดูหรู
                anchor="w"
            )

        # Hover effect
            def on_enter(e):
                b.config(bg="#2D2D2D")

            def on_leave(e):
                b.config(bg="#110A65")

        # Click event
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

    # ปุ่ม Export (แยกดีไซน์)
        export_btn = tk.Label(
            side, text="Export CSV",
            fg="white", bg="#333333",
            font=("Roboto", 12, "bold"),
            padx=18, pady=10,
            cursor="hand2",
            width=16, anchor="w"
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

    def card(self, parent, title, value):
        box = tk.Frame(parent, bg=THEME_CARD, bd=1)
        box.pack(side="left", padx=20, pady=10, ipadx=35, ipady=25)

        tk.Label(
            box, text=title, fg=THEME_ACCENT,
            bg=THEME_CARD, font=("Roboto", 14, "bold")
        ).pack()

        tk.Label(
            box, text=value, fg="white",
            bg=THEME_CARD, font=("Roboto", 16)
        ).pack()

    def build_table(self, parent, df):
        style = ttk.Style()
        style.configure("Treeview", background=THEME_TABLE_BG,
                        foreground=THEME_TABLE_FG, rowheight=28,
                        fieldbackground=THEME_TABLE_BG)
        style.configure("Treeview.Heading",
                        background=THEME_ACCENT,
                        foreground="white",
                        font=("Roboto", 12, "bold"))

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
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 22, "bold")
        ).pack(pady=10)

        # -------------------------
        # KPI ROW
        # -------------------------
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

        # -------------------------
        # TOP 10 OT
        # -------------------------
        tk.Label(
            self.content_frame, text="Top 10 OT Employees",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 16, "bold")
        ).pack(pady=10)

        df_top = db("""
            SELECT emp_id, SUM(ot_hours) total_ot
            FROM daily_summary
            GROUP BY emp_id
            ORDER BY total_ot DESC
            LIMIT 10
        """)

        self.build_table(self.content_frame, df_top)

        # -------------------------
        # MONTHLY CHART
        # -------------------------
        df_chart = db("""
            SELECT month, SUM(total_hours) hrs
            FROM monthly_summary
            GROUP BY month
            ORDER BY month
        """)

        fig = plt.Figure(figsize=(6,3), facecolor=THEME_BG)
        ax = fig.add_subplot(111)
        if len(df_chart) > 0:
            ax.plot(df_chart["month"], df_chart["hrs"],
                    color=THEME_ACCENT, linewidth=3)

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
            self.filter_frame, text="Select Department:",
            fg="white", bg=THEME_BG, font=("Roboto", 14)
        ).pack(side="left", padx=10)

        deps = db("SELECT DISTINCT department FROM employees")["department"].tolist()
        combo = ttk.Combobox(self.filter_frame, values=deps, width=20)
        combo.pack(side="left")

        tk.Button(
            self.filter_frame, text="Load",
            fg="white", bg=THEME_ACCENT,
            command=lambda: self.load_department(combo.get())
        ).pack(side="left", padx=10)


    def load_department(self, dep):
        self.clear_content()

        if dep == "":
            return

        tk.Label(
            self.content_frame,
            text=f"Department: {dep}",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 20, "bold")
        ).pack(pady=10)

        row = tk.Frame(self.content_frame, bg=THEME_BG)
        row.pack()

        df = db("""
            SELECT *
            FROM monthly_summary
            WHERE department=%s
        """, (dep,))

        # cards
        self.card(row, "Employees", df["emp_id"].nunique())
        self.card(row, "Total OT Hours", round(df["total_ot_hours"].sum() or 0, 2))
        self.card(row, "Total Hours", round(df["total_hours"].sum() or 0, 2))

        avg = df["total_hours"].mean()
        self.card(row, "Avg Hours", round(avg, 2) if avg is not None else 0)

        # table
        tk.Label(
            self.content_frame,
            text="Top 10 Department Employees",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 16, "bold")
        ).pack()

        df_top = db("""
            SELECT emp_id, SUM(total_hours) hrs
            FROM monthly_summary
            WHERE department=%s
            GROUP BY emp_id
            ORDER BY hrs DESC
            LIMIT 10
        """, (dep,))

        self.build_table(self.content_frame, df_top)

        # chart
        df_chart = db("""
            SELECT month, SUM(total_hours) hrs
            FROM monthly_summary
            WHERE department=%s
            GROUP BY month
            ORDER BY month
        """, (dep,))

        fig = plt.Figure(figsize=(6,3), facecolor=THEME_BG)
        ax = fig.add_subplot(111)

        if len(df_chart) > 0:
            ax.plot(df_chart["month"], df_chart["hrs"],
                    color=THEME_ACCENT, linewidth=3)

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
            self.content_frame, text="Department Analytics",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 22, "bold")
        ).pack(pady=20)

        df = db("""
            SELECT department, SUM(total_hours) hrs, SUM(total_ot_hours) ot
            FROM monthly_summary
            GROUP BY department
        """)

        self.build_table(self.content_frame, df)


    # ----------------------------------------------------------
    # DAILY PAYROLL
    # ----------------------------------------------------------
    def show_daily(self):
        self.clear_filter()
        self.clear_content()

        tk.Label(
            self.filter_frame, text="Select Employee:",
            fg="white", bg=THEME_BG, font=("Roboto", 14)
        ).pack(side="left", padx=10)

        emps = db("SELECT DISTINCT emp_id FROM employees")["emp_id"].tolist()
        combo = ttk.Combobox(self.filter_frame, values=emps, width=20)
        combo.pack(side="left")

        tk.Button(
            self.filter_frame, text="Load",
            fg="white", bg=THEME_ACCENT,
            command=lambda: self.load_daily(combo.get())
        ).pack(side="left", padx=10)


    def load_daily(self, emp):
        self.clear_content()

        tk.Label(
            self.content_frame, text=f"Daily Payroll — {emp}",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 20, "bold")
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
            self.filter_frame, text="Select Employee:",
            fg="white", bg=THEME_BG, font=("Roboto", 14)
        ).pack(side="left", padx=10)

        emps = db("SELECT DISTINCT emp_id FROM employees")["emp_id"].tolist()
        combo = ttk.Combobox(self.filter_frame, values=emps, width=20)
        combo.pack(side="left")

        tk.Button(
            self.filter_frame, text="Load",
            fg="white", bg=THEME_ACCENT,
            command=lambda: self.load_monthly(combo.get())
        ).pack(side="left", padx=10)


    def load_monthly(self, emp):
        self.clear_content()

        tk.Label(
            self.content_frame, text=f"Monthly Payroll — {emp}",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 20, "bold")
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
            self.content_frame, text="OT Alerts",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 22, "bold")
        ).pack(pady=10)

        # ---------------------------------------------
        # CARDS: Risk Level Count
        # ---------------------------------------------
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

        # ---------------------------------------------
        # TOP 10 OT RISK TABLE
        # ---------------------------------------------
        tk.Label(
            self.content_frame, text="Top 10 OT Risks",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 16, "bold")
        ).pack(pady=10)

        df_ab = db("""
            SELECT * FROM ot_abnormal
            ORDER BY deviation DESC
            LIMIT 10
        """)

        self.build_table(self.content_frame, df_ab)

        # ---------------------------------------------
        # RISK WEEKLY TREND CHART
        # ---------------------------------------------
        df_trend = db("""
            SELECT week_no, AVG(week_hours) hrs
            FROM v_burnout_risk
            GROUP BY week_no
            ORDER BY week_no
        """)

        fig = plt.Figure(figsize=(6,3), facecolor=THEME_BG)
        ax = fig.add_subplot(111)

        if len(df_trend) > 0:
            ax.plot(df_trend["week_no"], df_trend["hrs"],
                    color=THEME_ACCENT, linewidth=3)

        ax.set_facecolor(THEME_BG)
        ax.tick_params(colors="white")
        for e in ["left", "right", "top", "bottom"]:
            ax.spines[e].set_color("white")

        tk.Label(
            self.content_frame, text="Weekly Risk Trend",
            fg=THEME_ACCENT, bg=THEME_BG,
            font=("Roboto", 16, "bold")
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
            filetypes=[("CSV Files", "*.csv")]
        )
        if not path:
            return
        df.to_csv(path, index=False)


# -------------------------------------------------------------
# RUN APPLICATION
# -------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    WorkforceApp(root)
    root.mainloop()

