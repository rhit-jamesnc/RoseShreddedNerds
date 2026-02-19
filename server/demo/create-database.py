import pyodbc
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
import stored_procedures
import import_csv


_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_SERVER_DIR = os.path.dirname(os.path.dirname(_BASE_DIR)) 
load_dotenv(os.path.join(_SERVER_DIR, ".env"), override=True)

server = os.getenv("DB_SERVER")
database_master = 'master'
database = os.getenv("DB_NAME")
database_copy = os.getenv("DB_NAME_COPY", "RoseShreddednerdscopy")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = '{ODBC Driver 17 for SQL Server}'

connection_string_master = f'DRIVER={driver};SERVER={server};DATABASE={database_master};UID={username};PWD={password};'
connection_string_database = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
connection_string_database_copy = f'DRIVER={driver};SERVER={server};DATABASE={database_copy};UID={username};PWD={password};'

def create_db(connection_string):

    print(f"\nCreating [{database_copy}] on {server} …")

    with pyodbc.connect(connection_string, autocommit=True) as conn:
        cursor = conn.cursor()
        sql_command = f"""
                            CREATE DATABASE [{database_copy}]
                            ON
                                    PRIMARY ( NAME=Data,
                                    FILENAME='/var/opt/mssql/data/{database_copy}.mdf',
                                    SIZE=20MB,
                                    MAXSIZE=90MB,
                                    FILEGROWTH=12%)
                            LOG ON
                                    ( NAME=Log,
                                    FILENAME='/var/opt/mssql/data/{database_copy}.ldf',
                                    SIZE=10MB,
                                    MAXSIZE=30MB,
                                    FILEGROWTH=17%)
                            COLLATE SQL_Latin1_General_Cp1_CI_AS
                        """
        cursor.execute(sql_command)
        conn.commit()

def destroy_db(connection_string):

    print(f"\nDeleting [{database_copy}] on {server} …")

    with pyodbc.connect(connection_string, autocommit=True) as conn:
        cursor = conn.cursor()
        sql_command = f"""
                          ALTER DATABASE [{database_copy}]
                          SET SINGLE_USER WITH ROLLBACK IMMEDIATE
                          DROP DATABASE [{database_copy}]
                        """
        cursor.execute(sql_command)
        conn.commit()

def create_tables(connection_string):

    print(f"\nCreating tables for [{database_copy}] on {server} …")

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
                                StudentID int REFERENCES Student(ID) NULL,
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

def create_stored_procedures(connection_string):
    
    print(f"\nCreating stored procedures for [{database_copy}] on {server} …")
    
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
    stored_procedures.enroll_student(connection_string)
    stored_procedures.unenroll_student(connection_string)
    stored_procedures.get_trainer_classes(connection_string)
    stored_procedures.get_session_in_class(connection_string)
    stored_procedures.delete_class_session(connection_string)
    stored_procedures.add_and_update_pr(connection_string)
    stored_procedures.get_pr_sql(connection_string)
    stored_procedures.insert_pr_history(connection_string)
    stored_procedures.get_pr_progression(connection_string)
    stored_procedures.check_exercise_exists(connection_string)
    stored_procedures.get_exercise_name(connection_string)
    stored_procedures.get_exercise_leaderboard(connection_string)
    stored_procedures.get_big3_leaderboard(connection_string)
    stored_procedures.get_campus_workouts(connection_string)
    stored_procedures.upsert_set(connection_string)
    stored_procedures.get_session_details(connection_string)
    stored_procedures.get_person_id_by_username(connection_string)
    stored_procedures.get_AllClasses(connection_string)
    stored_procedures.sp_CreateClass(connection_string)
    stored_procedures.sp_UpdateClassSession(connection_string)
    stored_procedures.sp_UpsertExerciseLog(connection_string)
    stored_procedures.sp_DeleteClass(connection_string)
    stored_procedures.enroll_student(connection_string)

def create_and_setup_db():
    create_db(connection_string_master)
    create_tables(connection_string_database_copy)
    create_stored_procedures(connection_string_database_copy)
    import_csv.run()

create_and_setup_db()
# destroy_db(connection_string_master)