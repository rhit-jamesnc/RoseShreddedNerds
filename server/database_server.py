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
database_copy2 = 'RoseShreddedNerdscopy2'
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
driver = '{ODBC Driver 17 for SQL Server}'

connection_string_master = f'DRIVER={driver};SERVER={server};DATABASE={database_master};UID={username};PWD={password};'
connection_string_database = f'DRIVER={driver};SERVER={server};DATABASE={database};UID={username};PWD={password};'
connection_string_database_copy2 = f'DRIVER={driver};SERVER={server};DATABASE={database_copy2};UID={username};PWD={password};'

def create_db(connection_string):
    with pyodbc.connect(connection_string, autocommit=True) as conn:
        cursor = conn.cursor()
        sql_command = """
                            CREATE DATABASE [RoseShreddedNerdscopy2]
                            ON
                                    PRIMARY ( NAME=Data,
                                    FILENAME='/var/opt/mssql/data/RoseShreddedNerdscopy2.mdf',
                                    SIZE=20MB,
                                    MAXSIZE=90MB,
                                    FILEGROWTH=12%)
                            LOG ON
                                    ( NAME=Log,
                                    FILENAME='/var/opt/mssql/data/RoseShreddedNerdscopy2.ldf',
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
                            GO

                            CREATE USER [kapilaar] FROM LOGIN [kapilaar]; 
                            exec sp_addrolemember 'db_owner', 'kapilaar'; 
                            GO

                            CREATE USER [singha9] FROM LOGIN [singha9]; 
                            exec sp_addrolemember 'db_owner', 'singha9'; 
                            GO
                        """
        cursor.execute(sql_command)
        conn.commit()

def destroy_db(connection_string):
    with pyodbc.connect(connection_string, autocommit=True) as conn:
        cursor = conn.cursor()
        # Note the ALTER DATABASE... SQL Line was found online from Google search Gemini AI results because no other source gave the answer clearly
        # What it essentially does is closes any other existing connections to the database to get rid of error "cannot drop...bc currently in USE"
        sql_command = """
                          ALTER DATABASE [RoseShreddedNerdscopy2]
                          SET SINGLE_USER WITH ROLLBACK IMMEDIATE
                          DROP DATABASE [RoseShreddedNerdscopy2]
                        """
        cursor.execute(sql_command)
        conn.commit()

def create_tables(connection_string):
    tables = [
        """
        CREATE TABLE [Person] (
            ID int IDENTITY (1, 5) PRIMARY KEY NOT NULL,
            FName varchar(50) NOT NULL,
            LName varchar(50) NOT NULL,
            Username varchar(50) NOT NULL,
            PasswordHash varchar(512) NOT NULL,
            DOB date NULL,
            [Weight] int NULL
        )
        """,
        "CREATE TABLE [Student] (ID int PRIMARY KEY REFERENCES Person(ID) NOT NULL)",
        "CREATE TABLE [Trainer] (ID int PRIMARY KEY REFERENCES Person(ID) NOT NULL)",
        """
        CREATE TABLE [Class] (
            ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
            Name varchar(50) NOT NULL
        )
        """,
        """
        CREATE TABLE [Session] (
            ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
            Date date NULL,
            StudentID int REFERENCES Student(ID) NULL,
            ClassID int REFERENCES Class(ID) NULL
        )
        """,
        """
        CREATE TABLE [Teaches] (
            TrainerID int REFERENCES Trainer(ID) NOT NULL,
            ClassID int REFERENCES Class(ID) NOT NULL,
            PRIMARY KEY (TrainerID, ClassID)
        )
        """,
        """
        CREATE TABLE [Exercise] (
            ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
            Name varchar(50) NOT NULL,
            Category varchar(50) NOT NULL,
            Duration int NULL
        )
        """,
        """
        CREATE TABLE [Set] (
            ExerciseID int REFERENCES Exercise(ID) NOT NULL,
            SessionID int REFERENCES [Session](ID) NOT NULL,
            SetNumber int NOT NULL,
            Weight decimal(5,2) NULL,
            Reps int NULL,
            PRIMARY KEY (ExerciseID, SetNumber, SessionID)
        )
        """,
        "CREATE TABLE [Leaderboard] (ID int IDENTITY PRIMARY KEY NOT NULL, Name varchar(50) NOT NULL)",
        """
        CREATE TABLE [On] (
            StudentID int REFERENCES Student(ID) NOT NULL,
            LeaderboardID int REFERENCES Leaderboard(ID) NOT NULL,
            ExerciseID int REFERENCES Exercise(ID) NOT NULL,
            Rank int NULL,
            PRIMARY KEY (StudentID, LeaderboardID, ExerciseID)
        )
        """,
        """
        CREATE TABLE [Logs] (
            ExerciseID int REFERENCES Exercise(ID) NOT NULL,
            SessionID int REFERENCES Session(ID) NOT NULL,
            IsPr bit NOT NULL,
            PRIMARY KEY (ExerciseID, SessionID)
        )
        """,
        """
        CREATE TABLE [HasA] (
            StudentID int REFERENCES Student(ID) NOT NULL,
            ClassID int REFERENCES Class(ID) NOT NULL,
            PRIMARY KEY (StudentID, ClassID)
        )
        """,
        """
        CREATE TABLE [PersonalRecord] (
            ID int IDENTITY (1, 1) PRIMARY KEY NOT NULL,
            Weight decimal(7, 2) NOT NULL,
            Reps int NULL,
            Duration int NULL,
            Date date NOT NULL DEFAULT CAST(GETUTCDATE() AS date)
        )
        """,
        """
        CREATE TABLE [Achieves] (
            StudentID int REFERENCES Student(ID) NOT NULL,
            PersonalRecordID int REFERENCES PersonalRecord(ID) NOT NULL,
            PRIMARY KEY (StudentID, PersonalRecordID)
        )
        """,
        """
        CREATE TABLE [Of] (
            PersonalRecordID int REFERENCES PersonalRecord(ID) NOT NULL,
            ExerciseID int REFERENCES Exercise(ID) NOT NULL,
            PRIMARY KEY (PersonalRecordID, ExerciseID)
        )
        """
    ]

    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        for table_sql in tables:
            try:
                cursor.execute(table_sql)
            except pyodbc.Error as e:
                print(f"Error creating table: {e}")
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
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        
        # Stored procedure to add a new person. Can be either a Student or a Trainer
        add_person_sql = """
                          CREATE OR ALTER PROCEDURE add_Person
                            (
                                @FName varchar(50),
                                @LName varchar(50),
                                @Username varchar(50),
                                @PasswordHash varchar(512),
                                @DOB date,
                                @Weight int,
                                @PersonType varchar(20),
                                @GeneratedID int OUTPUT
                            )
                          AS
                          BEGIN
                                SET NOCOUNT ON;
                                IF @FName IS NULL OR @LName IS NULL OR @Username IS NULL OR @PasswordHash IS NULL
                                    OR (SELECT COUNT(Username) FROM Person WHERE Username = @Username) > 0
                                BEGIN;
                                    THROW 51000, 'Invalid Parameter(s): Given First Name, Last Name, Username, or Password are NULL or Username already exists.', 1
                                END
                                IF @PersonType <> 'Student' AND @PersonType <> 'Trainer'
                                BEGIN;
                                    THROW 51001, 'Invalid Parameter: The Person being created is neither a Student nor Teacher.', 2
                                END

                            INSERT INTO [Person]
                                    (FName, LName, Username, PasswordHash, DOB, Weight)
                            VALUES (@FName, @LName, @Username, @PasswordHash, @DOB, @Weight)

                            SET @GeneratedID = SCOPE_IDENTITY();
                            
                            IF @PersonType = 'Student'
                            BEGIN;
                                INSERT INTO [Student] (ID) VALUES (@GeneratedID);
                            END
                            ELSE
                            BEGIN;
                                INSERT INTO [Trainer] (ID) VALUES (@GeneratedID);
                            END
                          END
                        """
        cursor.execute(add_person_sql)

        # Stored procedure to update user information for profile or login features and functionality
        update_person_profile = """
                                 CREATE OR ALTER PROCEDURE update_person_profile
                                    (
                                        @PersonID int,
                                        @FName varchar(50) = NULL,
                                        @LName varchar(50) = NULL,
                                        @Username varchar(50) = NULL,
                                        @PasswordHash varchar(512) = NULL,
                                        @DOB date = NULL,
                                        @Weight int = NULL
                                    )
                                 AS
                                 BEGIN
                                    IF @PersonID IS NULL OR (SELECT COUNT(*) FROM Person WHERE ID = @PersonID) = 0
                                    BEGIN;
                                        THROW 51000, 'Error: Missing Person', 1
                                    END

                                    IF @FName IS NULL SET @FName = (SELECT FName FROM Person WHERE ID = @PersonID)
                                    IF @LName IS NULL SET @LName = (SELECT LName FROM Person WHERE ID = @PersonID)
                                    IF @Username IS NULL SET @Username = (SELECT Username FROM Person WHERE ID = @PersonID)
                                    IF @PasswordHash IS NULL SET @PasswordHash = (SELECT PasswordHash FROM Person WHERE ID = @PersonID)
                                    IF @DOB IS NULL SET @DOB = (SELECT DOB FROM Person WHERE ID = @PersonID)
                                    IF @Weight IS NULL SET @Weight = (SELECT Weight FROM Person WHERE ID = @PersonID)

                                    UPDATE Person
                                    SET FName = @FName,
                                        LName = @LName,
                                        Username = @Username,
                                        PasswordHash = @PasswordHash,
                                        DOB = @DOB,
                                        Weight = @Weight
                                 END

                                """
        cursor.execute(update_person_profile)

        # Stored procedure to add a workout or class session
        add_session_sql = """
                            CREATE OR ALTER PROCEDURE add_session
                            (
                                @Date date = NULL,
                                @ClassID int = NULL,
                                @StudentID int = NULL,
                                @GeneratedID int OUTPUT
                            )
                        AS
                        BEGIN
                            IF @ClassID IS NOT NULL AND (SELECT COUNT(*) FROM Class WHERE ID = @ClassID) = 0
                            BEGIN;
                                THROW 51002, 'Error: Class not found.', 1
                            END
                            
                            IF @Date IS NULL SET @Date = CAST(GETDATE() AS DATE)

                            INSERT INTO [Session] (Date, ClassID, StudentID) 
                            VALUES (@Date, @ClassID, @StudentID)

                            SET @GeneratedID = SCOPE_IDENTITY()
                        END
                          """
        cursor.execute(add_session_sql)

        # Stored procedure to add an exercise and log it for the session with information related to the exercise
        add_exercise_and_related_info_sql = """
                                            CREATE OR ALTER PROCEDURE add_exercise_and_info
                                                (
                                                    @Name varchar(50),
                                                    @Category varchar(50),
                                                    @Duration int = NULL,
                                                    @SessionID int,
                                                    @IsPr bit,
                                                    @SetNumber int,
                                                    @Weight decimal(5, 2),
                                                    @Reps int
                                                )
                                            AS
                                            BEGIN
                                                SET NOCOUNT ON;
                                                DECLARE @ExID int;

                                                SELECT @ExID = ID FROM Exercise WHERE Name = @Name;
                                                IF @ExID IS NULL
                                                BEGIN
                                                    INSERT INTO Exercise (Name, Category, Duration) VALUES (@Name, @Category, @Duration);
                                                    SET @ExID = SCOPE_IDENTITY();
                                                END

                                                IF NOT EXISTS (SELECT 1 FROM Logs WHERE SessionID = @SessionID AND ExerciseID = @ExID)
                                                BEGIN
                                                    INSERT INTO Logs (SessionID, ExerciseID, IsPr) VALUES (@SessionID, @ExID, @IsPr);
                                                END

                                                INSERT INTO [Set] (ExerciseID, SessionID, SetNumber, Weight, Reps)
                                                VALUES (@ExID, @SessionID, @SetNumber, @Weight, @Reps);
                                            END
                                        """
        
        cursor.execute(add_exercise_and_related_info_sql)
        conn.commit()



        get_StudentEnrollments = """
            CREATE OR ALTER PROCEDURE get_StudentEnrollments
                @StudentID INT
            AS
            BEGIN
                SET NOCOUNT ON;
                SELECT c.ID, c.Name, p.FName, p.LName, 
                        (
                            SELECT STRING_AGG(CAST(s.Date AS VARCHAR), ', ') 
                            FROM [Session] s 
                            WHERE s.ClassID = c.ID
                        ) AS session_dates
                FROM [HasA] h
                JOIN [Class] c ON h.ClassID = c.ID
                JOIN [Teaches] t ON c.ID = t.ClassID
                JOIN [Person] p ON t.TrainerID = p.ID
                WHERE h.StudentID = @StudentID;
            END
        """
        cursor.execute(get_StudentEnrollments)
        conn.commit()

        get_trainer_classes_sql = """
            CREATE OR ALTER PROCEDURE get_TrainerClasses
                @TrainerID INT
            AS
            BEGIN
                SET NOCOUNT ON;
                SELECT c.ID, c.Name, p.FName, p.LName,
                    (SELECT STRING_AGG(CAST(Date AS VARCHAR), ', ') 
                     FROM (SELECT DISTINCT Date FROM [Session] WHERE ClassID = c.ID) AS Dates
                    ) AS AllSessionDates
                FROM [Class] c
                JOIN [Teaches] t ON c.ID = t.ClassID
                JOIN [Person] p ON t.TrainerID = p.ID
                WHERE t.TrainerID = @TrainerID;
            END
        """
        cursor.execute(get_trainer_classes_sql)

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

        #stored proc for unenrolling a student from a class
        unenrollStudent_sql = """
            CREATE OR ALTER PROCEDURE UnenrollStudent
                @StudentID INT, 
                @ClassID INT
            AS
            BEGIN
                SET NOCOUNT ON;

                DELETE FROM [HasA] 
                WHERE StudentID = @StudentID AND ClassID = @ClassID;
            END
        """
        cursor.execute(unenrollStudent_sql)
        conn.commit()

        #stored proc for getting a session in a class
        get_session_sql = """
            CREATE OR ALTER PROCEDURE get_ClassSessions
                @ClassID INT
            AS
            BEGIN
                SET NOCOUNT ON;
                SELECT 
                    s.ID, 
                    s.Date, 
                    c.Name AS ClassName
                FROM [Session] s
                JOIN [Class] c ON s.ClassID = c.ID
                WHERE s.ClassID = @ClassID
                ORDER BY s.Date DESC;
            END
        """
        cursor.execute(get_session_sql)
        conn.commit()

        #stored proc for deleting a session in a class
        delete_session_sql = """
            CREATE OR ALTER PROCEDURE delete_Session
                @SessionID INT
            AS
            BEGIN
                SET NOCOUNT ON;
                DELETE FROM [Logs] WHERE SessionID = @SessionID;
                DELETE FROM [Session] WHERE ID = @SessionID;
            END
        """
        cursor.execute(delete_session_sql)
        conn.commit()

        upsert_set_sql = """
            CREATE OR ALTER PROCEDURE upsert_Set
                @ExerciseID INT,
                @SessionID INT,
                @SetNumber INT,
                @Weight DECIMAL(5,2),
                @Reps INT
            AS
            BEGIN
                SET NOCOUNT ON;

                IF EXISTS (
                    SELECT 1 FROM [Set] 
                    WHERE SessionID = @SessionID 
                    AND ExerciseID = @ExerciseID 
                    AND SetNumber = @SetNumber
                )
                BEGIN
                    UPDATE [Set]
                    SET Weight = @Weight,
                        Reps = @Reps
                    WHERE SessionID = @SessionID 
                    AND ExerciseID = @ExerciseID 
                    AND SetNumber = @SetNumber;
                END
                ELSE
                BEGIN
                    INSERT INTO [Set] (ExerciseID, SessionID, SetNumber, Weight, Reps)
                    VALUES (@ExerciseID, @SessionID, @SetNumber, @Weight, @Reps);
                END
            END
        """
        cursor.execute(upsert_set_sql)
        conn.commit()

        get_session_details_sql = """
            CREATE OR ALTER PROCEDURE get_SessionDetails
                @SessionID int
            AS
            BEGIN
                SET NOCOUNT ON;
                SELECT 
                    e.[Name] AS ExerciseName,
                    e.Category,
                    s.SetNumber,
                    s.Weight,
                    s.Reps,
                    l.IsPr
                FROM [Logs] l
                JOIN [Exercise] e 
                    ON l.ExerciseID = e.ID
                LEFT JOIN [Set] s 
                    ON s.ExerciseID = l.ExerciseID 
                    AND s.SessionID = l.SessionID
                WHERE l.SessionID = @SessionID
                ORDER BY e.[Name], s.SetNumber
            END
        """
        cursor.execute(get_session_details_sql)
        conn.commit()

        create_trainer_sql = """
                CREATE OR ALTER PROCEDURE sp_CreateTrainer
                    @FName NVARCHAR(50),
                    @LName NVARCHAR(50),
                    @Username NVARCHAR(50),
                    @PasswordHash NVARCHAR(255),
                    @Weight FLOAT
                AS
                BEGIN
                    SET NOCOUNT ON;
                    DECLARE @PersonID INT;
                    INSERT INTO [Person] (FName, LName, Username, PasswordHash, Weight)
                    VALUES (@FName, @LName, @Username, @PasswordHash, @Weight);
                    SET @PersonID = SCOPE_IDENTITY();
                    INSERT INTO [Trainer] (ID) VALUES (@PersonID);
                    SELECT @PersonID AS PersonID;
                END
            """
        cursor.execute(create_trainer_sql)
        conn.commit()

        create_class_sql = """
                CREATE OR ALTER PROCEDURE sp_CreateClass
                    @TrainerID INT,
                    @ClassName NVARCHAR(100)
                AS
                BEGIN
                    SET NOCOUNT ON;
                    DECLARE @ClassID INT;
                    INSERT INTO [Class] (Name) VALUES (@ClassName);
                    SET @ClassID = SCOPE_IDENTITY();
                    INSERT INTO [Teaches] (TrainerID, ClassID) VALUES (@TrainerID, @ClassID);
                    SELECT @ClassID AS ClassID;
                END
            """
        cursor.execute(create_class_sql)
        conn.commit()

        delete_class_sql = """
                CREATE OR ALTER PROCEDURE sp_DeleteClass
                    @TrainerID INT,
                    @ClassID INT
                AS
                BEGIN
                    SET NOCOUNT ON;
                    IF EXISTS (SELECT 1 FROM [Teaches] WHERE TrainerID = @TrainerID AND ClassID = @ClassID)
                    BEGIN
                        DECLARE @SessionIDs TABLE (ID INT);
                        INSERT INTO @SessionIDs SELECT ID FROM [Session] WHERE ClassID = @ClassID;
                        DELETE FROM [Logs] WHERE SessionID IN (SELECT ID FROM @SessionIDs);
                        DELETE FROM [Set] WHERE SessionID IN (SELECT ID FROM @SessionIDs);
                        DELETE FROM [Session] WHERE ClassID = @ClassID;
                        DELETE FROM [HasA] WHERE ClassID = @ClassID;
                        DELETE FROM [Teaches] WHERE ClassID = @ClassID;
                        DELETE FROM [Class] WHERE ID = @ClassID;
                        SELECT 1 AS Success;
                    END
                    ELSE
                    BEGIN
                        SELECT 0 AS Success;
                    END
                END
            """
        cursor.execute(delete_class_sql)
        conn.commit()

        upsert_session_exercise_sql = """
                CREATE OR ALTER PROCEDURE sp_UpsertSessionExercise
                    @ClassID INT,
                    @SessionDate DATE,
                    @ExName NVARCHAR(100),
                    @ExCategory NVARCHAR(50)
                AS
                BEGIN
                    SET NOCOUNT ON;
                    DECLARE @SessionID INT;
                    DECLARE @ExerciseID INT;

                    SELECT @SessionID = ID FROM [Session] WHERE ClassID = @ClassID AND [Date] = @SessionDate;
                    IF @SessionID IS NULL
                    BEGIN
                        INSERT INTO [Session] ([Date], ClassID) VALUES (@SessionDate, @ClassID);
                        SET @SessionID = SCOPE_IDENTITY();
                    END

                    SELECT @ExerciseID = ID FROM [Exercise] WHERE [Name] = @ExName;
                    IF @ExerciseID IS NULL
                    BEGIN
                        INSERT INTO [Exercise] ([Name], [Category]) VALUES (@ExName, @ExCategory);
                        SET @ExerciseID = SCOPE_IDENTITY();
                    END

                    IF NOT EXISTS (SELECT 1 FROM [Logs] WHERE ExerciseID = @ExerciseID AND SessionID = @SessionID)
                    BEGIN
                        INSERT INTO [Logs] (ExerciseID, SessionID, IsPr) VALUES (@ExerciseID, @SessionID, 0);
                    END

                    SELECT @SessionID AS SessionID, @ExerciseID AS ExerciseID;
                END
            """

        cursor.execute(upsert_session_exercise_sql)
        conn.commit()

        upsert_exercise_log_sql = """
                CREATE OR ALTER PROCEDURE sp_UpsertExerciseLog
                    @SessionID INT,
                    @ExName NVARCHAR(100),
                    @ExCategory NVARCHAR(50)
                AS
                BEGIN
                    SET NOCOUNT ON;
                    DECLARE @ExerciseID INT;

                    SELECT @ExerciseID = ID FROM [Exercise] WHERE [Name] = @ExName;

                    IF @ExerciseID IS NULL
                    BEGIN
                        INSERT INTO [Exercise] ([Name], [Category]) 
                        VALUES (@ExName, @ExCategory);
                        SET @ExerciseID = SCOPE_IDENTITY();
                    END

                    IF NOT EXISTS (SELECT 1 FROM [Logs] WHERE ExerciseID = @ExerciseID AND SessionID = @SessionID)
                    BEGIN
                        INSERT INTO [Logs] (ExerciseID, SessionID, IsPr) 
                        VALUES (@ExerciseID, @SessionID, 0);
                    END

                    SELECT @ExerciseID AS ExerciseID;
                END
            """
        cursor.execute(upsert_exercise_log_sql)
        conn.commit()

        get_class_sessions_sql = """
            CREATE OR ALTER PROCEDURE get_ClassSessions
                @ClassID INT
            AS
            BEGIN
                SET NOCOUNT ON;
                SELECT 
                    s.ID, 
                    s.[Date], 
                    c.Name AS ClassName, 
                    e.[Name] AS ExerciseName, 
                    e.[Category]
                FROM [Session] s
                LEFT JOIN [Class] c ON s.ClassID = c.ID
                LEFT JOIN [Logs] l ON s.ID = l.SessionID
                LEFT JOIN [Exercise] e ON l.ExerciseID = e.ID
                WHERE s.ClassID = @ClassID
                ORDER BY s.[Date] DESC;
            END
        """
        cursor.execute(upsert_exercise_log_sql)
        conn.commit()

        delete_class_session_sql = """
            CREATE OR ALTER PROCEDURE delete_ClassSession
                @ClassID INT,
                @SessionDate DATE
            AS
            BEGIN
                SET NOCOUNT ON;
                DECLARE @SID INT;
                SELECT @SID = ID FROM [Session] WHERE ClassID = @ClassID AND [Date] = @SessionDate;
                
                IF @SID IS NOT NULL
                BEGIN
                    DELETE FROM [Logs] WHERE SessionID = @SID;
                    DELETE FROM [Set] WHERE SessionID = @SID;
                    DELETE FROM [Session] WHERE ID = @SID;
                    SELECT 1 AS Success;
                END
                ELSE SELECT 0 AS Success;
            END
        """
        cursor.execute(delete_class_session_sql)
        conn.commit()

        upsert_exercise_sql = """
            CREATE OR ALTER PROCEDURE upsert_Exercise
                @Name NVARCHAR(100),
                @Category NVARCHAR(50)
            AS
            BEGIN
                SET NOCOUNT ON;
                DECLARE @EID INT;
                SELECT @EID = ID FROM [Exercise] WHERE [Name] = @Name;
                
                IF @EID IS NULL
                BEGIN
                    INSERT INTO [Exercise] ([Name], [Category]) VALUES (@Name, @Category);
                    SET @EID = SCOPE_IDENTITY();
                END
                SELECT @EID AS ID;
            END
        """
        cursor.execute(upsert_exercise_sql)
        conn.commit()

        delete_exercise_from_session_sql = """
            CREATE OR ALTER PROCEDURE delete_ExerciseFromSession
                @SessionID INT,
                @ExerciseID INT
            AS
            BEGIN
                SET NOCOUNT ON;
                DELETE FROM [Set] WHERE ExerciseID = @ExerciseID AND SessionID = @SessionID;
                DELETE FROM [Logs] WHERE ExerciseID = @ExerciseID AND SessionID = @SessionID;
            END
        """
        cursor.execute(delete_exercise_from_session_sql)
        conn.commit()

        add_exercise_to_logs_sql = """
                CREATE OR ALTER PROCEDURE sp_AddExerciseToLogs
                    @SessionID INT,
                    @ExerciseID INT
                AS
                BEGIN
                    SET NOCOUNT ON;
                    IF NOT EXISTS (
                        SELECT 1 
                        FROM [Logs] 
                        WHERE ExerciseID = @ExerciseID AND SessionID = @SessionID
                    )
                    BEGIN
                        INSERT INTO [Logs] (ExerciseID, SessionID, IsPr) 
                        VALUES (@ExerciseID, @SessionID, 0);
                    END
                END
            """
        cursor.execute(add_exercise_to_logs_sql)
        conn.commit()

        get_trainer_classes_sql = """
                    CREATE OR ALTER PROCEDURE get_TrainerClasses
                        @TrainerID INT
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        SELECT 
                            c.ID, 
                            c.Name, 
                            p.FName, 
                            p.LName,
                            (
                                SELECT STRING_AGG(CAST(s.Date AS VARCHAR), ', ') 
                                FROM [Session] s 
                                WHERE s.ClassID = c.ID
                            ) AS session_dates,
                            (
                                SELECT STRING_AGG(sub.ExName, ', ')
                                FROM (
                                    SELECT DISTINCT e.Name AS ExName
                                    FROM [Logs] l
                                    JOIN [Exercise] e ON l.ExerciseID = e.ID
                                    JOIN [Session] s ON l.SessionID = s.ID
                                    WHERE s.ClassID = c.ID
                                ) sub
                            ) AS exercises
                        FROM [Class] c
                        JOIN [Teaches] t ON c.ID = t.ClassID
                        JOIN [Person] p ON t.TrainerID = p.ID
                        WHERE t.TrainerID = @TrainerID;
                    END
                """
        cursor.execute(get_trainer_classes_sql)
        conn.commit()

        get_all_classes_sql = """
                    CREATE OR ALTER PROCEDURE get_AllClasses
                    AS
                    BEGIN
                        SET NOCOUNT ON;
                        SELECT 
                            c.ID, 
                            c.Name, 
                            p.FName, 
                            p.LName 
                        FROM [Class] c
                        JOIN [Teaches] t ON c.ID = t.ClassID
                        JOIN [Person] p ON t.TrainerID = p.ID;
                    END
                """
        cursor.execute(get_all_classes_sql)
        conn.commit()

# create_db(connection_string_master)
# add_owners(connection_string_master)
# create_tables(connection_string_database_copy2)
# seed_data(connection_string_database_copy2)
# create_stored_procedures(connection_string_database_copy2)
# destroy_db(connection_string_master)