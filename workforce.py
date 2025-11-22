from datetime import datetime
import mysql.connector
import customtkinter as ctk
from tkinter import messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import math


DB = {
    "host": "localhost",
    "user": "root",
    "password": "Sic300445!",
    "database": "workforce",
}

ADMIN_PASSWORD = "admin123"



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
    
    def fetch_with_columns(self, sql, params=None):
        self.cur.execute(sql, params or ())
        columns = [desc[0] for desc in self.cur.description]
        rows = self.cur.fetchall()
        return columns, rows

    def fetch_one(self, sql, params=None):
        self.cur.execute(sql, params or ())
        return self.cur.fetchone()


class App(ctk.CTk):
    def __init__(self, db: DBConn):
        super().__init__()
        self.db = db

        self.title("WorkForce Analytics – Minimal Black")
        self.geometry("1150x650")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.menu = None
        self.body = None

        self.build_ui()


    def build_ui(self):
        self.menu = ctk.CTkFrame(self, width=200)
        self.menu.pack(side="left", fill="y")

        ctk.CTkButton(
            self.menu, text="OT per Department (by week)", command=self.show_weekly_ot_by_dept
        ).pack(fill="x", pady=8, padx=10)

        ctk.CTkButton(self.menu, text="Add Time Record", command=self.show_time_entry_form).pack(
            fill="x", pady=3, padx=10
        )

        ctk.CTkButton(self.menu, text="Export Excel", command=self.export_excel).pack(
            fill="x", pady=8, padx=10
        )

        ctk.CTkLabel(self.menu, text="ดูตารางข้อมูลต่างๆ", anchor="w").pack(
            fill="x", padx=10, pady=(15, 5)
        )

        ctk.CTkButton(self.menu, text="Department", command=self.show_department).pack(
            fill="x", pady=3, padx=10
        )

        ctk.CTkButton(self.menu, text="Payroll", command=self.show_payroll).pack(
            fill="x", pady=3, padx=10
        )
        ctk.CTkButton(self.menu, text="Shift", command=self.show_shift).pack(
            fill="x", pady=3, padx=10
        )
        ctk.CTkButton(self.menu, text="Time Records", command=self.show_time_records).pack(
            fill="x", pady=3, padx=10
        )
        ctk.CTkButton(self.menu, text="OT Summary", command=self.show_ot_summary_table).pack(
            fill="x", pady=3, padx=10
        )

        ctk.CTkButton(self.menu, text="Employees (Admin)", command=self.show_employees_admin).pack(
            fill="x", pady=3, padx=10
        )

        ctk.CTkButton(self.menu, text="ออก", fg_color="red", command=self.destroy).pack(
            fill="x", pady=20, padx=10
        )

        # MAIN BODY
        self.body = ctk.CTkFrame(self)
        self.body.pack(side="right", expand=True, fill="both")
        self.show_weekly_ot_by_dept()

    def check_admin_password(self) -> bool:
        try:
            dialog = ctk.CTkInputDialog(
                title="Admin Authentication",
                text="กรุณากรอกรหัสผ่านผู้ดูแลระบบ:"
            )
            pwd = dialog.get_input()
        except AttributeError:
            messagebox.showerror(
                "Error",
                "เวอร์ชัน customtkinter นี้ไม่รองรับ CTkInputDialog\nกรุณาอัปเกรด customtkinter ก่อน"
            )
            return False

        if pwd is None:
            return False

        if pwd != ADMIN_PASSWORD:
            messagebox.showerror("Access Denied", "รหัสผ่านไม่ถูกต้อง")
            return False

        return True


    def clear_body(self):
        for widget in self.body.winfo_children():
            widget.destroy()

    def show_table_generic(self, title: str, sql: str):
        self.clear_body()

        cols, rows = self.db.fetch_with_columns(sql)

        if not rows:
            messagebox.showinfo("NO DATA", f"ยังไม่มีข้อมูลใน {title}")
            return

        title_label = ctk.CTkLabel(self.body, text=title, font=("Arial", 18, "bold"))
        title_label.pack(pady=(10, 5))

        tree = ttk.Treeview(self.body, columns=cols, show="headings")

        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor="center")

        yscroll = ttk.Scrollbar(self.body, orient="vertical", command=tree.yview)
        xscroll = ttk.Scrollbar(self.body, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

        tree.pack(side="top", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")
        xscroll.pack(side="bottom", fill="x")

        for row in rows:
            tree.insert("", "end", values=row)

    def show_department(self):
        self.show_table_generic("Department", "SELECT * FROM department")
    
    def show_payroll(self):
        self.show_table_generic("Payroll", "SELECT * FROM payroll")

    def show_shift(self):
        self.show_table_generic("Shifts", "SELECT * FROM shift")

    def show_employees_admin(self):
        if not self.check_admin_password():
            return
        
        self.clear_body()

        container = ctk.CTkFrame(self.body)
        container.pack(fill="both", expand=True, padx=20, pady=20)

        title = ctk.CTkLabel(
            container, text="Manage Employees", font=("Arial", 18, "bold")
        )
        title.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        form_frame = ctk.CTkFrame(container)
        form_frame.grid(row=1, column=0, sticky="nw", padx=(0, 20), pady=10)

        table_frame = ctk.CTkFrame(container)
        table_frame.grid(row=1, column=1, sticky="nsew", pady=10)

        container.grid_rowconfigure(1, weight=1)
        container.grid_columnconfigure(1, weight=1)

        form_entries = {}

        def add_form_row(row, label, key, placeholder=""):
            ctk.CTkLabel(form_frame, text=label).grid(
                row=row, column=0, sticky="e", padx=5, pady=4
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

        form_btn_frame = ctk.CTkFrame(form_frame)
        form_btn_frame.grid(row=6, column=0, columnspan=2, pady=(10, 0))

        ctk.CTkButton(form_btn_frame, text="Add Employee", command=add_employee, width=120).pack(
            side="left", padx=5
        )
        ctk.CTkButton(form_btn_frame, text="Clear Form", command=clear_form, width=100).pack(
            side="left", padx=5
        )

        del_btn = ctk.CTkButton(table_frame, text="Delete Selected", command=delete_selected)
        del_btn.grid(row=2, column=0, pady=(8, 0), sticky="w")

        refresh_table()

    def show_time_entry_form(self):
        self.clear_body()

        wrapper = ctk.CTkFrame(self.body)
        wrapper.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            wrapper, text="Time Record – Check In / Check Out", font=("Arial", 18, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        fields = [
            ("Employee ID", "emp_id"),
            ("Work Date (YYYY-MM-DD)", "work_date"),
            ("Job Type (W/L/H/T)", "job_type"),
            ("Shift Code", "shift_code"),
            ("Clock In (auto)", "clock_in"),
            ("Clock Out (auto)", "clock_out"),
        ]
        entries = {}
        for idx, (label_text, key) in enumerate(fields, start=1):
            ctk.CTkLabel(wrapper, text=label_text).grid(
                row=idx, column=0, pady=6, padx=5, sticky="e"
            )
            entry = ctk.CTkEntry(wrapper, width=200)
            entry.grid(row=idx, column=1, pady=6, padx=5, sticky="w")
            entries[key] = entry

        from datetime import date
        entries["work_date"].insert(0, date.today().strftime("%Y-%m-%d"))

        def parse_time_str(t: str):
            t = t.strip()
            if not t:
                return None
            try:
                return datetime.strptime(t, "%H:%M:%S")
            except ValueError:
                raise ValueError("รูปแบบเวลาต้องเป็น HH:MM:SS เช่น 08:00:00")

        def calc_hours(diff):
            raw = diff.total_seconds() / 3600.0
            if raw <= 0:
                return 0.0
            return float(math.ceil(raw))  

        def get_base_info():
            data = {k: v.get().strip() for k, v in entries.items()}
            required_keys = ["emp_id", "work_date", "job_type", "shift_code"]
            if any(not data[k] for k in required_keys):
                messagebox.showwarning(
                    "Missing Data",
                    "กรุณากรอก Employee ID, Work Date, Job Type และ Shift Code ให้ครบ"
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
                    f"วันนี้ ( {work_date} ) มี Time Record ของ emp_id {emp_id} อยู่แล้ว"
                )
                return

            shift_row = self.db.fetch_one(
                "SELECT start_time, end_time FROM shift WHERE shift_code = %s",
                (shift_code,),
            )
            if not shift_row:
                messagebox.showwarning("Invalid Shift", f"ไม่พบ Shift code '{shift_code}' ในระบบ")
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
                messagebox.showwarning("Not Found", f"ไม่พบ emp_id '{emp_id}' ในตาราง employees")
                return
            department = emp_row[0]

            clock_in_str = datetime.now().strftime("%H:%M:%S")

            entries["clock_in"].delete(0, "end")
            entries["clock_in"].insert(0, clock_in_str)

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
                    f"ยังไม่มีการเช็คอินของ emp_id {emp_id} วันที่ {work_date}"
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
                    "ข้อมูลเวลาในระบบไม่ถูกต้อง (in/out/clock_in) ตรวจสอบฐานข้อมูล"
                )
                return

            clock_out_str = datetime.now().strftime("%H:%M:%S")
            entries["clock_out"].delete(0, "end")
            entries["clock_out"].insert(0, clock_out_str)

            try:
                clock_out_dt = parse_time_str(clock_out_str)
            except Exception:
                messagebox.showwarning(
                    "Invalid Time",
                    "ไม่สามารถอ่านเวลา Clock Out ปัจจุบันได้"
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

            bf_ot = f"{bf_ot_hours:.2f}" if bf_ot_hours > 0 else None
            af_ot = f"{af_ot_hours:.2f}" if af_ot_hours > 0 else None
            bt_ot = f"{bt_ot_hours:.2f}" if bt_ot_hours > 0 else None

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
                f"BF OT: {bf_ot or '0.00'}  AF OT: {af_ot or '0.00'}  BT OT: {bt_ot or '0.00'}"
            )

        btn_frame = ctk.CTkFrame(wrapper)
        btn_frame.grid(row=len(fields) + 2, column=0, columnspan=2, pady=(12, 0))

        ctk.CTkButton(btn_frame, text="Check In (INSERT)", command=handle_check_in, width=140).pack(
            side="left", padx=5
        )
        ctk.CTkButton(btn_frame, text="Check Out (UPDATE)", command=handle_check_out, width=140).pack(
            side="left", padx=5
        )
        ctk.CTkButton(btn_frame, text="Back to Time Records", command=self.show_time_records, width=160).pack(
            side="left", padx=5
        )

    def show_time_records(self):
        self.show_table_generic("Time Records", "SELECT * FROM time_records")
    
    def show_ot_summary_table(self):
        self.show_table_generic(
            "OT Monthly Summary",
            "SELECT * FROM v_monthly_payroll"
        )

    def show_weekly_ot_by_dept(self, top_only=False):
        self.clear_body()

        controls = ctk.CTkFrame(self.body)
        controls.pack(fill="x", pady=(5, 0), padx=5)
        ctk.CTkLabel(
            controls,
            text="OT per Department (Avg OT Hours)",
            font=("Arial", 16, "bold"),
        ).pack(side="left", padx=(5, 10))
        if top_only:
            ctk.CTkButton(
                controls,
                text="Show All",
                command=lambda: self.show_weekly_ot_by_dept(False),
                width=90,
            ).pack(side="left", padx=4)
        else:
            ctk.CTkButton(
                controls,
                text="Show Top 3",
                command=lambda: self.show_weekly_ot_by_dept(True),
                width=90,
            ).pack(side="left", padx=4)

        query = """
            SELECT e.department,
                   AVG(w.total_ot_hours) AS avg_ot_hours
            FROM v_weekly_hours_summary w
            JOIN employees e ON w.emp_id = e.emp_id
            GROUP BY e.department
            ORDER BY {order_clause}
        """.format(
            order_clause="avg_ot_hours DESC" if top_only else "e.department"
        )

        if top_only:
            query += " LIMIT 3"

        rows = self.db.fetch(query)

        if not rows:
            messagebox.showinfo("NO DATA", "ยังไม่มีข้อมูล OT Summary")
            return

        departments = [r[0] for r in rows]
        values = [float(r[1]) for r in rows]

        fig, ax = plt.subplots(figsize=(5, 2.5))
        ax.bar(departments, values, color="#00b4d8")
        ax.set_title("Top 3 Departments by Avg OT Hours" if top_only else "Average OT Hours per Department")
        ax.set_ylabel("Avg OT Hours")

        ax.set_xticks(range(len(departments)))
        ax.set_xticklabels(departments, rotation=60, ha="right")

        ax.tick_params(axis="x", labelsize=3)
        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.body)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        columns = ("department", "avg_ot_hours")
        tree = ttk.Treeview(self.body, columns=columns, show="headings", height=10)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor="center")
        for row in rows:
            tree.insert("", "end", values=row)
        tree.pack(fill="both", expand=True, pady=10)

    def export_excel(self):
        messagebox.showinfo("COMING SOON", "Export Excel กำลังพัฒนา…")


def main():
    db = DBConn()

    app = App(db)
    app.mainloop()


if __name__ == "__main__":
    main()
