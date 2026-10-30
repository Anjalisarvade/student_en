

import re
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import date

DB_PATH = Path(__file__).resolve().with_name("student_enrollment.db")


def connect_db():
    """Open a database connection with foreign-key enforcement enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create database tables and insert starter courses if needed."""
    with connect_db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS students (
                student_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                gender TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                guardian_name TEXT NOT NULL,
                previous_education TEXT NOT NULL,
                admission_date TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS courses (
                course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_name TEXT NOT NULL UNIQUE,
                course_duration TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                enrollment_date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                UNIQUE(student_id, course_id),
                FOREIGN KEY(student_id) REFERENCES students(student_id)
                    ON DELETE CASCADE,
                FOREIGN KEY(course_id) REFERENCES courses(course_id)
                    ON DELETE CASCADE
            );
            """
        )
        course_count = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
        if course_count == 0:
            conn.executemany(
                "INSERT INTO courses (course_name, course_duration) VALUES (?, ?)",
                [
                    ("Bachelor of Computer Applications (BCA)", "3 years"),
                    ("Bachelor of Business Administration (BBA)", "3 years"),
                    ("Bachelor of Science (Computer Science)", "3 years"),
                    ("Diploma in Information Technology", "1 year"),
                    ("Python Programming", "3 months"),
                ],
            )


def valid_email(value):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value) is not None


def valid_date(value):
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


class StudentEnrollmentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Enrollment System")
        self.root.geometry("1180x760")
        self.root.minsize(980, 650)
        self.selected_student_id = None
        self.course_map = {}

        self.configure_style()
        self.build_ui()
        self.load_courses()
        self.refresh_students()
        self.refresh_enrollments()

    def configure_style(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Section.TLabel", font=("Segoe UI", 11, "bold"))
        style.configure("Treeview", rowheight=25, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))
        style.configure("TButton", padding=6)

    def build_ui(self):
        header = ttk.Frame(self.root, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Student Enrollment System", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Register students, manage records, and enroll students in courses",
        ).pack(anchor="w", pady=(3, 0))

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.student_tab = ttk.Frame(self.notebook, padding=12)
        self.enrollment_tab = ttk.Frame(self.notebook, padding=12)
        self.course_tab = ttk.Frame(self.notebook, padding=12)
        self.notebook.add(self.student_tab, text="Student Management")
        self.notebook.add(self.enrollment_tab, text="Course Enrollment")
        self.notebook.add(self.course_tab, text="Courses")

        self.build_student_tab()
        self.build_enrollment_tab()
        self.build_course_tab()

    def build_student_tab(self):
        form = ttk.LabelFrame(self.student_tab, text="Student Details", padding=10)
        form.pack(fill="x")

        self.fields = {}
        field_specs = [
            ("Full Name", "full_name"),
            ("Date of Birth (YYYY-MM-DD)", "date_of_birth"),
            ("Gender", "gender"),
            ("Email", "email"),
            ("Phone", "phone"),
            ("Address", "address"),
            ("Parent / Guardian", "guardian_name"),
            ("Previous Education", "previous_education"),
            ("Admission Date (YYYY-MM-DD)", "admission_date"),
        ]

        for index, (label, key) in enumerate(field_specs):
            row, col = divmod(index, 3)
            cell = ttk.Frame(form)
            cell.grid(row=row, column=col, sticky="ew", padx=6, pady=5)
            ttk.Label(cell, text=label).pack(anchor="w")
            if key == "gender":
                widget = ttk.Combobox(
                    cell, values=("Female", "Male", "Non-binary", "Prefer not to say"),
                    state="readonly", width=30
                )
                widget.set("Prefer not to say")
            else:
                widget = ttk.Entry(cell, width=33)
                if key == "admission_date":
                    widget.insert(0, date.today().isoformat())
            widget.pack(fill="x")
            self.fields[key] = widget

        for col in range(3):
            form.columnconfigure(col, weight=1)

        buttons = ttk.Frame(self.student_tab)
        buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Add Student", command=self.add_student).pack(side="left", padx=(0, 6))
        ttk.Button(buttons, text="Update Selected", command=self.update_student).pack(side="left", padx=6)
        ttk.Button(buttons, text="Delete Selected", command=self.delete_student).pack(side="left", padx=6)
        ttk.Button(buttons, text="Clear Form", command=self.clear_form).pack(side="left", padx=6)

        search_frame = ttk.Frame(self.student_tab)
        search_frame.pack(fill="x", pady=(2, 8))
        ttk.Label(search_frame, text="Search by student ID, name, or email:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=32)
        search_entry.pack(side="left", padx=8)
        search_entry.bind("<Return>", lambda _event: self.refresh_students())
        ttk.Button(search_frame, text="Search", command=self.refresh_students).pack(side="left")
        ttk.Button(search_frame, text="Show All", command=self.clear_search).pack(side="left", padx=6)

        columns = (
            "student_id", "full_name", "date_of_birth", "gender", "email", "phone",
            "address", "guardian_name", "previous_education", "admission_date"
        )
        tree_frame = ttk.Frame(self.student_tab)
        tree_frame.pack(fill="both", expand=True)
        self.student_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=11)
        headings = {
            "student_id": "Student ID", "full_name": "Full Name",
            "date_of_birth": "Date of Birth", "gender": "Gender", "email": "Email",
            "phone": "Phone", "address": "Address", "guardian_name": "Guardian",
            "previous_education": "Previous Education", "admission_date": "Admission Date",
        }
        widths = {
            "student_id": 75, "full_name": 150, "date_of_birth": 105, "gender": 100,
            "email": 190, "phone": 110, "address": 180, "guardian_name": 150,
            "previous_education": 150, "admission_date": 110,
        }
        for col in columns:
            self.student_tree.heading(col, text=headings[col])
            self.student_tree.column(col, width=widths[col], minwidth=70, anchor="w")
        yscroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.student_tree.yview)
        xscroll = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.student_tree.xview)
        self.student_tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.student_tree.grid(row=0, column=0, sticky="nsew")
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.student_tree.bind("<<TreeviewSelect>>", self.on_student_select)

    def build_enrollment_tab(self):
        form = ttk.LabelFrame(self.enrollment_tab, text="Enroll Student in a Course", padding=12)
        form.pack(fill="x")
        ttk.Label(form, text="Student").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.enroll_student_var = tk.StringVar()
        self.enroll_student_combo = ttk.Combobox(
            form, textvariable=self.enroll_student_var, state="readonly", width=52
        )
        self.enroll_student_combo.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(form, text="Course").grid(row=0, column=1, sticky="w", padx=5, pady=5)
        self.enroll_course_var = tk.StringVar()
        self.enroll_course_combo = ttk.Combobox(
            form, textvariable=self.enroll_course_var, state="readonly", width=52
        )
        self.enroll_course_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)

        ttk.Button(form, text="Enroll Student", command=self.enroll_student).grid(
            row=1, column=2, padx=8, pady=5
        )
        ttk.Button(form, text="Refresh", command=self.refresh_all).grid(
            row=1, column=3, padx=8, pady=5
        )

        ttk.Label(self.enrollment_tab, text="Enrollment Records", style="Section.TLabel").pack(
            anchor="w", pady=(14, 6)
        )
        columns = ("enrollment_id", "student_id", "student_name", "course_name", "enrollment_date", "status")
        self.enrollment_tree = ttk.Treeview(self.enrollment_tab, columns=columns, show="headings")
        headings = {
            "enrollment_id": "Enrollment ID", "student_id": "Student ID",
            "student_name": "Student Name", "course_name": "Course",
            "enrollment_date": "Enrollment Date", "status": "Status",
        }
        widths = {"enrollment_id": 100, "student_id": 90, "student_name": 220,
                  "course_name": 320, "enrollment_date": 140, "status": 100}
        for col in columns:
            self.enrollment_tree.heading(col, text=headings[col])
            self.enrollment_tree.column(col, width=widths[col], anchor="w")
        self.enrollment_tree.pack(fill="both", expand=True)
        controls = ttk.Frame(self.enrollment_tab)
        controls.pack(fill="x", pady=8)
        ttk.Button(controls, text="Set Selected to Active", command=lambda: self.set_enrollment_status("Active")).pack(side="left")
        ttk.Button(controls, text="Set Selected to Completed", command=lambda: self.set_enrollment_status("Completed")).pack(side="left", padx=8)
        ttk.Button(controls, text="Set Selected to Cancelled", command=lambda: self.set_enrollment_status("Cancelled")).pack(side="left")

    def build_course_tab(self):
        form = ttk.LabelFrame(self.course_tab, text="Add a Course", padding=12)
        form.pack(fill="x")
        ttk.Label(form, text="Course Name").grid(row=0, column=0, sticky="w", padx=5)
        self.course_name_entry = ttk.Entry(form, width=50)
        self.course_name_entry.grid(row=1, column=0, sticky="ew", padx=5, pady=6)
        ttk.Label(form, text="Course Duration (e.g. 3 years)").grid(row=0, column=1, sticky="w", padx=5)
        self.course_duration_entry = ttk.Entry(form, width=25)
        self.course_duration_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=6)
        ttk.Button(form, text="Add Course", command=self.add_course).grid(row=1, column=2, padx=8)
        form.columnconfigure(0, weight=2)
        form.columnconfigure(1, weight=1)

        columns = ("course_id", "course_name", "course_duration")
        self.course_tree = ttk.Treeview(self.course_tab, columns=columns, show="headings", height=15)
        for col, heading, width in [
            ("course_id", "Course ID", 100),
            ("course_name", "Course Name", 600),
            ("course_duration", "Duration", 180),
        ]:
            self.course_tree.heading(col, text=heading)
            self.course_tree.column(col, width=width, anchor="w")
        self.course_tree.pack(fill="both", expand=True, pady=12)
        ttk.Button(self.course_tab, text="Refresh Courses", command=self.load_courses).pack(anchor="w")

    def get_form_data(self):
        data = {}
        for key, widget in self.fields.items():
            data[key] = widget.get().strip()
        return data

    def validate_student(self, data):
        required = {
            "full_name": "Full name", "date_of_birth": "Date of birth",
            "gender": "Gender", "email": "Email", "phone": "Phone",
            "address": "Address", "guardian_name": "Parent/guardian name",
            "previous_education": "Previous education", "admission_date": "Admission date",
        }
        for key, label in required.items():
            if not data[key]:
                messagebox.showwarning("Missing Information", f"{label} is required.")
                return False
        if not valid_email(data["email"]):
            messagebox.showwarning("Invalid Email", "Enter a valid email address.")
            return False
        if not valid_date(data["date_of_birth"]):
            messagebox.showwarning("Invalid Date", "Date of birth must use YYYY-MM-DD.")
            return False
        if not valid_date(data["admission_date"]):
            messagebox.showwarning("Invalid Date", "Admission date must use YYYY-MM-DD.")
            return False
        if len(data["phone"]) < 7:
            messagebox.showwarning("Invalid Phone", "Enter a valid phone number (at least 7 characters).")
            return False
        return True

    def add_student(self):
        data = self.get_form_data()
        if not self.validate_student(data):
            return
        try:
            with connect_db() as conn:
                conn.execute(
                    """INSERT INTO students
                    (full_name, date_of_birth, gender, email, phone, address,
                     guardian_name, previous_education, admission_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    tuple(data[k] for k in (
                        "full_name", "date_of_birth", "gender", "email", "phone",
                        "address", "guardian_name", "previous_education", "admission_date"
                    )),
                )
            messagebox.showinfo("Success", "Student registered successfully.")
            self.clear_form()
            self.refresh_all()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Email", "A student with this email address already exists.")
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not add student:\n{exc}")

    def update_student(self):
        if self.selected_student_id is None:
            messagebox.showwarning("Select Student", "Select a student from the table first.")
            return
        data = self.get_form_data()
        if not self.validate_student(data):
            return
        try:
            with connect_db() as conn:
                conn.execute(
                    """UPDATE students SET full_name=?, date_of_birth=?, gender=?, email=?,
                    phone=?, address=?, guardian_name=?, previous_education=?, admission_date=?
                    WHERE student_id=?""",
                    tuple(data[k] for k in (
                        "full_name", "date_of_birth", "gender", "email", "phone",
                        "address", "guardian_name", "previous_education", "admission_date"
                    )) + (self.selected_student_id,),
                )
            messagebox.showinfo("Success", "Student details updated.")
            self.clear_form()
            self.refresh_all()
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Email", "Another student already uses this email address.")
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not update student:\n{exc}")

    def delete_student(self):
        if self.selected_student_id is None:
            messagebox.showwarning("Select Student", "Select a student from the table first.")
            return
        if not messagebox.askyesno(
            "Confirm Delete",
            "Delete this student and their enrollment records? This cannot be undone."
        ):
            return
        try:
            with connect_db() as conn:
                conn.execute("DELETE FROM students WHERE student_id=?", (self.selected_student_id,))
            messagebox.showinfo("Deleted", "Student and related enrollment records deleted.")
            self.clear_form()
            self.refresh_all()
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not delete student:\n{exc}")

    def on_student_select(self, _event=None):
        selection = self.student_tree.selection()
        if not selection:
            return
        values = self.student_tree.item(selection[0], "values")
        self.selected_student_id = int(values[0])
        keys = [
            "full_name", "date_of_birth", "gender", "email", "phone", "address",
            "guardian_name", "previous_education", "admission_date"
        ]
        for key, value in zip(keys, values[1:]):
            widget = self.fields[key]
            widget.delete(0, "end")
            if key == "gender":
                widget.set(value)
            else:
                widget.insert(0, value)

    def clear_form(self):
        self.selected_student_id = None
        for key, widget in self.fields.items():
            if key == "gender":
                widget.set("Prefer not to say")
            else:
                widget.delete(0, "end")
                if key == "admission_date":
                    widget.insert(0, date.today().isoformat())
        for item in self.student_tree.selection():
            self.student_tree.selection_remove(item)

    def clear_search(self):
        self.search_var.set("")
        self.refresh_students()

    def refresh_students(self):
        query = self.search_var.get().strip()
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        try:
            with connect_db() as conn:
                if query:
                    rows = conn.execute(
                        """SELECT student_id, full_name, date_of_birth, gender, email, phone,
                        address, guardian_name, previous_education, admission_date
                        FROM students
                        WHERE CAST(student_id AS TEXT) LIKE ? OR full_name LIKE ? OR email LIKE ?
                        ORDER BY student_id DESC""",
                        (f"%{query}%", f"%{query}%", f"%{query}%"),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """SELECT student_id, full_name, date_of_birth, gender, email, phone,
                        address, guardian_name, previous_education, admission_date
                        FROM students ORDER BY student_id DESC"""
                    ).fetchall()
            for row in rows:
                self.student_tree.insert("", "end", values=row)
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load students:\n{exc}")

    def load_courses(self):
        try:
            with connect_db() as conn:
                courses = conn.execute(
                    "SELECT course_id, course_name, course_duration FROM courses ORDER BY course_name"
                ).fetchall()
            for item in self.course_tree.get_children():
                self.course_tree.delete(item)
            self.course_map = {}
            course_options = []
            for course_id, name, duration in courses:
                self.course_tree.insert("", "end", values=(course_id, name, duration))
                label = f"{course_id} - {name} ({duration})"
                self.course_map[label] = course_id
                course_options.append(label)
            self.enroll_course_combo["values"] = course_options
            if course_options and self.enroll_course_var.get() not in course_options:
                self.enroll_course_var.set(course_options[0])
            elif not course_options:
                self.enroll_course_var.set("")
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load courses:\n{exc}")

    def refresh_student_choices(self):
        try:
            with connect_db() as conn:
                rows = conn.execute(
                    "SELECT student_id, full_name, email FROM students ORDER BY full_name"
                ).fetchall()
            options = [f"{sid} - {name} ({email})" for sid, name, email in rows]
            self.enroll_student_combo["values"] = options
            if options and self.enroll_student_var.get() not in options:
                self.enroll_student_var.set(options[0])
            elif not options:
                self.enroll_student_var.set("")
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load student choices:\n{exc}")

    def enroll_student(self):
        student_label = self.enroll_student_var.get()
        course_label = self.enroll_course_var.get()
        if not student_label:
            messagebox.showwarning("No Students", "Register a student before enrolling.")
            return
        if not course_label:
            messagebox.showwarning("No Courses", "Add or select a course before enrolling.")
            return
        try:
            student_id = int(student_label.split(" - ", 1)[0])
            course_id = self.course_map[course_label]
            with connect_db() as conn:
                conn.execute(
                    """INSERT INTO enrollments (student_id, course_id, enrollment_date, status)
                    VALUES (?, ?, ?, 'Active')""",
                    (student_id, course_id, date.today().isoformat()),
                )
            messagebox.showinfo("Success", "Student enrolled in the selected course.")
            self.refresh_enrollments()
        except sqlite3.IntegrityError:
            messagebox.showwarning("Already Enrolled", "This student is already enrolled in that course.")
        except (sqlite3.Error, ValueError, KeyError) as exc:
            messagebox.showerror("Enrollment Error", f"Could not complete enrollment:\n{exc}")

    def refresh_enrollments(self):
        if not hasattr(self, "enrollment_tree"):
            return
        for item in self.enrollment_tree.get_children():
            self.enrollment_tree.delete(item)
        try:
            with connect_db() as conn:
                rows = conn.execute(
                    """SELECT e.enrollment_id, s.student_id, s.full_name, c.course_name,
                    e.enrollment_date, e.status
                    FROM enrollments e
                    JOIN students s ON s.student_id=e.student_id
                    JOIN courses c ON c.course_id=e.course_id
                    ORDER BY e.enrollment_id DESC"""
                ).fetchall()
            for row in rows:
                self.enrollment_tree.insert("", "end", values=row)
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not load enrollments:\n{exc}")

    def set_enrollment_status(self, status):
        selection = self.enrollment_tree.selection()
        if not selection:
            messagebox.showwarning("Select Enrollment", "Select an enrollment record first.")
            return
        enrollment_id = int(self.enrollment_tree.item(selection[0], "values")[0])
        try:
            with connect_db() as conn:
                conn.execute(
                    "UPDATE enrollments SET status=? WHERE enrollment_id=?",
                    (status, enrollment_id),
                )
            self.refresh_enrollments()
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not update enrollment:\n{exc}")

    def add_course(self):
        name = self.course_name_entry.get().strip()
        duration = self.course_duration_entry.get().strip()
        if not name or not duration:
            messagebox.showwarning("Missing Information", "Enter both course name and duration.")
            return
        try:
            with connect_db() as conn:
                conn.execute(
                    "INSERT INTO courses (course_name, course_duration) VALUES (?, ?)",
                    (name, duration),
                )
            self.course_name_entry.delete(0, "end")
            self.course_duration_entry.delete(0, "end")
            self.load_courses()
            self.refresh_enrollments()
            messagebox.showinfo("Success", "Course added successfully.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Course", "A course with that name already exists.")
        except sqlite3.Error as exc:
            messagebox.showerror("Database Error", f"Could not add course:\n{exc}")

    def refresh_all(self):
        self.refresh_students()
        self.load_courses()
        self.refresh_student_choices()
        self.refresh_enrollments()


def main():
    try:
        init_db()
        root = tk.Tk()
        app = StudentEnrollmentApp(root)
        app.refresh_student_choices()
        root.mainloop()
    except sqlite3.Error as exc:
        messagebox.showerror("Startup Error", f"Could not initialize the database:\n{exc}")
    except tk.TclError as exc:
        print("Could not start the graphical interface.")
        print("On Linux, install Tkinter with your system package manager (for example: sudo apt install python3-tk).")
        print(f"Details: {exc}")


if __name__ == "__main__":
    main()
