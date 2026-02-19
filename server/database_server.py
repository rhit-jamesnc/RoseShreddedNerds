# Below are the list of sites we referred to or used to connect to the Microsoft
# https://medium.com/@gunkurnia/connecting-python-to-sql-server-a-comprehensive-guide-to-essential-libraries-1dfcba96fafb
# https://hex.tech/blog/connecting-python-sql-server/
# https://stackoverflow.com/questions/25670565/create-a-database-using-pyodbc
import pyodbc
import os
from dotenv import load_dotenv
import stored_procedures

load_dotenv()

print(pyodbc.drivers())

server = os.getenv("DB_SERVER")
database_master = 'master'
database = os.getenv("DB_NAME")
database_copy = 'RoseShreddednerdscopy'
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = '{ODBC Driver 17 for SQL Server}'

connection_string_master = f'DRIVER={driver};SERVER={server};DATABASE={database_master};UID={username};PWD={password};'
connection_string_database = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
connection_string_database_copy = f'DRIVER={driver};SERVER={server};DATABASE={database_copy};UID={username};PWD={password};'

def create_db(connection_string):
    with pyodbc.connect(connection_string, autocommit=True) as conn:
        cursor = conn.cursor()
        sql_command = """
                            CREATE DATABASE [RoseShreddednerdscopy]
                            ON
                                    PRIMARY ( NAME=Data,
                                    FILENAME='/var/opt/mssql/data/RoseShreddednerdscopy.mdf',
                                    SIZE=20MB,
                                    MAXSIZE=90MB,
                                    FILEGROWTH=12%)
                            LOG ON
                                    ( NAME=Log,
                                    FILENAME='/var/opt/mssql/data/RoseShreddednerdscopy.ldf',
                                    SIZE=10MB,
                                    MAXSIZE=30MB,
                                    FILEGROWTH=17%)
                            COLLATE SQL_Latin1_General_Cp1_CI_AS
                        """
        cursor.execute(sql_command)
        conn.commit()

def add_owners(connection_string):
    with pyodbc.connect(connection_string, autocommit=True) as conn:
        cursor = conn.cursor()
        sql_command = """
                            CREATE USER [jamesnc] FROM LOGIN [jamesnc]; 
                            exec sp_addrolemember 'db_owner', 'jamesnc'; 

                            CREATE USER [kapilaar] FROM LOGIN [kapilaar]; 
                            exec sp_addrolemember 'db_owner', 'kapilaar'; 

                            CREATE USER [singha9] FROM LOGIN [singha9]; 
                            exec sp_addrolemember 'db_owner', 'singha9'; 
                        """
        cursor.execute(sql_command)
        conn.commit()

def destroy_db(connection_string):
    with pyodbc.connect(connection_string, autocommit=True) as conn:
        cursor = conn.cursor()
        # Note the ALTER DATABASE... SQL Line was found online from Google search Gemini AI results because no other source gave the answer clearly
        # What it essentially does is closes any other existing connections to the database to get rid of error "cannot drop...bc currently in USE"
        sql_command = """
                          ALTER DATABASE [RoseShreddednerdscopy]
                          SET SINGLE_USER WITH ROLLBACK IMMEDIATE
                          DROP DATABASE [RoseShreddednerdscopy]
                        """
        cursor.execute(sql_command)
        conn.commit()

def create_tables(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_command = """
                            CREATE TABLE [Person] (
                                ID int IDENTITY (1, 5) PRIMARY KEY NOT NULL,
                                FName varchar(50) NOT NULL,
                                LName varchar(50) NOT NULL,
                                Username varchar(50) NOT NULL,
                                PasswordHash varchar(512) NOT NULL,
                                DOB date NULL,
                                [Weight] int NULL,
                            )
                            CREATE TABLE [Student] (
                                ID int PRIMARY KEY REFERENCES Person(ID) NOT NULL
                            )
                            CREATE TABLE [Trainer] (
                                ID int PRIMARY KEY REFERENCES Person(ID) NOT NULL
                            )
                            CREATE TABLE [Class] (
                                ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
                                Name varchar(50) NOT NULL
                            )
                            CREATE TABLE [Session] (
                                ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
                                Date date NULL,
                                StartTime TIME(0) NULL,
                                EndTime TIME(0) NULL,
                                Location varchar(50) NULL,
                                Notes varchar(500) NULL,
                                Visibility bit,
                                StudentID int REFERENCES Student(ID) NOT NULL,
                                ClassID int REFERENCES Class(ID) NULL
                            )
                            CREATE TABLE [Teaches] (
                                TrainerID int REFERENCES Trainer(ID) NOT NULL,
                                ClassID int REFERENCES Class(ID) NOT NULL,
                                PRIMARY KEY (TrainerID, ClassID)
                            )
                            CREATE TABLE [Exercise] (
                                ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
                                Name varchar(50) NOT NULL,
                                Category varchar(50) NOT NULL,
                                Notes varchar(50),
                                Duration int NULL
                            )
                            CREATE TABLE [Set] (
                                ExerciseID int REFERENCES Exercise(ID) NOT NULL,
                                SessionID int REFERENCES [Session](ID) NOT NULL,
                                SetNumber int NOT NULL,
                                Weight decimal(5,2) NULL,
                                Reps int NULL,
                                PRIMARY KEY (ExerciseID, SetNumber, SessionID)
                            )
                            CREATE TABLE [Leaderboard] (
                                ID int IDENTITY PRIMARY KEY NOT NULL,
                                Name varchar(50) NOT NULL
                            )
                            CREATE TABLE [On] (
                                StudentID int REFERENCES Student(ID) NOT NULL,
                                LeaderboardID int REFERENCES Leaderboard(ID) NOT NULL,
                                ExerciseID int REFERENCES Exercise(ID) NOT NULL,
                                Rank int NULL,
                                PRIMARY KEY (StudentID, LeaderboardID, ExerciseID)
                            )
                            CREATE TABLE [Logs] (
                                ExerciseID int REFERENCES Exercise(ID) NOT NULL,
                                SessionID int REFERENCES Session(ID) NOT NULL,
                                IsPr bit NOT NULL,
                                PRIMARY KEY (ExerciseID, SessionID)
                            )
                            CREATE TABLE [HasA] (
                                StudentID int REFERENCES Student(ID) NOT NULL,
                                ClassID int REFERENCES Class(ID) NOT NULL,
                                PRIMARY KEY (StudentID, ClassID)
                            )

                            -- used geeksforgeeks.org for the default date value syntax
                            CREATE TABLE [PersonalRecord] (
                                ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
                                Weight decimal(7, 2) NOT NULL,
                                Reps int NULL,
                                Duration int NULL,
                                Date date NOT NULL DEFAULT CAST(GETUTCDATE() AS date)
                            )
                            CREATE TABLE [Achieves] (
                                StudentID int REFERENCES Student(ID) NOT NULL,
                                PersonalRecordID int REFERENCES PersonalRecord(ID) NOT NULL,
                                PRIMARY KEY (StudentID, PersonalRecordID)
                            )
                            CREATE TABLE [Of] (
                                PersonalRecordID int REFERENCES PersonalRecord(ID) NOT NULL,
                                ExerciseID int REFERENCES Exercise(ID) NOT NULL,
                                PRIMARY KEY (PersonalRecordID, ExerciseID)
                            )
                        """
        cursor.execute(sql_command)
        conn.commit()

def seed_data(connection_string):
    exercises = [
        ('Squat', 'strength'),
        ('Bench Press', 'strength'),
        ('Deadlift', 'strength'),
        ('Overhead Press', 'strength'),
        ('Barbell Row', 'strength'),
        ('Dumbell Curl', 'strength'),
        ('Pull-ups', 'strength'),
        ('Running', 'cardio'),
        ('Cycling', 'cardio'),
        ('Jogging', 'cardio'),
    ]

    persons = [
        ('John', 'Doe', 'jdoe', 'hash123', '1995-01-01', 180, 'Student'),
        ('Jane', 'Smith', 'jsmith', 'hash456', '1992-05-15', 150, 'Student'),
        ('Mike', 'Tyson', 'ironmike', 'hash789', '1966-06-30', 220, 'Trainer')
    ]

    classes = ['Powerlifting', 'Yoga Flow', 'HIIT Circuit']
    leaderboards = ['Strength Overall', 'Cardio Kings']

    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()

        for name, category in exercises:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Exercise] WHERE Name = ?) "
                "INSERT INTO [Exercise] (Name, Category) VALUES (?, ?)",
                (name, name, category)
            )

        for fname, lname, uname, phash, dob, weight, ptype in persons:
            cursor.execute("SELECT ID FROM [Person] WHERE Username = ?", (uname,))
            row = cursor.fetchone()
            if not row:
                cursor.execute(
                    "INSERT INTO [Person] (FName, LName, Username, PasswordHash, DOB, [Weight]) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (fname, lname, uname, phash, dob, weight)
                )
                cursor.execute("SELECT @@IDENTITY")
                new_id = cursor.fetchone()[0]
                if ptype == 'Student':
                    cursor.execute("INSERT INTO [Student] (ID) VALUES (?)", (new_id,))
                else:
                    cursor.execute("INSERT INTO [Trainer] (ID) VALUES (?)", (new_id,))

        for cname in classes:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Class] WHERE Name = ?) "
                "INSERT INTO [Class] (Name) VALUES (?)",
                (cname, cname)
            )

        for lname in leaderboards:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Leaderboard] WHERE Name = ?) "
                "INSERT INTO [Leaderboard] (Name) VALUES (?)",
                (lname, lname)
            )

        cursor.execute("SELECT TOP 1 ID FROM Student")
        sid_row = cursor.fetchone()
        sid = sid_row[0] if sid_row else None

        cursor.execute("SELECT TOP 1 ID FROM Class")
        cid_row = cursor.fetchone()
        cid = cid_row[0] if cid_row else None

        cursor.execute("SELECT TOP 1 ID FROM Trainer")
        tid_row = cursor.fetchone()
        tid = tid_row[0] if tid_row else None

        cursor.execute("SELECT TOP 1 ID FROM Exercise")
        eid_row = cursor.fetchone()
        eid = eid_row[0] if eid_row else None

        cursor.execute("SELECT TOP 1 ID FROM Leaderboard")
        lid_row = cursor.fetchone()
        lid = lid_row[0] if lid_row else None

        if sid and cid:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [HasA] WHERE StudentID = ? AND ClassID = ?) "
                "INSERT INTO [HasA] (StudentID, ClassID) VALUES (?, ?)",
                (sid, cid, sid, cid)
            )

        if tid and cid:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Teaches] WHERE TrainerID = ? AND ClassID = ?) "
                "INSERT INTO [Teaches] (TrainerID, ClassID) VALUES (?, ?)",
                (tid, cid, tid, cid)
            )

        cursor.execute(
            "INSERT INTO [PersonalRecord] (Weight, Reps, Date) VALUES (?, ?, GETUTCDATE())",
            (225.50, 5)
        )
        cursor.execute("SELECT @@IDENTITY")
        pr_id = cursor.fetchone()[0]

        if sid and pr_id:
            cursor.execute("INSERT INTO [Achieves] (StudentID, PersonalRecordID) VALUES (?, ?)", (sid, pr_id))
        
        if pr_id and eid:
            cursor.execute("INSERT INTO [Of] (PersonalRecordID, ExerciseID) VALUES (?, ?)", (pr_id, eid))

        if sid and cid and eid:
            cursor.execute(
                "INSERT INTO [Session] (Date, StudentID, ClassID) VALUES (GETDATE(), NULL, ?)",
                (cid,)
            )
            cursor.execute("SELECT @@IDENTITY")
            class_sess_id = cursor.fetchone()[0]

            cursor.execute(
                "INSERT INTO [Session] (Date, StudentID, ClassID) VALUES (GETDATE(), ?, NULL)",
                (sid,)
            )
            cursor.execute("SELECT @@IDENTITY")
            student_sess_id = cursor.fetchone()[0]

            for sess_id in [class_sess_id, student_sess_id]:
                cursor.execute(
                    "INSERT INTO [Logs] (ExerciseID, SessionID, IsPr) VALUES (?, ?, ?)",
                    (eid, sess_id, 1 if sess_id == student_sess_id else 0)
                )
            
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Set] WHERE ExerciseID = ? AND SetNumber = ?) "
                "INSERT INTO [Set] (ExerciseID, SetNumber, Weight, Reps) VALUES (?, ?, ?, ?)",
                (eid, 1, eid, 1, 225.50, 5)
            )

        if sid and lid and eid:
            cursor.execute(
                "INSERT INTO [On] (StudentID, LeaderboardID, ExerciseID, Rank) VALUES (?, ?, ?, ?)",
                (sid, lid, eid, 1)
            )

        conn.commit()


def create_stored_procedures(connection_string):
    
    stored_procedures.add_person(connection_string)
    stored_procedures.get_person_by_username(connection_string)
    stored_procedures.get_person_by_id(connection_string)
    stored_procedures.update_person(connection_string)
    stored_procedures.add_session(connection_string)
    stored_procedures.add_exercise_info(connection_string)
    stored_procedures.update_exercise_info(connection_string)
    stored_procedures.get_session_info(connection_string)
    stored_procedures.get_schedule_info(connection_string)
    stored_procedures.get_student_enrollments(connection_string)
    stored_procedures.unenroll_student(connection_string)
    stored_procedures.get_trainer_classes(connection_string)
    stored_procedures.get_session_in_class(connection_string)
    stored_procedures.delete_session_in_class(connection_string)
    stored_procedures.add_and_update_pr(connection_string)
    stored_procedures.get_pr_sql(connection_string)
    stored_procedures.get_big3_leaderboard(connection_string)
    stored_procedures.upsert_set(connection_string)
    stored_procedures.get_session_details(connection_string)
    stored_procedures.get_AllClasses(connection_string)

def create_and_setup_db():
    #create_db(connection_string_master)
    #create_tables(connection_string_database_copy)
    #seed_data(connection_string_database_copy)
    create_stored_procedures(connection_string_database_copy)

create_and_setup_db()
#destroy_db(connection_string_master)