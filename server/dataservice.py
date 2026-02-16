import re
import pyodbc
import os
import database_server
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone, date
from helpers_for_dataservice import now_iso, parse_iso_z, parse_date, epley_1rm, iso_week_of, iso_week_boundary

load_dotenv()

server = os.getenv("DB_SERVER")
database_master = 'master'
database = os.getenv("DB_NAME")
database_copy = os.getenv("DB_NAME_COPY", "RoseShreddedNerdsCopy")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = '{ODBC Driver 17 for SQL Server}'

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
    ...
    def __init__(self):
        self.server = os.getenv("DB_SERVER")
        self.database_master = 'master'
        self.database = os.getenv("DB_NAME")
        self.database_copy = 'RoseShreddedNerdsCopy'
        self.username = os.getenv("DB_USERNAME")
        self.password = os.getenv("DB_PASSWORD")
        self.driver = '{ODBC Driver 17 for SQL Server}'

        self.connection_string_master = f'DRIVER={self.driver};SERVER={self.server};DATABASE={self.database_master};UID={self.username};PWD={self.password};'
        self.connection_string_database = f'DRIVER={self.driver};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password};'
        self.connection_string_database_copy = f'DRIVER={self.driver};SERVER={self.server};DATABASE={self.database_copy};UID={self.username};PWD={self.password};'

        self.user = None
    
    def _user(self):
        return self.user
    
    def create_user(self, first_name, last_name, username, password_hash, dob=None, weight=None, role='Student'):
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
            print(user_id)
            conn.commit()
        
        print("User id", user_id)
        self.user = self.get_user_by_id(user_id)
        
    
    def get_user_by_username(self, username):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            cursor.execute("{CALL get_Person_by_Username (?)}", username)

            row = cursor.fetchone()
            if not row:
                return None
            
            user_searched = {
                "ID": row[0],
                "FName": row[1],
                "LName": row[2],
                "Username": row[3],
                "PasswordHash": row[4],
                "DOB": row[5],
                "Weight": row[6]
            }

            return user_searched
    
    def get_user_by_id(self, user_id):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()

            print("Calling get_person", user_id)
            cursor.execute("{CALL get_Person_by_ID (?)}", user_id)

            row = cursor.fetchone()
            if not row:
                return None
            
            user_searched = {
                "ID": row[0],
                "FName": row[1],
                "LName": row[2],
                "Username": row[3],
                "PasswordHash": row[4],
                "DOB": row[5],
                "Weight": row[6]
            }

            return user_searched
    
    def update_user(self, ID, FName=None, LName=None, Username=None, PasswordHash=None, DOB=None, Weight=None):
        with pyodbc.connect(self.connection_string_database_copy) as conn:
            cursor = conn.cursor()
            cursor.execute("{CALL update_person_profile (?, ?, ?, ?, ?, ?, ?)}", ID, FName, LName, Username, PasswordHash, DOB, Weight)
            conn.commit()
        
        self.user = self.get_user_by_id(ID)
    
    def login(self, ID):
        self.user = self.get_user_by_id(ID)
    def logout(self):
        self.user = None
    
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

                EXEC add_session ?, ?, ?, ?, ?, ?, ?, @GeneratedID OUTPUT;

                SELECT @GeneratedID;
                """, Date, StartTime, EndTime, Location, Notes, Visibility, ID)
        
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

    def list_exercises(self):
        items = []
        i = 1
        for (name, category) in WEIGHT_EXERCISES:
            items.append({
                "id": i,             # frontend needs an id; this is just local
                "name": name,
                "category": category
            })
            i += 1
        return items
    
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
