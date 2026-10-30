# Student Enrollment System Using Python

## Project Description
The Student Enrollment System is a desktop application developed using Python, Tkinter, and SQLite. It helps schools and colleges manage student registration, student records, courses, and course enrollments.

## Technologies Used
- Python
- Tkinter (Graphical User Interface)
- SQLite (Database)
- sqlite3 (Database connectivity)

## Features
- Register new students
- Automatically generate unique student IDs
- View all registered students
- Search students by ID, name, or email
- Update student details
- Delete student records
- Add and view courses
- Enroll students in courses
- Prevent duplicate course enrollments
- Update enrollment status
- Validate user input
- Automatically create the database

## Project Files

```text
StudentEnrollment/
├── student_enrollment.py
├── README.md
└── student_enrollment.db  (created automatically)
```

## Requirements
- Python 3.x
- Tkinter
- SQLite

Tkinter and SQLite are included with most standard Python installations. No additional Python packages are normally required.

## How to Run the Project

### Step 1: Install Python
Download and install Python from the official website:

https://www.python.org/downloads/

On Windows, enable **Add Python to PATH** during installation.

### Step 2: Download the Project
Download `student_enrollment.py` and save it in a folder.

### Step 3: Open the Terminal
Open Command Prompt or the VS Code terminal and navigate to the project folder.

```bash
cd path/to/StudentEnrollment
```

Replace the example path with the actual location of your folder.

### Step 4: Run the Application

On Windows:

```bash
python student_enrollment.py
```

Alternatively:

```bash
py student_enrollment.py
```

On Linux or macOS:

```bash
python3 student_enrollment.py
```

### Step 5: Start Using the Application
The Student Enrollment System window will open.

You can:
1. Register new students.
2. View, search, update, or delete student records.
3. Add courses.
4. Enroll students in courses.
5. Update enrollment status.

## Database Information
The application automatically creates an SQLite database named `student_enrollment.db` in the same directory as the Python file.

The database contains three tables:

- **Students:** Stores student information.
- **Courses:** Stores available courses.
- **Enrollments:** Stores student course enrollment records.

Keep the database file to preserve your records between application sessions.

## Troubleshooting

**Problem: Python is not recognized.**

Solution: Install Python and enable the Add Python to PATH option.

**Problem: No module named tkinter.**

Solution: Install or repair your Python installation with Tkinter support. On Ubuntu, you can usually run:

```bash
sudo apt install python3-tk
```

**Problem: The application does not open.**

Solution: Check your Python installation and confirm that the terminal is open in the directory containing `student_enrollment.py`.

## Author
Anjali Sarvade —  Student Enrollment System

## License
This project is intended for educational and academic use.
