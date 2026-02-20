import re
import pyodbc
import os
import database_server
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone, date
from helpers_for_dataservice import now_iso, parse_iso_z, parse_date, epley_1rm, iso_week_of, iso_week_boundary

_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_BASE_DIR)
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"), override=False)
load_dotenv(os.path.join(_BASE_DIR, ".env"), override=False)

server = os.getenv("DB_SERVER")
database_master = 'master'
database = os.getenv("DB_NAME")
database_copy = os.getenv("DB_NAME_COPY", "RoseShreddednerdscopy")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")
encrypt = os.getenv("DB_ENCRYPT", "yes")
trust_server_cert = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")

WEIGHT_EXERCISES = [
    # (Name, Category)
    ("Bench Press", "strength"),
    ("Incline Bench Press", "strength"),
    ("Dumbbell Bench Press", "strength"),
    ("Squat", "strength"),
    ("Front Squat", "strength"),
    ("Deadlift", "strength"),
    ("Romanian Deadlift", "strength"),
    ("Overhead Press", "strength"),
    ("Barbell Row", "strength"),
    ("Lat Pulldown", "strength"),
    ("Pull-ups (Weighted)", "strength"),
    ("Dumbbell Curl", "strength"),
    ("Hammer Curl", "strength"),
    ("Tricep Pushdown", "strength"),
    ("Skull Crushers", "strength"),
    ("Leg Press", "strength"),
    ("Leg Extension", "strength"),
    ("Leg Curl", "strength"),
    ("Calf Raise", "strength"),
    ("Hip Thrust", "strength"),
    ("Lateral Raise", "strength"),
    ("Chest Fly", "strength"),
]

def build_connection_string(database_name):
    return (
        f"DRIVER={driver};"
        f"SERVER={server};"
        f"DATABASE={database_name};"
        f"UID={username};"
        f"PWD={password};"
        f"Encrypt={encrypt};"
        f"TrustServerCertificate={trust_server_cert};"
    )

connection_string_master = build_connection_string(database_master)
connection_string_database = build_connection_string(database)
connection_string_database_copy = build_connection_string(database_copy)



ISO_Z = "%Y-%m-%dT%H:%M:%SZ" # Storing the date and time format in ISO 8601 format with 'Z' suffix for UTC time

def _minutes_between(start_time, end_time):
    if start_time is None or end_time is None:
        return 0
    
    start = datetime.combine(datetime.today(), start_time)
    end = datetime.combine(datetime.today(), end_time)
    mins = int((end - start).total_seconds() // 60)

    return max(0, mins)

# The main class in this file which manages all the data for the application
class DataService:
    def __init__(self):
        self.server = os.getenv("DB_SERVER")
        self.database_master = 'master'
        self.database = os.getenv("DB_NAME")
        self.database_copy = os.getenv("DB_NAME_COPY", "RoseShreddednerdscopy")
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.driver = os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")
        self.encrypt = os.getenv("DB_ENCRYPT", "yes")
        self.trust_server_cert = os.getenv("DB_TRUST_SERVER_CERTIFICATE", "yes")

        self.connection_string_master = (
            f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database_master};"
            f"UID={self.username};PWD={self.password};Encrypt={self.encrypt};"
            f"TrustServerCertificate={self.trust_server_cert};"
        )
        self.connection_string_database = (
            f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};"
            f"UID={self.username};PWD={self.password};Encrypt={self.encrypt};"
            f"TrustServerCertificate={self.trust_server_cert};"
        )
        self.connection_string_database_copy = (
            f"DRIVER={self.driver};SERVER={self.server};DATABASE={self.database_copy};"
            f"UID={self.username};PWD={self.password};Encrypt={self.encrypt};"
            f"TrustServerCertificate={self.trust_server_cert};"
        )

        self.user = None

    def _role_for_person_id(self, person_id):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT
                        CASE
                            WHEN EXISTS (SELECT 1 FROM Trainer WHERE ID = ?) THEN 'trainer'
                            WHEN EXISTS (SELECT 1 FROM Student WHERE ID = ?) THEN 'student'
                            ELSE NULL
                        END
                    """,
                    (int(person_id), int(person_id)),
                )
                row = cursor.fetchone()
                return row[0] if row else None
        except Exception as e:
            print(f"SQL Error in _role_for_person_id: {e}")
            return None

    def _decorate_user(self, row):
        if not row:
            return None
        person_id = row[0]
        role = self._role_for_person_id(person_id)
        return {
            "ID": person_id,
            "FName": row[1],
            "LName": row[2],
            "Username": row[3],
            "PasswordHash": row[4],
            "DOB": row[5],
            "Weight": row[6],
            "sql_id": person_id,
            "role": role,
            "username": row[3],
            "first_name": row[1],
            "last_name": row[2],
        }

    def _user(self):
        return self.user

    def login(self, ID):
        self.user = self.get_user_by_id(int(ID))

    def logout(self):
        self.user = None

    def create_user(self, first_name, last_name, username, password_hash, dob=None, weight=None, role='student'):

        if role:
            role = role.strip().lower()
        else:
            role = 'student'
        
        # The way i had role field in table, it takes 'Student' or 'Trainer' so have to make first letter capital.
        role = role.capitalize()

        user_id = None
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SET NOCOUNT ON;
                DECLARE @GeneratedID int;

                EXEC add_Person ?, ?, ?, ?, ?, ?, ?, @GeneratedID OUTPUT;

                SELECT @GeneratedID;
                """, first_name, last_name, username, password_hash, dob, weight, role)

            row = cursor.fetchone()
            user_id = row[0]
            if row is None:
                raise RuntimeError("Error: No user was created")
            user_id = int(user_id)
            conn.commit()

        self.user = self.get_user_by_id(user_id)
        return self.user


    def get_user_by_username(self, username):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute("{CALL get_Person_by_Username (?)}", username)

                row = cursor.fetchone()
                if not row:
                    return None

                #stored procedure column ordering can differ; re-read by ID
                #suing the ID-based proc so field mapping stays consistent.
                return self.get_user_by_id(int(row[0]))
        except Exception as e:
            print(f"SQL Error in get_user_by_username: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            print("Calling get_person", user_id)
            cursor.execute("{CALL get_Person_by_ID (?)}", user_id)

            row = cursor.fetchone()
            if not row:
                return None
            
            return self._decorate_user(row)
    
    def update_user(self, ID, FName=None, LName=None, Username=None, PasswordHash=None, DOB=None, Weight=None):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL update_person_profile (?, ?, ?, ?, ?, ?, ?)}", ID, FName, LName, Username, PasswordHash, DOB, Weight)
            conn.commit()
        
        self.user = self.get_user_by_id(ID)
    
    def create_schedule_slot(self, ID, Date, StartTime, EndTime, Location, Notes, Visibility=0):
        session_id = None
        if Visibility == 'friends':
            Visibility = 1
        elif Visibility == "private":
            Visibility = 0
        print("Visibility is", Visibility)

        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SET NOCOUNT ON;
                DECLARE @GeneratedID int;

                EXEC add_session ?, ?, ?, ?, ?, ?, ?, ?, @GeneratedID OUTPUT;

                SELECT @GeneratedID;
                """, Date, StartTime, EndTime, Location, Notes, Visibility, ID, None)
        
            row = cursor.fetchone()
            session_id = row[0]
            if row is None:
                raise RuntimeError("Error: No user was created")
            session_id = int(session_id)
            print(session_id)
            conn.commit()
        
        return session_id

    def list_my_slots(self, ID, num_rows=5):
        slots = []
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            cursor.execute("{CALL get_schedule_info (?, ?)}", (num_rows, int(ID)))
            rows = cursor.fetchall()

            for row in rows:

                start_t = row[2]
                end_t = row[3]

                slot = {
                    "id": int(row[0]),
                    "date": row[1].strftime("%Y-%m-%d") if row[1] else "",
                    "start_time": start_t.strftime("%H:%M") if start_t else "",
                    "end_time": end_t.strftime("%H:%M") if end_t else "",
                    "location": row[4] or "",
                    "notes": row[5] or "",      
                    "visibility": bool(row[6]) if row[6] is not None else False,
                    "duration_minutes": _minutes_between(start_t, end_t),
                }

                slots.append(slot)

        return slots
    
    def list_exercises(self):
        exercises = []
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT MIN(ID) AS ID, [Name], [Category]
                    FROM [Exercise]
                    GROUP BY [Name], [Category]
                    ORDER BY [Name] ASC
                """)
                
                for row in cursor.fetchall():
                    exercises.append({
                        "id": row[0],
                        "name": row[1],
                        "category": row[2]
                    })
        except Exception as e:
            print(f"SQL Error in list_exercises: {e}")
            
        return exercises

    def add_exercise_and_info(self, Name, Category, Duration, SessionID, IsPr, SetNumber, Weight, Reps):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SET NOCOUNT ON;
                DECLARE @GeneratedID int;

                EXEC add_exercise_and_info
                    ?, ?, ?, ?, ?, ?, ?, ?, @GeneratedID OUTPUT;

                SELECT @GeneratedID;
            """, (Name, Category, Duration, SessionID, IsPr, SetNumber, Weight, Reps))

            row = cursor.fetchone()
            if row is None or row[0] is None:
                raise RuntimeError("Exercise ID not returned")

            conn.commit()
            return int(row[0])

    def get_session_info(self, SessionID):
        items = []
        session_date = None

        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            cursor.execute("{CALL get_session_info (?)}", (SessionID))
            rows = cursor.fetchall()

            for row in rows:
                items.append({
                    "name": row[0],
                    "category": row[1],
                    "duration": row[2],
                    "set_number": row[3],
                    "weight": float(row[4]) if row[4] is not None else None,
                    "reps": int(row[5]) if row[5] is not None else None,
                    "is_pr": bool(row[6])
                })

            cursor.execute("SELECT [Date] FROM [Session] WHERE ID = ?", (SessionID,))
            drow = cursor.fetchone()
            if drow and drow[0]:
                session_date = drow[0].strftime("%Y-%m-%d")

        return {"date": session_date, "items": items}
    
    def workout_totals(self, student_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    COUNT(*) AS total_sessions,
                    SUM(DATEDIFF(MINUTE, StartTime, EndTime)) AS total_minutes
                FROM [Session]
                WHERE StudentID = ?;
            """, (int(student_id),))

            row = cursor.fetchone()
            return {
                "total_sessions": int(row[0] or 0),
                "total_minutes": int(row[1] or 0),
            }
    
    # Method to register an exercise name and category pair in the database
    def list_exercises_second(self):
        exercises = []
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                # Use MIN(ID) with GROUP BY to get unique exercises, filter out test data
                cursor.execute("""
                    SELECT MIN(ID) AS ID, [Name], [Category]
                    FROM [Exercise]
                    WHERE [Category] IS NOT NULL
                      AND [Name] NOT IN ('Test', 'test10', 'Test2', 'test3', 'test4', 'test9', 'Testy', 'Bench', 'Bench2')
                    GROUP BY [Name], [Category]
                    ORDER BY [Name] ASC
                """)

                for row in cursor.fetchall():
                    exercises.append({
                        "id": row[0],
                        "name": row[1],
                        "category": row[2]
                    })
        except Exception as e:
            print(f"SQL Error in list_exercises: {e}")
            
        return exercises
    
    # Gets the name of exercise base don the id
    def _exercise_name(self, exercise_map, exercise_id):
        exercise = exercise_map.get(str(exercise_id))
        if exercise:
            return exercise["name"]
        else:
            return f"#{exercise_id}"
    
# ------------------------------------- SQL-based PR and Leaderboard Methods ---------------------------------------------------

    def _ensure_pr_history_table_sql(self):
        """Create PRHistory table if missing"""
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    IF OBJECT_ID('dbo.PRHistory', 'U') IS NULL
                    BEGIN
                        CREATE TABLE dbo.PRHistory (
                            ID int IDENTITY(1,1) PRIMARY KEY NOT NULL,
                            StudentID int NOT NULL REFERENCES Student(ID),
                            ExerciseID int NOT NULL REFERENCES Exercise(ID),
                            [Weight] decimal(7,2) NOT NULL,
                            Reps int NOT NULL,
                            OneRM decimal(10,2) NOT NULL,
                            RecordedAt datetime2 NOT NULL DEFAULT SYSUTCDATETIME()
                        );
                    END
                    """
                )
                conn.commit()
        except Exception as e:
            print(f"SQL Error in _ensure_pr_history_table_sql: {e}")

    def _insert_pr_history_row_sql(self, cursor, sql_student_id, exercise_name, best_weight, best_reps, best_1rm):
        """Insert PR history row using stored procedure"""
        try:
            cursor.execute(
                "{CALL insert_PRHistory (?, ?, ?, ?, ?)}",
                (int(sql_student_id), exercise_name, float(best_weight), int(best_reps), float(best_1rm))
            )
        except Exception as e:
            print(f"Error in insert_PRHistory: {e}")

    def get_personal_records_sql(self, sql_student_id):
        records = []
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL get_PersonalRecords (?)}", (sql_student_id,))
            for row in cursor.fetchall():
                records.append({
                    "exercise_name": row[0],
                    "category": row[1],
                    "best_weight_kg": float(row[2]),
                    "best_reps": row[3],
                    "best_1rm_kg": float(row[4]),
                    "updated_at": row[5].isoformat() if row[5] else None
                })
        return records

    def get_pr_progression_sql(self, sql_student_id):
        """Read PR history using stored procedure"""
        items = []
        self._ensure_pr_history_table_sql()
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL get_PRProgression (?)}", (sql_student_id,))
            for row in cursor.fetchall():
                items.append({
                    "exercise_name": row[0],
                    "best_weight_kg": float(row[1]),
                    "best_reps": int(row[2]),
                    "best_1rm_kg": float(row[3]),
                    "recorded_at": row[4].isoformat() if row[4] else None,
                })
        return items

    def _maybe_update_pr_sql(self, sql_student_id, exercise_name, weight_kg, reps):
        if not sql_student_id or not exercise_name:
            return None

        try:
            weight_val = float(weight_kg)
            reps_val = int(reps)
        except Exception:
            return None

        one_rm = epley_1rm(weight_val, reps_val)
        existing = None
        try:
            records = self.get_personal_records_sql(sql_student_id)
            for rec in records:
                if rec["exercise_name"].lower() == exercise_name.lower():
                    existing = rec
                    break
        except Exception as e:
            print(f"SQL Error in _maybe_update_pr_sql (read): {e}")

        if existing and one_rm <= existing.get("best_1rm_kg", 0):
            return None

        try:
            self._ensure_pr_history_table_sql()
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "{CALL upsert_PersonalRecord (?, ?, ?, ?)}",
                    (int(sql_student_id), exercise_name, weight_val, reps_val),
                )
                self._insert_pr_history_row_sql(
                    cursor,
                    int(sql_student_id),
                    exercise_name,
                    weight_val,
                    reps_val,
                    one_rm,
                )
                conn.commit()
        except Exception as e:
            print(f"SQL Error in _maybe_update_pr_sql (write): {e}")
            return None

        return {
            "exercise_name": exercise_name,
            "best_weight_kg": weight_val,
            "best_reps": reps_val,
            "best_1rm_kg": one_rm,
        }

    def _exercise_exists_sql(self, exercise_id):
        """Check exercise existence using stored procedure"""
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL check_ExerciseExists (?)}", (int(exercise_id),))
            row = cursor.fetchone()
            return row[0] == 1 if row else False

    def _exercise_name_by_id_sql(self, exercise_id):
        """Get exercise name using stored procedure"""
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL get_ExerciseName (?)}", (int(exercise_id),))
            row = cursor.fetchone()
            return row[0] if row else None

    def big3_leaderboard_sql(self):
        board = []
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL get_Big3Leaderboard}")
            for row in cursor.fetchall():
                board.append({
                    "username": row[0],
                    "display_name": f"{row[1]} {row[2][0]}.",
                    "big3_total_kg": round(float(row[3]), 2)
                })
        return board

    def exercise_leaderboards_sql(self, exercise_names=None, limit=10):
        names = exercise_names or ["Squat", "Bench Press", "Deadlift"]
        board = {}
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            for exercise_name in names:
                cursor.execute("{CALL get_ExerciseLeaderboard (?, ?)}", (exercise_name, limit))
                rows = []
                for idx, row in enumerate(cursor.fetchall(), start=1):
                    rows.append({
                        "rank": idx,
                        "username": row[0],
                        "display_name": f"{row[1]} {row[2][0]}.",
                        "best_1rm_kg": round(float(row[3]), 2),
                    })
                board[exercise_name] = rows
        return board

    # ------------------------------------- Classes and Trainers ---------------------------------------------------
    
    def create_class(self, trainer_id, name):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("{CALL sp_CreateClass (?, ?)}", (trainer_id, name))
                class_id = cursor.fetchone()[0]
                conn.commit()
                return {"class_id": class_id, "name": name}
            except Exception as e:
                conn.rollback()
                raise e

    def get_classes(self):
        classes = []
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL get_AllClasses}")
            for row in cursor.fetchall():
                classes.append({
                    "id": row[0],
                    "name": row[1],
                    "trainer_name": f"{row[2]} {row[3]}"
                })
        return classes
        
    def delete_class(self, trainer_id, class_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL sp_DeleteClass (?, ?)}", (trainer_id, class_id))
            result = cursor.fetchone()[0]
            if result == 1:
                conn.commit()
                return {"success": True}
            else:
                return {"error": "Unauthorized or Class not found"}
            
    def get_student_enrollments(self, student_sql_id):
        enrolled_classes = []
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute("{CALL get_StudentEnrollments (?)}", (student_sql_id,))
                
                for row in cursor.fetchall():
                    session_dates = "Not Set"
                    if len(row) > 4 and row[4]:
                        session_dates = row[4]
                    enrolled_classes.append({
                        "id": row[0],
                        "name": row[1],
                        "trainer_name": f"{row[2]} {row[3]}",
                        "session_dates": session_dates
                    })
        except Exception as e:
            print(f"Error: {e}")
        return enrolled_classes
    
    def enroll_student(self, student_sql_id, class_id):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute("{CALL EnrollStudent (?, ?)}", (int(student_sql_id), int(class_id)))
                row = cursor.fetchone()
                if row is None:
                    return {"error": "Enrollment failed"}
                success = int(row[0]) == 1
                message = row[1]
                if success:
                    return {"success": True}
                return {"error": message or "Enrollment failed"}
        except Exception as e:
            print(f"SQL Error in EnrollStudent: {e}")
            return {"error": str(e)}

    def get_trainer_classes(self, trainer_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("{CALL get_TrainerClasses(?)}", (trainer_id,))
                
                classes = []
                for row in cursor.fetchall():
                    classes.append({
                        "id": row[0],
                        "name": row[1],
                        "trainer_name": f"{row[2]} {row[3]}",
                        "session_dates": row[4] if row[4] else "Not Set",
                        "exercises": row[5] if row[5] else ""
                    })
                return classes
            except Exception as e:
                print(f"Database error: {e}")
                return []
            
    def unenroll_student(self, student_id, class_id):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute('{CALL UnenrollStudent (?, ?)}', [student_id, class_id])
                conn.commit()
                return {"success": True}
        except Exception as e:
            print(f"SQL Error in unenroll_student: {e}")
            return {"error": str(e)}
            
    def update_class_session(self, class_id, session_date, exercises):
        if exercises is None: exercises = []
        if isinstance(exercises, str): exercises = [exercises]
        
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("{CALL sp_UpdateClassSession (?, ?)}", (int(class_id), session_date))
                session_id = cursor.fetchone()[0]

                exercise_id_map = {}  # name -> db exercise id

                for ex_data in exercises:
                    if isinstance(ex_data, dict):
                        ex_name = ex_data.get('name', '').strip()
                        ex_cat = ex_data.get('category', 'General').strip()
                    else:
                        ex_name = str(ex_data).strip()
                        ex_cat = 'General'

                    if not ex_name:
                        continue

                    cursor.execute("{CALL sp_UpsertExerciseLog (?, ?, ?)}", (session_id, ex_name, ex_cat))
                    result = cursor.fetchone()
                    if result:
                        exercise_id_map[ex_name.strip().lower()] = result[0] 

                conn.commit()
                return {"success": True, "session_id": session_id, "exercise_id_map": exercise_id_map}
            except Exception as e:
                conn.rollback()
                return {"error": str(e)}
            
    def get_class_details(self, class_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            query = "SELECT ID, Name FROM [Class] WHERE ID = ?"
            cursor.execute(query, (class_id,))
            row = cursor.fetchone()
            if row:
                return {"id": row[0], "name": row[1]}
            return None
        
    def get_class_sessions(self, class_id):
        sessions = {}
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL get_ClassSessions (?)}", (class_id,))
            for row in cursor.fetchall():
                s_id = row[0]
                if s_id not in sessions:
                    sessions[s_id] = {
                        "id": s_id,
                        "date": row[1].isoformat() if hasattr(row[1], 'isoformat') else str(row[1]),
                        "class_name": row[2],
                        "exercises": []
                    }
                if row[3]:
                    sessions[s_id]["exercises"].append({"name": row[3], "category": row[4]})
        return list(sessions.values())

    def delete_class_session(self, class_id, session_date):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL delete_ClassSession (?, ?)}", (int(class_id), session_date))
            result = cursor.fetchone()[0]
            conn.commit()
            return {"success": True} if result == 1 else {"error": "Session not found"}

    def update_session_date(self, session_id, new_date):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                sql = "UPDATE [Session] SET [Date] = ? WHERE ID = ?"
                cursor.execute(sql, (new_date, session_id))
                conn.commit()
                return {"success": True}
        except Exception as e:
            print(f"SQL Error in update_session_date: {e}")
            return {"error": str(e)}
        
    def log_exercise_to_session(self, exercise_id, session_id, is_pr=0):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO [Logs] (ExerciseID, SessionID, IsPr) VALUES (?, ?, ?)",
                    (int(exercise_id), int(session_id), int(is_pr))
                )
                conn.commit()
                return {"success": True}
        except Exception as e:
            return {"error": str(e)}
        
    def get_all_sessions_sql(self):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ID, ClassID, [Date] FROM [Session]")
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    sessions.append({
                        "id": row[0],
                        "class_id": row[1],
                        "date": str(row[2])
                    })
                return sessions
        except Exception as e:
            print(f"SQL Error: {e}")
            raise e

    def list_campus_workouts(self):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute("{CALL get_CampusWorkouts (?)}", (None,))
                rows = cursor.fetchall()

                workouts = []
                for row in rows:
                    date_val = row[0]
                    start_t = row[1]
                    end_t = row[2]

                    workouts.append({
                        "date": date_val.strftime("%Y-%m-%d") if date_val else "",
                        "duration_minutes": _minutes_between(start_t, end_t),
                    })
                return workouts
        except Exception as e:
            print(f"SQL Error in list_campus_workouts: {e}")
            return []
        
    def create_exercise(self, name, category="General"):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL upsert_Exercise (?, ?)}", (name.strip(), category.strip()))
            new_id = cursor.fetchone()[0]
            conn.commit()
            return {"id": new_id, "name": name.strip(), "category": category.strip()}
        
    def trainer_edit_set(self, session_id, exercise_id, set_num, weight, reps):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL upsert_Set(?, ?, ?, ?, ?)}", 
                        (exercise_id, session_id, set_num, weight, reps))
            conn.commit()

    def student_get_session_content(self, session_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL get_SessionDetails(?)}", (session_id,))
            rows = cursor.fetchall()
            
            results = {}
            for row in rows:
                ex_name = row.ExerciseName
                if ex_name not in results:
                    results[ex_name] = {"category": row.Category, "sets": []}
                results[ex_name]["sets"].append({
                    "number": row.SetNumber,
                    "weight": float(row.Weight) if row.Weight else 0,
                    "reps": row.Reps
                })
            return results
    
    def delete_exercise_from_session(self, session_id, exercise_id):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute("{CALL delete_ExerciseFromSession (?, ?)}", (int(session_id), int(exercise_id)))
                conn.commit()
                return {"success": True, "message": "Exercise and related sets deleted"}
        except Exception as e:
            return {"error": str(e)}

    def add_exercise_to_session(self, name, category, session_id, weight, reps, is_pr=0):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            sql = "{CALL add_exercise_and_info (?, ?, ?, ?, ?, ?, ?, ?, ?)}"
            params = (name, category, None, session_id, is_pr, 1, weight, reps)
            cursor.execute(sql, params)
            conn.commit()

    def add_exercise_to_logs(self, session_id, exercise_id):
        try:
            with pyodbc.connect(self.connection_string_database_copy) as conn:
                cursor = conn.cursor()
                cursor.execute("{CALL sp_AddExerciseToLogs (?, ?)}", (exercise_id, session_id))
                conn.commit()
            return True
        except Exception as e:
            print(f"SQL Error in add_exercise_to_logs: {e}")
            return False

    def get_session_content(self, session_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL get_SessionDetails(?)}", (session_id,))
            rows = cursor.fetchall()

            workout_data = {}
            for row in rows:
                ex_name = row.ExerciseName
                if ex_name not in workout_data:
                    workout_data[ex_name] = {
                        "category": row.Category,
                        "is_pr": bool(row.IsPr),
                        "sets": []
                    }

                if row.SetNumber is not None:
                    workout_data[ex_name]["sets"].append({
                        "number": row.SetNumber,
                        "weight": float(row.Weight) if row.Weight else 0,
                        "reps": row.Reps
                    })

            return workout_data

    def get_session_details_by_date(self, date_str, class_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            find_session_sql = "SELECT ID FROM [Session] WHERE Date = ? AND ClassID = ?"
            cursor.execute(find_session_sql, (date_str, class_id))
            row = cursor.fetchone()

            if not row:
                return []

            session_id = row[0]

            cursor.execute("{CALL get_SessionDetails (?)}", (session_id,))

            rows_out = []
            all_rows = cursor.fetchall()

            columns = []
            for col in cursor.description:
                columns.append(col[0])

            for row in all_rows:
                row_dict = {"session_id": session_id}

                for i in range(len(columns)):
                    row_dict[columns[i]] = row[i]

                rows_out.append(row_dict)

            return rows_out
    
    def viewer_list_sessions(self, student_id):
        result = []

        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            # Past sessions (ones which would actually allow me to edit exercises)
            cursor.execute("{CALL get_sessions_in_past (?)}", (int(student_id),))
            rows = cursor.fetchall()
            for row in rows:
                
                sid = int(row[0])
                cursor2 = conn.cursor()
                cursor2.execute("""
                    SELECT ID, [Date], StartTime, EndTime, [Location], Notes, Visibility
                    FROM [Session]
                    WHERE ID = ?
                """, (sid,))
                srow = cursor2.fetchone()
                if srow:
                    item = {
                        "id": int(srow[0]),
                        "date": srow[1].strftime("%Y-%m-%d") if srow[1] else "",
                        "start_time": srow[2].strftime("%H:%M") if srow[2] else "",
                        "end_time": srow[3].strftime("%H:%M") if srow[3] else "",
                        "location": srow[4] or "",
                        "notes": srow[5] or "",
                        "visibility": bool(srow[6]) if srow[6] is not None else False,
                        "is_future": False
                    }
                    result.append(item)

            # Here basically am adding future sessions
            cursor.execute("{CALL get_sessions_in_future (?)}", (int(student_id),))
            rows = cursor.fetchall()
            for row in rows:
                sid = int(row[0])
                cursor2 = conn.cursor()
                cursor2.execute("""
                    SELECT ID, [Date], StartTime, EndTime, [Location], Notes, Visibility
                    FROM [Session]
                    WHERE ID = ?
                """, (sid,))
                srow = cursor2.fetchone()
                if srow:
                    item = {
                        "id": int(srow[0]),
                        "date": srow[1].strftime("%Y-%m-%d") if srow[1] else "",
                        "start_time": srow[2].strftime("%H:%M") if srow[2] else "",
                        "end_time": srow[3].strftime("%H:%M") if srow[3] else "",
                        "location": srow[4] or "",
                        "notes": srow[5] or "",
                        "visibility": bool(srow[6]) if srow[6] is not None else False,
                        "is_future": True
                    }
                    result.append(item)

        n = len(result)
        i = 0
        while i < n:
            j = i + 1
            while j < n:
                a = result[i]
                b = result[j]
                swap = False

                if b["date"] > a["date"]:
                    swap = True
                elif b["date"] == a["date"] and b["start_time"] > a["start_time"]:
                    swap = True

                if swap:
                    temp = result[i]
                    result[i] = result[j]
                    result[j] = temp
                j += 1
            i += 1

        return result

    def viewer_get_session_full(self, student_id, session_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            cursor.execute("SELECT StudentID FROM [Session] WHERE ID = ?", (int(session_id),))
            owner = cursor.fetchone()
            if not owner or int(owner[0]) != int(student_id):
                raise RuntimeError("Unauthorized session access")

            cursor.execute("""
                SELECT ID, [Date], StartTime, EndTime, [Location], Notes, Visibility
                FROM [Session]
                WHERE ID = ?
            """, (int(session_id),))
            srow = cursor.fetchone()
            if not srow:
                raise RuntimeError("Session not found")

            session_obj = {
                "id": int(srow[0]),
                "date": srow[1].strftime("%Y-%m-%d") if srow[1] else "",
                "start_time": srow[2].strftime("%H:%M") if srow[2] else "",
                "end_time": srow[3].strftime("%H:%M") if srow[3] else "",
                "location": srow[4] or "",
                "notes": srow[5] or "",
                "visibility": bool(srow[6]) if srow[6] is not None else False,
                "items": []
            }

            cursor.execute("""
                SELECT e.ID AS ExerciseID, e.[Name], e.Category, l.IsPr, s.SetNumber, s.[Weight], s.Reps
                FROM Logs l
                JOIN Exercise e ON e.ID = l.ExerciseID
                JOIN [Set] s ON s.ExerciseID = e.ID
                WHERE l.SessionID = ?
                ORDER BY e.[Name], s.SetNumber
            """, (int(session_id),))

            rows = cursor.fetchall()
            for row in rows:
                session_obj["items"].append({
                    "exercise_id": int(row[0]),
                    "name": row[1],
                    "category": row[2],
                    "is_pr": bool(row[3]),
                    "set_number": int(row[4]),
                    "weight": float(row[5]) if row[5] is not None else None,
                    "reps": int(row[6]) if row[6] is not None else None
                })

            return session_obj
    
    def viewer_update_session(self, session_id, date=None, start_time=None, end_time=None, location=None, notes=None, visibility=None):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "{CALL update_session (?, ?, ?, ?, ?, ?, ?)}",
                (int(session_id), date, start_time, end_time, location, notes, visibility)
            )
            conn.commit()
        return {"success": True}
    
    def viewer_update_exercise(self, session_id, exercise_id, set_number, weight=None, reps=None):

        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "{CALL update_exercise (?, ?, ?, ?, ?)}",
                (int(session_id), int(exercise_id), int(set_number), weight, reps)
            )
            conn.commit()
        return {"success": True}