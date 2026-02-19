import pyodbc

# Stored procedure to add a new person. Can be either a Student or a Trainer
def add_person(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to get user by username
def get_person_by_username(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
                        CREATE OR ALTER PROCEDURE get_Person_by_Username
                            (
                                @Username varchar(50)
                            )
                        AS
                        BEGIN
                            IF @Username IS NULL OR (SELECT COUNT(*) FROM PERSON WHERE Username = @Username) = 0
                            BEGIN;
                                THROW 51000, 'Error: No user with the given username exists in the database', 1
                            END
                            SELECT ID, FName, LName, Username, PasswordHash, DOB, [Weight]
                            FROM Person
                            WHERE Username = @Username
                        END
                     """
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to get user by id
def get_person_by_id(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
                        CREATE OR ALTER PROCEDURE get_Person_by_ID
                            (
                                @ID int
                            )
                        AS
                        BEGIN
                            IF @ID IS NULL OR (SELECT COUNT(*) FROM PERSON WHERE ID = @ID) = 0
                            BEGIN;
                                THROW 51000, 'Error: No user with the user id exists in the database', 1
                            END
                            SELECT ID, FName, LName, Username, PasswordHash, DOB, [Weight]
                            FROM Person
                            WHERE ID = @ID
                        END
                     """
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to update user information for profile or login features and functionality
def update_person(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
                                    WHERE ID = @PersonID
                                 END

                                """
        cursor.execute(sql_script)
        conn.commit()

#Stored procedure to get all existing (non deleted) classes
def get_AllClasses(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to add a workout or class session
def add_session(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
                            CREATE OR ALTER PROCEDURE add_session
                                (
                                    @Date date = NULL,
                                    @StartTime TIME(0),
                                    @EndTime TIME (0),
                                    @Location varchar(50),
                                    @Notes varchar(500),
                                    @Visibility bit = 0,
                                    @StudentID int,
                                    @ClassID int,
                                    @GeneratedID int OUTPUT
                                )
                            AS
                            BEGIN
                                IF @StudentID IS NULL OR (SELECT COUNT(*) FROM STUDENT WHERE ID = @StudentID) = 0
                                BEGIN;
                                    THROW 51001, 'Error: Student not found.', 1
                                END

                                IF @ClassID IS NOT NULL AND (SELECT COUNT(*) FROM Class WHERE ID = @ClassID) = 0
                                BEGIN;
                                    THROW 51002, 'Error: Class not found.', 1
                                END
                                IF @Date IS NULL SET @Date = CAST(GETDATE() AS DATE)

                                INSERT INTO [Session] (Date, StartTime, EndTime, Location, Notes, Visibility, StudentID, ClassID) 
                                VALUES (@Date, @StartTime, @EndTime, @Location, @Notes, @Visibility, @StudentID, @ClassID)

                                SET @GeneratedID = SCOPE_IDENTITY()
                            END
                          """
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to add an exercise and log it for the session with information related to the exercise
def add_exercise_info(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
                                            CREATE OR ALTER PROCEDURE add_exercise_and_info
                                                (
                                                    @Name varchar(50),
                                                    @Category varchar(50),
                                                    @Duration int = NULL,
                                                    @SessionID int,
                                                    @IsPr bit,
                                                    @SetNumber int,
                                                    @Weight decimal(5, 2),
                                                    @Reps int,
                                                    @GeneratedID int OUTPUT
                                                )
                                            AS
                                            BEGIN
                                                IF @Name IS NULL OR @Category IS NULL OR @SessionID IS NULL OR (SELECT COUNT(*) FROM Session WHERE ID = @SessionID) = 0
                                                BEGIN;
                                                    THROW 51001, 'Invalid parameters', 1
                                                END

                                                INSERT INTO [Exercise] (Name, Category, Duration)
                                                VALUES (@Name, @Category, @Duration)

                                                SET @GeneratedID = SCOPE_IDENTITY()

                                                INSERT INTO [Logs] (ExerciseID, SessionID, IsPr)
                                                VALUES (@GeneratedID, @SessionID, @IsPr)

                                                INSERT INTO [Set] (ExerciseID, SessionID, SetNumber, Weight, Reps)
                                                VALUES (@GeneratedID, @SessionID, @SetNumber, @Weight, @Reps)

                                            END
                                        """
        cursor.execute(sql_script)
        conn.commit()

def update_exercise_info(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
                        CREATE OR ALTER PROCEDURE update_exercise_info
                            (
                                @ExerciseID int,
                                @SessionID int,
                                @Name varchar(50),
                                @Category varchar(50),
                                @Duration int,
                                @IsPr bit,
                                @SetNumber int,
                                @Weight decimal(5, 2),
                                @Reps int
                            )
                        AS
                        BEGIN
                            IF @ExerciseID IS NULL OR @SessionID IS NULL OR (SELECT COUNT(*) FROM Logs WHERE ExerciseID = @ExerciseID AND SessionID = @SessionID) = 0
                            BEGIN;
                                THROW 51000, 'Could not find the exercise or session requested', 1
                            END

                            UPDATE Exercise
                            SET [Name] = @Name, [Category] = @Category, Duration = @Duration
                            WHERE ID = @ExerciseID

                            UPDATE [Set]
                            SET SetNumber = @SetNumber, [Weight] = @Weight, Reps = @Reps
                            WHERE ExerciseID = @ExerciseID

                            UPDATE [Logs]
                            SET IsPr = @IsPr
                            WHERE ExerciseID = @ExerciseID AND SessionID = @SessionID
                        END 
                     """
        cursor.execute(sql_script)
        conn.commit()

def get_session_info(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
                        CREATE OR ALTER PROCEDURE get_session_info
                            (
                                @SessionID int,
                                @Date date OUTPUT

                            )
                        AS
                        BEGIN
                            IF @SessionID IS NULL OR (SELECT COUNT(*) FROM Session WHERE ID = @SessionID) = 0
                            BEGIN;
                                THROW 51000, 'The session you are looking for does not exist in the database', 0
                            END

                            SELECT e.Name, e.Category, e.Duration, s.SetNumber, s.Weight, s.Reps, IsPr AS PR
                            FROM Logs
                            JOIN Exercise e ON Logs.ExerciseID = e.ID
                            JOIN [Set] s ON e.ID = s.ExerciseID
                            WHERE Logs.SessionID = @SessionID

                            SET @Date = (SELECT [Date] FROM Session WHERE ID = @SessionID)

                        END 
                     """
        cursor.execute(sql_script)
        conn.commit()

def get_schedule_info(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
                        CREATE OR ALTER PROCEDURE get_schedule_info
                            (
                                @NumRows int = 5,
                                @ID int
                            )
                        AS
                        BEGIN
                            SELECT TOP(@NumRows)
                                ID,
                                [Date],
                                StartTime,
                                EndTime,
                                Location,
                                Notes,
                                Visibility,
                                StudentID,
                                ClassID
                            FROM [Session]
                            WHERE StudentID = @ID
                            ORDER BY [Date] DESC, ID DESC
                        END
                     """
        cursor.execute(sql_script)
        conn.commit()
        

def get_student_enrollments(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE get_StudentEnrollments
                @StudentID INT
            AS
            BEGIN
                SET NOCOUNT ON;
                SELECT c.ID, c.Name, p.FName, p.LName
                FROM [HasA] h
                JOIN [Class] c ON h.ClassID = c.ID
                JOIN [Teaches] t ON c.ID = t.ClassID
                JOIN [Person] p ON t.TrainerID = p.ID
                WHERE h.StudentID = @StudentID;
            END
        """
        cursor.execute(sql_script)
        conn.commit()

def unenroll_student(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

def enroll_student(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE EnrollStudent
                @StudentID INT,
                @ClassID INT
            AS
            BEGIN
                SET NOCOUNT ON;

                IF @StudentID IS NULL OR @ClassID IS NULL
                BEGIN
                    SELECT 0 AS Success, 'Missing StudentID or ClassID' AS Message;
                    RETURN;
                END

                IF NOT EXISTS (SELECT 1 FROM [Student] WHERE ID = @StudentID)
                BEGIN
                    SELECT 0 AS Success, 'Student not found' AS Message;
                    RETURN;
                END

                IF NOT EXISTS (SELECT 1 FROM [Class] WHERE ID = @ClassID)
                BEGIN
                    SELECT 0 AS Success, 'Class not found' AS Message;
                    RETURN;
                END

                IF EXISTS (SELECT 1 FROM [HasA] WHERE StudentID = @StudentID AND ClassID = @ClassID)
                BEGIN
                    SELECT 0 AS Success, 'Already enrolled' AS Message;
                    RETURN;
                END

                INSERT INTO [HasA] (StudentID, ClassID) VALUES (@StudentID, @ClassID);
                SELECT 1 AS Success, NULL AS Message;
            END
        """
        cursor.execute(sql_script)
        conn.commit()

def get_trainer_classes(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

def get_session_in_class(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

def delete_session_in_class(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE delete_Session
                @SessionID INT
            AS
            BEGIN
                SET NOCOUNT ON;
                DELETE FROM [Logs] WHERE SessionID = @SessionID;
                DELETE FROM [Session] WHERE ID = @SessionID;
            END
        """
        cursor.execute(sql_script)
        conn.commit()

#stored proc personal record (uses Achieves and Of) and upsert here is to insert or update, learned from geeksforgeeks and w3schools
def add_and_update_pr(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

#stored proc to get all personal records for a student
def get_pr_sql(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

# Stored proc for the big-3 leaderboard (squat, bench-press, deadlift)
def get_big3_leaderboard(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to get campus-wide workouts for the last year
def get_campus_workouts(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
                        CREATE OR ALTER PROCEDURE get_CampusWorkouts
                            (
                                @SinceDate date = NULL
                            )
                        AS
                        BEGIN
                            IF @SinceDate IS NULL
                                SET @SinceDate = DATEADD(year, -1, CAST(GETDATE() AS date))

                            SELECT [Date], StartTime, EndTime
                            FROM [Session]
                            WHERE [Date] >= @SinceDate
                            ORDER BY [Date] DESC
                        END
                     """
        cursor.execute(sql_script)
        conn.commit()

def upsert_set(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

def get_session_details(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
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
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to insert PR history row
def insert_pr_history(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE insert_PRHistory
                @StudentID INT,
                @ExerciseName VARCHAR(100),
                @Weight DECIMAL(7,2),
                @Reps INT,
                @OneRM DECIMAL(10,2)
            AS
            BEGIN
                SET NOCOUNT ON;

                DECLARE @ExerciseID INT;
                SELECT @ExerciseID = ID FROM [Exercise] WHERE [Name] = @ExerciseName;

                IF @ExerciseID IS NULL
                BEGIN
                    THROW 51000, 'Exercise not found', 1;
                END

                IF @StudentID IS NULL OR @Weight IS NULL OR @Reps IS NULL
                BEGIN
                    THROW 51001, 'Invalid parameters: StudentID, Weight, and Reps are required', 1;
                END

                INSERT INTO dbo.PRHistory (StudentID, ExerciseID, [Weight], Reps, OneRM)
                VALUES (@StudentID, @ExerciseID, @Weight, @Reps, @OneRM);
            END
        """
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to get PR progression history
def get_pr_progression(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE get_PRProgression
                @StudentID INT
            AS
            BEGIN
                SET NOCOUNT ON;

                IF @StudentID IS NULL
                BEGIN
                    THROW 51000, 'StudentID is required', 1;
                END

                SELECT
                    e.Name AS ExerciseName,
                    h.[Weight],
                    h.Reps,
                    h.OneRM,
                    h.RecordedAt
                FROM dbo.PRHistory h
                JOIN [Exercise] e ON h.ExerciseID = e.ID
                WHERE h.StudentID = @StudentID
                ORDER BY e.Name ASC, h.RecordedAt ASC;
            END
        """
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to check if exercise exists
def check_exercise_exists(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE check_ExerciseExists
                @ExerciseID INT
            AS
            BEGIN
                SET NOCOUNT ON;

                IF @ExerciseID IS NULL
                BEGIN
                    SELECT 0 AS ExerciseExists;
                    RETURN;
                END

                IF EXISTS (SELECT 1 FROM [Exercise] WHERE ID = @ExerciseID)
                    SELECT 1 AS ExerciseExists;
                ELSE
                    SELECT 0 AS ExerciseExists;
            END
        """
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to get exercise name by ID
def get_exercise_name(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE get_ExerciseName
                @ExerciseID INT
            AS
            BEGIN
                SET NOCOUNT ON;

                IF @ExerciseID IS NULL
                BEGIN
                    THROW 51000, 'ExerciseID is required', 1;
                END

                SELECT [Name] FROM [Exercise] WHERE ID = @ExerciseID;
            END
        """
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to get exercise leaderboard
def get_exercise_leaderboard(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE get_ExerciseLeaderboard
                @ExerciseName VARCHAR(100),
                @Limit INT = 10
            AS
            BEGIN
                SET NOCOUNT ON;

                IF @ExerciseName IS NULL
                BEGIN
                    THROW 51000, 'ExerciseName is required', 1;
                END

                SELECT TOP (@Limit)
                    p.Username,
                    p.FName,
                    p.LName,
                    (pr.Weight * (1.0 + pr.Reps / 30.0)) AS Best1RM
                FROM [PersonalRecord] pr
                JOIN [Achieves] a ON pr.ID = a.PersonalRecordID
                JOIN [Of] o ON pr.ID = o.PersonalRecordID
                JOIN [Exercise] e ON o.ExerciseID = e.ID
                JOIN [Student] s ON a.StudentID = s.ID
                JOIN [Person] p ON s.ID = p.ID
                WHERE e.Name = @ExerciseName
                ORDER BY Best1RM DESC, p.Username ASC;
            END
        """
        cursor.execute(sql_script)
        conn.commit()

# Stored procedure to get person ID by username
def get_person_id_by_username(connection_string):
    with pyodbc.connect(connection_string) as conn:
        cursor = conn.cursor()
        sql_script = """
            CREATE OR ALTER PROCEDURE get_PersonIDByUsername
                @Username VARCHAR(50)
            AS
            BEGIN
                SET NOCOUNT ON;

                IF @Username IS NULL
                BEGIN
                    THROW 51000, 'Username is required', 1;
                END

                SELECT TOP 1 ID FROM [Person] WHERE [Username] = @Username ORDER BY ID DESC;
            END
        """
        cursor.execute(sql_script)
        conn.commit()
