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
database_copy = 'RoseShreddedNerdsCopy'
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
                            CREATE DATABASE [RoseShreddedNerdsCopy]
                            ON
                                    PRIMARY ( NAME=Data,
                                    FILENAME='/var/opt/mssql/data/RoseShreddedNerdsCopy.mdf',
                                    SIZE=20MB,
                                    MAXSIZE=90MB,
                                    FILEGROWTH=12%)
                            LOG ON
                                    ( NAME=Log,
                                    FILENAME='/var/opt/mssql/data/RoseShreddedNerdsCopy.ldf',
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
                          ALTER DATABASE [RoseShreddedNerdsCopy]
                          SET SINGLE_USER WITH ROLLBACK IMMEDIATE
                          DROP DATABASE [RoseShreddedNerdsCopy]
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
                        """
        cursor.execute(sql_command)
        conn.commit()

def create_stored_procedures(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        # Note the ALTER DATABASE... SQL Line was found online from Google search Gemini AI results because no other source gave the answer clearly
        # What it essentially does is closes any other existing connections to the database to get rid of error "cannot drop...bc currently in USE"
        sql_command = """
                          CREATE OR ALTER PROCEDURE add_Student
                            (
                                @FName varchar(50),
                                @LName varchar(50),
                                @Username varchar(50),
                                @PasswordHash varchar(50),
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

                          END
                        """
        cursor.execute(sql_command)
        conn.commit()


#create_db(connection_string_master)
#create_tables(connection_string_database_copy)
#create_stored_procedures(connection_string_database_copy)
#destroy_db(connection_string_master)
