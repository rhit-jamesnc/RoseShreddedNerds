import csv
import os
import pyodbc
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# ── paths ────────────────────────────────────────────────────────────────────
_BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
_ENV_PATH   = os.path.join(_BASE_DIR, "..", ".env")
DATA_DIR    = os.path.join(_BASE_DIR, "data")


def csv_path(filename):
    return os.path.join(DATA_DIR, filename)

def read_csv(filename):
    path = csv_path(filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

# ── connection ────────────────────────────────────────────────────────────────
load_dotenv(_ENV_PATH, override=True)

DB_SERVER  = os.getenv("DB_SERVER")
DB_DRIVER  = os.getenv("DB_DRIVER", "{ODBC Driver 17 for SQL Server}")
TARGET_DB  = os.getenv("DB_NAME")

def get_conn():
    cs = (
        f"DRIVER={DB_DRIVER};SERVER={DB_SERVER};DATABASE={TARGET_DB};"
        f"Trusted_Connection=yes;TrustServerCertificate=yes;"
    )
    return pyodbc.connect(cs)

def _id(cursor):
    cursor.execute("SELECT @@IDENTITY")
    return int(cursor.fetchone()[0])

# ── step 1 – exercises ────────────────────────────────────────────────────────
def import_exercises(cursor):
    exercise_map = {}
    for row in read_csv("exercises.csv"):
        name = row["name"].strip()
        cat  = row["category"].strip()

        cursor.execute("SELECT ID FROM [Exercise] WHERE [Name] = ?", (name,))
        existing = cursor.fetchone()
        if existing:
            exercise_map[name.lower()] = existing[0]
        else:
            cursor.execute(
                "INSERT INTO [Exercise] ([Name], Category) VALUES (?, ?)",
                (name, cat)
            )
            exercise_map[name.lower()] = _id(cursor)

    print(f"  Exercises: {len(exercise_map)} upserted")
    return exercise_map

# ── step 2 – persons ──────────────────────────────────────────────────────────
def import_persons(cursor):
    person_map = {}
    DEFAULT_PW = generate_password_hash("Password1!")

    for row in read_csv("persons.csv"):
        uname  = row["username"].strip()
        fname  = row["fname"].strip()
        lname  = row["lname"].strip()
        role   = row["role"].strip()          # 'Student' or 'Trainer'
        dob    = row["dob"].strip() or None
        weight = int(row["weight"]) if row.get("weight", "").strip() else None

        cursor.execute("SELECT ID FROM [Person] WHERE Username = ?", (uname,))
        existing = cursor.fetchone()
        if existing:
            person_map[uname.lower()] = existing[0]
            continue

        cursor.execute(
            "INSERT INTO [Person] (FName, LName, Username, PasswordHash, DOB, [Weight]) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (fname, lname, uname, DEFAULT_PW, dob, weight)
        )
        new_id = _id(cursor)

        if role == "Student":
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Student] WHERE ID = ?) "
                "INSERT INTO [Student] (ID) VALUES (?)", (new_id, new_id)
            )
        else:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Trainer] WHERE ID = ?) "
                "INSERT INTO [Trainer] (ID) VALUES (?)", (new_id, new_id)
            )

        person_map[uname.lower()] = new_id

    print(f"  Persons:   {len(person_map)} upserted")
    return person_map

# ── step 3 – classes + teaches ────────────────────────────────────────────────
def import_classes(cursor, person_map):
    class_map = {}
    for row in read_csv("classes.csv"):
        cname   = row["name"].strip()
        trainer = row["trainer_username"].strip()
        trainer_id = person_map.get(trainer.lower())

        if not trainer_id:
            print(f"  WARNING: trainer '{trainer}' not found – skipping class '{cname}'")
            continue

        cursor.execute("SELECT ID FROM [Class] WHERE [Name] = ?", (cname,))
        existing = cursor.fetchone()
        if existing:
            class_map[cname.lower()] = existing[0]
        else:
            cursor.execute("INSERT INTO [Class] ([Name]) VALUES (?)", (cname,))
            class_id = _id(cursor)
            class_map[cname.lower()] = class_id

            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Teaches] WHERE TrainerID = ? AND ClassID = ?) "
                "INSERT INTO [Teaches] (TrainerID, ClassID) VALUES (?, ?)",
                (trainer_id, class_id, trainer_id, class_id)
            )

    print(f"  Classes:   {len(class_map)} upserted")
    return class_map

# ── step 4 – enrollments ──────────────────────────────────────────────────────
def import_enrollments(cursor, person_map, class_map):
    count = 0
    for row in read_csv("enrollments.csv"):
        uname  = row["student_username"].strip()
        cname  = row["class_name"].strip()
        sid    = person_map.get(uname.lower())
        cid    = class_map.get(cname.lower())

        if not sid or not cid:
            print(f"  WARNING: enrollment skip – student='{uname}' class='{cname}'")
            continue

        cursor.execute(
            "IF NOT EXISTS (SELECT 1 FROM [HasA] WHERE StudentID = ? AND ClassID = ?) "
            "INSERT INTO [HasA] (StudentID, ClassID) VALUES (?, ?)",
            (sid, cid, sid, cid)
        )
        count += 1

    print(f"  Enrollments: {count} upserted")

# ── step 5 – sessions ─────────────────────────────────────────────────────────
def import_sessions(cursor, person_map, class_map):
    """Returns {session_code: session_db_id}"""
    session_map = {}
    for row in read_csv("sessions.csv"):
        code       = row["session_code"].strip()
        date       = row["date"].strip()
        start_t    = row["start_time"].strip() or None
        end_t      = row["end_time"].strip() or None
        location   = row["location"].strip() or None
        notes      = row["notes"].strip() or None
        visibility = int(row["visibility"]) if row["visibility"].strip() else 0
        student_un = row["student_username"].strip()
        class_name = row["class_name"].strip()

        student_id = person_map.get(student_un.lower()) if student_un else None
        class_id   = class_map.get(class_name.lower()) if class_name else None

        cursor.execute(
            "INSERT INTO [Session] ([Date], StartTime, EndTime, Location, Notes, "
            "Visibility, StudentID, ClassID) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (date, start_t, end_t, location, notes, visibility, student_id, class_id)
        )
        session_map[code] = _id(cursor)

    print(f"  Sessions:  {len(session_map)} inserted")
    return session_map

# ── step 6 – logs ─────────────────────────────────────────────────────────────
def import_logs(cursor, session_map, exercise_map):
    count = 0
    for row in read_csv("logs.csv"):
        code    = row["session_code"].strip()
        exname  = row["exercise_name"].strip()
        is_pr   = int(row["is_pr"])
        sess_id = session_map.get(code)
        ex_id   = exercise_map.get(exname.lower())

        if not sess_id or not ex_id:
            print(f"  WARNING: log skip – code='{code}' exercise='{exname}'")
            continue

        cursor.execute(
            "IF NOT EXISTS (SELECT 1 FROM [Logs] WHERE ExerciseID = ? AND SessionID = ?) "
            "INSERT INTO [Logs] (ExerciseID, SessionID, IsPr) VALUES (?, ?, ?)",
            (ex_id, sess_id, ex_id, sess_id, is_pr)
        )
        count += 1

    print(f"  Logs:      {count} upserted")

# ── step 7 – sets ─────────────────────────────────────────────────────────────
def import_sets(cursor, session_map, exercise_map):
    count = 0
    for row in read_csv("sets.csv"):
        code    = row["session_code"].strip()
        exname  = row["exercise_name"].strip()
        set_num = int(row["set_number"])
        weight  = float(row["weight"])
        reps    = int(row["reps"])
        sess_id = session_map.get(code)
        ex_id   = exercise_map.get(exname.lower())

        if not sess_id or not ex_id:
            print(f"  WARNING: set skip – code='{code}' exercise='{exname}'")
            continue

        cursor.execute(
            "IF NOT EXISTS (SELECT 1 FROM [Set] "
            "  WHERE ExerciseID = ? AND SessionID = ? AND SetNumber = ?) "
            "INSERT INTO [Set] (ExerciseID, SessionID, SetNumber, Weight, Reps) "
            "VALUES (?, ?, ?, ?, ?)",
            (ex_id, sess_id, set_num,
             ex_id, sess_id, set_num, weight, reps)
        )
        count += 1

    print(f"  Sets:      {count} upserted")

# ── step 8 – personal records ─────────────────────────────────────────────────
def import_personal_records(cursor, person_map, exercise_map):
    count = 0
    for row in read_csv("personal_records.csv"):
        uname  = row["student_username"].strip()
        exname = row["exercise_name"].strip()
        weight = float(row["weight"])
        reps   = int(row["reps"])
        date   = row["date"].strip()

        student_id = person_map.get(uname.lower())
        ex_id      = exercise_map.get(exname.lower())

        if not student_id:
            print(f"  WARNING: PR skip – username '{uname}' not found")
            continue
        if not ex_id:
            print(f"  WARNING: PR skip – exercise '{exname}' not found")
            continue

        cursor.execute("SELECT 1 FROM [Student] WHERE ID = ?", (student_id,))
        if not cursor.fetchone():
            print(f"  WARNING: PR skip – '{uname}' (ID {student_id}) not in Student table")
            continue

        cursor.execute(
            "SELECT a.PersonalRecordID FROM [Achieves] a "
            "JOIN [Of] o ON a.PersonalRecordID = o.PersonalRecordID "
            "WHERE a.StudentID = ? AND o.ExerciseID = ?",
            (student_id, ex_id)
        )
        existing = cursor.fetchone()
        if existing:
            pr_id = existing[0]
            cursor.execute(
                "UPDATE [PersonalRecord] SET [Weight] = ?, Reps = ?, [Date] = ? WHERE ID = ?",
                (weight, reps, date, pr_id)
            )
        else:
            cursor.execute(
                "INSERT INTO [PersonalRecord] ([Weight], Reps, [Date]) VALUES (?, ?, ?)",
                (weight, reps, date)
            )
            pr_id = _id(cursor)
            cursor.execute(
                "INSERT INTO [Achieves] (StudentID, PersonalRecordID) VALUES (?, ?)",
                (student_id, pr_id)
            )
            cursor.execute(
                "INSERT INTO [Of] (PersonalRecordID, ExerciseID) VALUES (?, ?)",
                (pr_id, ex_id)
            )
        count += 1

    print(f"  PersonalRecords: {count} upserted")

# ── main ──────────────────────────────────────────────────────────────────────
def run():
    print(f"\nConnecting to [{TARGET_DB}] on {DB_SERVER} …")
    print(f"Reading CSVs from: {DATA_DIR}\n")

    # Verify all CSV files exist before starting
    required = [
        "exercises.csv", "persons.csv", "classes.csv", "enrollments.csv",
        "sessions.csv", "logs.csv", "sets.csv", "personal_records.csv"
    ]
    missing = [f for f in required if not os.path.exists(csv_path(f))]
    if missing:
        print(f"Missing CSV files: {missing}")
        return

    try:
        with get_conn() as conn:
            cursor = conn.cursor()
            print("Connected.\n")

            print("Step 1 – Exercises")
            exercise_map = import_exercises(cursor)
            conn.commit()

            print("\nStep 2 – Persons")
            person_map = import_persons(cursor)
            conn.commit()

            print("\nStep 3 – Classes + Teaches")
            class_map = import_classes(cursor, person_map)
            conn.commit()

            print("\nStep 4 – Enrollments (HasA)")
            import_enrollments(cursor, person_map, class_map)
            conn.commit()

            print("\nStep 5 – Sessions")
            session_map = import_sessions(cursor, person_map, class_map)
            conn.commit()

            print("\nStep 6 – Logs")
            import_logs(cursor, session_map, exercise_map)
            conn.commit()

            print("\nStep 7 – Sets")
            import_sets(cursor, session_map, exercise_map)
            conn.commit()

            print("\nStep 8 – Personal Records")
            import_personal_records(cursor, person_map, exercise_map)
            conn.commit()

            print("\nPopulation complete!")

    except pyodbc.Error as e:
        print(f"\nDatabase error: {e}")
        raise


if __name__ == "__main__":
    run()
