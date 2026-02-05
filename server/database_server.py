# Below are the list of sites we referred to or used to connect to the Microsoft
# https://medium.com/@gunkurnia/connecting-python-to-sql-server-a-comprehensive-guide-to-essential-libraries-1dfcba96fafb
# https://hex.tech/blog/connecting-python-sql-server/
# https://stackoverflow.com/questions/25670565/create-a-database-using-pyodbc
import pyodbc
import os
from dotenv import load_dotenv

load_dotenv()

print(pyodbc.drivers())

server = os.getenv("DB_SERVER")
#database = os.getenv("DB_NAME")
database_master = 'master'
database = os.getenv("DB_NAME")
database_copy = 'RoseShreddedNerdscopy'
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
                            CREATE DATABASE [RoseShreddedNerdscopy]
                            ON
                                    PRIMARY ( NAME=Data,
                                    FILENAME='/var/opt/mssql/data/RoseShreddedNerdscopy.mdf',
                                    SIZE=20MB,
                                    MAXSIZE=90MB,
                                    FILEGROWTH=12%)
                            LOG ON
                                    ( NAME=Log,
                                    FILENAME='/var/opt/mssql/data/RoseShreddedNerdscopy.ldf',
                                    SIZE=10MB,
                                    MAXSIZE=30MB,
                                    FILEGROWTH=17%)
                            COLLATE SQL_Latin1_General_Cp1_CI_AS
                        """
        cursor.execute(sql_command)
        conn.commit()

def destroy_db(connection_string):
    with pyodbc.connect(connection_string, autocommit=True) as conn:
        cursor = conn.cursor()
        # Note the ALTER DATABASE... SQL Line was found online from Google search Gemini AI results because no other source gave the answer clearly
        # What it essentially does is closes any other existing connections to the database to get rid of error "cannot drop...bc currently in USE"
        sql_command = """
                          ALTER DATABASE [RoseShreddedNerdscopy]
                          SET SINGLE_USER WITH ROLLBACK IMMEDIATE
                          DROP DATABASE [RoseShreddedNerdscopy]
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
                                [Weight] int NULL
                            )
                            CREATE TABLE [Student] (
                                ID int PRIMARY KEY REFERENCES Person(ID) NOT NULL
                            )
                            CREATE TABLE [Trainer] (
                                ID int PRIMARY KEY REFERENCES Person(ID) NOT NULL
                            )
                            CREATE TABLE [Session] (
                                ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
                                Date date NULL,
                                StudentID int REFERENCES Student(ID) NOT NULL
                            )
                            CREATE TABLE [Class] (
                                ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
                                Name varchar(50) NOT NULL
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
                                Duration int NULL
                            )
                            CREATE TABLE [Set] (
                                ExerciseID int REFERENCES Exercise(ID) NOT NULL,
                                SetNumber int NOT NULL,
                                Weight decimal(5,2) NULL,
                                Reps int NULL,
                                PRIMARY KEY (ExerciseID, SetNumber)
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
                            CREATE TABLE [Done] (
                                SectionID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
                                ClassID int REFERENCES Class(ID) NOT NULL
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

def seed_exercises(connection_string):
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
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        for name, category in exercises:
            cursor.execute(
                "IF NOT EXISTS (SELECT 1 FROM [Exercise] WHERE Name = ?) "
                "INSERT INTO [Exercise] (Name, Category) VALUES (?, ?)",
                (name, name, category)
            )
        conn.commit()

def create_stored_procedures(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
#Stored procedure to add a new student
        add_student_sql = """
                          CREATE OR ALTER PROCEDURE add_Student
                            (
                                @FName varchar(50),
                                @LName varchar(50),
                                @Username varchar(50),
                                @PasswordHash varchar(512),
                                @DOB date,
                                @Weight int,
                                @GeneratedID int OUTPUT
                            )
                          AS
                          BEGIN

                                IF @FName IS NULL OR @LName IS NULL OR @Username IS NULL OR @PasswordHash IS NULL
                                    OR (SELECT COUNT(Username) FROM Person WHERE Username = @Username) > 0
                                BEGIN;
                                    THROW 51000, 'Invalid Parameter(s): Given First Name, Last Name, Username, or Password are NULL or Username already exists.', 1
                                END
                          INSERT INTO [Person]
                                (FName, LName, Username, PasswordHash, DOB, Weight)
                          VALUES (@FName, @LName, @Username, @PasswordHash, @DOB, @Weight)

                          SET @GeneratedID = SCOPE_IDENTITY();

                          INSERT INTO [Student] (ID) VALUES (@GeneratedID);

                          END
                        """
        cursor.execute(add_student_sql)

        add_trainer_sql = """
                          CREATE OR ALTER PROCEDURE add_Trainer
                            (
                                @FName varchar(50),
                                @LName varchar(50),
                                @Username varchar(50),
                                @PasswordHash varchar(512),
                                @Weight int,
                                @GeneratedID int OUTPUT
                            )
                        AS
                        BEGIN
                            IF EXISTS (SELECT 1 FROM Person WHERE Username = @Username)
                            BEGIN;
                                THROW 51000, 'Username already exists.', 1;
                            END

                            INSERT INTO [Person] (FName, LName, Username, PasswordHash, [Weight])
                            VALUES (@FName, @LName, @Username, @PasswordHash, @Weight);

                            SET @GeneratedID = SCOPE_IDENTITY();

                            INSERT INTO [Trainer] (ID) VALUES (@GeneratedID);
                        END
                        """
        cursor.execute(add_trainer_sql)

#stored proc personal record (uses Achieves and Of) and upsert here is to insert or update, learned from geeksforgeeks and w3schools
        upsert_pr_sql = """
            CREATE OR ALTER PROCEDURE upsert_PersonalRecord 
                @StudentID    int,
                @ExerciseName varchar(50),
                @BestWeight   decimal(7,2),
                @BestReps     int
            AS
            BEGIN
                DECLARE @ExerciseID int
                SELECT @ExerciseID = ID FROM [Exercise] WHERE Name = @ExerciseName

                IF @ExerciseID IS NULL
                    RETURN

                DECLARE @ExistingPRID int
                SELECT @ExistingPRID = a.PersonalRecordID
                FROM [Achieves] a
                JOIN [Of] o ON a.PersonalRecordID = o.PersonalRecordID
                WHERE a.StudentID = @StudentID AND o.ExerciseID = @ExerciseID

                IF @ExistingPRID IS NOT NULL
                BEGIN
                    UPDATE [PersonalRecord]
                    SET Weight = @BestWeight,
                        Reps   = @BestReps,
                        Date   = CAST(GETUTCDATE() AS date)
                    WHERE ID = @ExistingPRID
                END
                ELSE
                BEGIN
                    INSERT INTO [PersonalRecord] (Weight, Reps, Date)
                    VALUES (@BestWeight, @BestReps, CAST(GETUTCDATE() AS date))

                    DECLARE @NewPRID int
                    SET @NewPRID = SCOPE_IDENTITY()

                    INSERT INTO [Achieves] (StudentID, PersonalRecordID)
                    VALUES (@StudentID, @NewPRID)

                    INSERT INTO [Of] (PersonalRecordID, ExerciseID)
                    VALUES (@NewPRID, @ExerciseID)
                END
            END
        """
        cursor.execute(upsert_pr_sql)

#stored proc to get all personal records for a student
        get_pr_sql = """
            CREATE OR ALTER PROCEDURE get_PersonalRecords
                @StudentID int
            AS
            BEGIN
                SELECT
                    e.Name       AS ExerciseName,
                    e.Category   AS ExerciseCategory,
                    pr.Weight    AS BestWeight,
                    pr.Reps      AS BestReps,
                    pr.Weight * (1.0 + pr.Reps / 30.0) AS Best1RM,
                    pr.Date      AS UpdatedAt
                FROM [PersonalRecord] pr
                JOIN [Achieves] a ON pr.ID = a.PersonalRecordID
                JOIN [Of] o ON pr.ID = o.PersonalRecordID
                JOIN [Exercise] e ON o.ExerciseID = e.ID
                WHERE a.StudentID = @StudentID
                ORDER BY e.Category, e.Name
            END
        """
        cursor.execute(get_pr_sql)

#stored proc for the big-3 leaderboard (squat, bench press, deadlift)
        leaderboard_sql = """
            CREATE OR ALTER PROCEDURE get_Big3Leaderboard
            AS
            BEGIN
                SELECT
                    p.Username,
                    p.FName,
                    p.LName,
                    SUM(pr.Weight * (1.0 + pr.Reps / 30.0)) AS Big3Total
                FROM [PersonalRecord] pr
                JOIN [Achieves] a ON pr.ID = a.PersonalRecordID
                JOIN [Of] o ON pr.ID = o.PersonalRecordID
                JOIN [Exercise] e ON o.ExerciseID = e.ID
                JOIN [Student] s ON a.StudentID = s.ID
                JOIN [Person] p ON s.ID = p.ID
                WHERE e.Name IN ('Squat', 'Bench Press', 'Deadlift')
                GROUP BY p.ID, p.Username, p.FName, p.LName
                ORDER BY Big3Total DESC
            END
        """
        cursor.execute(leaderboard_sql)
        conn.commit()


#create_db(connection_string_master)
#create_tables(connection_string_database_copy)
#seed_exercises(connection_string_database_copy)
#create_stored_procedures(connection_string_database_copy)
#destroy_db(connection_string_master)
