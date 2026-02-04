# dataservice.py has the data management code and functions for the ShreddedNerds database
# It makes use of PickleDB-backed data layer and has data on all the following: users, workouts, PRs, leaderboards, schedules, and friends

import re
from pickledb import PickleDB
from datetime import datetime, timedelta, timezone, date

# Storing the date and time format in ISO 8601 format with 'Z' suffix for UTC time
ISO_Z = "%Y-%m-%dT%H:%M:%SZ"

# This method find the current time in UTC and formats it in the ISO_Z format
def now_iso():
    """UTC timestamp e.g: 2023-10-05T14:48:00Z"""
    return datetime.now(timezone.utc).replace(microsecond=0).strftime(ISO_Z)

# This method takes any ISO_Z formatted datetime string and converts it into python datetime object
def parse_iso_z(time_string):
    """Parse ISO 8601 'Z' formatted string to datetime object"""
    return datetime.strptime(time_string, ISO_Z).replace(tzinfo=timezone.utc)

# This method also takes any date string and converts it into python date object
def parse_date(date_string):
    """Parse date string in YYYY-MM-DD format to date object"""
    return datetime.strptime(date_string, "%Y-%m-%d").date()

# The Epley Formula
def epley_1rm(weight_kg, reps):
    """1RM = W * (1 + reps/30), rounded to 2 decimal places"""
    return round(float(weight_kg) * (1.0 + float(reps) / 30.0), 2)

def iso_week_of(day):
    """Return ISO Week string like '2025-W44' for a date"""
    # Can be very use useful for weekly score report, scheduling and weekly stats
    year, week, _ = day.isocalendar()
    return f"{year}-W{week:02d}"

def iso_week_boundary(week_string):
    """
    Given 'YYYY-Www', it gives (this_week_monday_date, next_week_monday_date)
    Example: '2025-W44' it gives (2025-10-27, 2025-11-03)
    """

    year, week = week_string.split("-W")
    year, week = int(year), int(week)

    # The method isocalendar(year, week, weekday) return the date for that ISO calendar combination
    # weekday=1 means date for Monday of that week
    start_date = date.fromisocalendar(year, week, 1)
    end_date = start_date + timedelta(days=7)

    return start_date, end_date

# The main class in this file which manages all the data for the application
class DataService:
    """
    A Simple JSON-on-disk store using PickleDB
    Collections (dicts of id->doc)
        - users, exercises, workouts, workout_exercises, personal_records, schedules, friends
    Also maintains simple indexing
    """


    def __init__(self, filepath="shreddednerds.db"):
        self.db = PickleDB(filepath)
        self.filepath = filepath
        self._ensure_roots()
    
    def init_store(self, seed_exercises=False):
        """
        Ensure base collections exist and optionally add an initia set of exercises.
        If at all, this will be called only once at startup from the Flask server
        """
        self._ensure_roots()
        if seed_exercises and not self.db.get("exercises"):
            self._set_exercises()
        self.dump()
    
    def _ensure_roots(self):
        """Initialises the data collections and indexes if missing"""
        for key in ["users", "exercises", "workouts", "workout_exercises", "personal_records", "schedules", "friends"]:
            if not self.db.get(key):
                self.db.set(key, {})
        
        # The sequence object dictionary just stored number of entries in each colleciton (very useful for assigning them indexes naturally upon creation/assignment)
        if not self.db.get("seq"):
            self.db.set("seq", {
                "users": 0, "exercises": 0, "workouts": 0, "workout_exercises": 0, "personal_records": 0, "schedules": 0, "friends": 0
            })
        
        # This dict stores the mapping of each normalized username (converted to all lowercase for consitency) to the user id
        if not self.db.get("index_users_username_normalization"):
            self.db.set("index_users_username_normalization", {})
        
        self.dump()
    
    # Saves the database state
    def dump(self):
        """Save DB to disk"""
        self.db.save()
    
    # Updates count of specific collection and returns id/index of entry
    def _next_id(self, coll):
        """Return index of new entry added to collection"""
        seq = self.db.get("seq")
        seq[coll] += 1
        self.db.set("seq", seq)
        self.dump()
        return seq[coll]

    def _username_normalization(self, username):
        return username.strip().lower()
    
    # -----------------------------USERS------------------------------------
    
    def create_user(self, first_name, last_name, username, password_hash):
        # The password's first char must be a letter and next 2-19 chars can be letters, digits, hyphen or underscore
        if not re.match("^[A-Za-z][A-Za-z0-9._-]{2,19}$", username.strip()):
            raise ValueError("Invalid username")

        norm = self._username_normalization(username)

        idx = self.db.get("index_users_username_normalization")
        if norm in idx:
            raise ValueError("Username already exists")
        
        user_id = self._next_id("users")
        user = {
            "id": user_id,
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "username": username.strip(),
            "username_normalization": norm,
            "password_hash": password_hash,
            "is_public": True,
            "unit_pref": "kg",
            "created_at": now_iso(),
            "last_login_at": None
        }

        users = self.db.get("users")
        users[str(user_id)] = user
        self.db.set("users", users)

        idx[norm] = user_id
        self.db.set("index_users_username_normalization", idx)

        self.dump()
        return self._user(user)
    
    # This method first takes username, then gets the id, and then gives back the user
    def get_user_by_username(self, username):
        norm = self._username_normalization(username)
        idx = self.db.get("index_users_username_normalization")
        user_id = idx.get(norm)
        if not user_id:
            return None
        return self.db.get("users").get(str(user_id))
    
    # This method takes user id and gives back the user object
    def get_user_by_id(self, user_id):
        return self.db.get("users").get(str(user_id))
    
    # Note: **kwargs means it can be as many number of arguments
    # Good source i referred to understand what it means/how to use it: https://www.geeksforgeeks.org/python/args-kwargs-python/
    # It also takes form of a dictionary of key (name) and value pairs
    def update_user(self, user_id, **fields):
        users = self.db.get("users")
        user = users.get(str(user_id))
        if not user:
            raise KeyError("User not found")
        
        allowed_fields = {"first_name", "last_name", "is_public", "unit_pref", "last_login_at"}
        for name, value in fields.items():
            if name in allowed_fields:
                user[name] = value

        users[str(user_id)] = user
        self.db.set("users", users)
        self.dump()

        return self._user(user)
    
    # Just returns an object with user's key info (one that can be made public)
    def _user(self, user):
        return {
            "id": user["id"],
            "username": user["username"],
            "first_name": user["first_name"],
            "last_name": user["last_name"],
            "is_public": user["is_public"],
            "unit_pref": user["unit_pref"],
            "created_at": user["created_at"],
            "last_login_at": user["last_login_at"]
        }
    

    #--------------------------------------Exercises---------------------------------------
    
    # Method to set/define all exercises in the database
    def _set_exercises(self):
        catalog = [
            ("Squat", "strength"),
            ("Bench Press", "strength"),
            ("Deadlift", "strength"),
            ("Overhead Press", "strength"),
            ("Barbell Row", "strength"),
            ("Dumbell Curl", "strength"),
            ("Pull-ups", "strength"),
            ("Running", "cardio"),
            ("Cycling", "cardio"),
            ("Jogging", "cardio")
        ]

        for name, category in catalog:
            self.create_exercise(name, category)
    

    # Method to register an exercise name and category pair in the database
    def create_exercise(self, name, category):
        exercise_id = self._next_id("exercises")
        exercise = {"id": exercise_id, "name": name, "category": category}
        exercises = self.db.get("exercises")
        exercises[str(exercise_id)] = exercise
        self.db.set("exercises", exercises)
        self.dump()
        return exercise
    
    # Gives a list of all the exercises in the database
    def list_exercises(self):
        exercises = list(self.db.get("exercises").values())
        exercises.sort(key=lambda exercise: exercise["name"].lower())
        return exercises
    
    # Gets the name of exercise base don the id
    def _exercise_name(self, exercise_map, exercise_id):
        exercise = exercise_map.get(str(exercise_id))
        if exercise:
            return exercise["name"]
        else:
            return f"#{exercise_id}"
    
    #-------------------------Workouts-------------------------
    def create_workout(self, user_id, day, duration_minutes, notes=""):
        workout_id = self._next_id("workouts")

        # Here I am creating a new workout with the provided arguments/information
        workout = {
            "id": workout_id,
            "user_id": user_id,
            "date": day,
            "duration_minutes": int(duration_minutes),
            "notes": notes,
            "created_at": now_iso()
        }

        # Here I am fetching the list of workouts entries currently in the database, appending this one to it, and setting this updated list (new copy) to be the new workouts list/object in the database
        workouts = self.db.get("workouts")
        workouts[str(workout_id)] = workout
        self.db.set("workouts", workouts)
        self.dump()
        return workout

    def add_workout_exercises(self, user_id, workout_id, items):

        # Getting the workout with the workout_id passed in
        workouts = self.db.get("workouts")
        workout = workouts.get(str(workout_id))
        if not workout or workout["user_id"] != user_id:
            raise KeyError("Workout not found")
        
        exercise_map = self.db.get("exercises")
        workout_map = self.db.get("workout_exercises")
        new_prs = []

        for item in items:
            exercise_id = int(item["exercise_id"])
            if str(exercise_id) not in exercise_map:
                raise ValueError("Exercise not found")
            row_id = self._next_id("workout_exercises")

            # Creating a new exercise row for the workout
            row = {
                "id": row_id,
                "workout_id": workout_id,
                "exercise_id": exercise_id,
                "sets": int(item["sets"]),
                "reps": int(item["reps"]),
                "weight_kg": float(item("weight_kg")),
                "created_at": now_iso()
            }

            # Updating the workout map and potentially PRs if new PRs were made
            workout_map[str(row_id)] = row
            pr_updated = self._update_pr(user_id, exercise_id, row["weight_kg"], row["reps"])
            if pr_updated:
                new_prs.append(pr_updated)
        

        self.db.set("workout_exercises", workout_map)
        self.dump()
        return {"added": len(items), "new_prs": new_prs}
    
    def get_workout(self, user_id, workout_id):

        # Fetching workout
        workouts = self.db.get("workouts")
        workout_exercises = self.db.get("workout_exercises")
        exercise_map = self.db.get("exercises")

        workout = workouts.get(str(workout_id))
        if not workout or workout["user_id"] != user_id:
            raise KeyError("Workout not found")

        # Gather exercises linked to this workout
        items = []
        for we in workout_exercises.values():
            if we["workout_id"] == workout_id:
                ex = exercise_map.get(str(we["exercise_id"]))
                items.append({
                    "exercise": ex["name"] if ex else f"#{we['exercise_id']}",
                    "sets": we["sets"],
                    "reps": we["reps"],
                    "weight_kg": we["weight_kg"],
                    "one_rm": round(we["weight_kg"] * (1 + we["reps"] / 30), 2)
                })
        
        items.sort(key=lambda i: i["exercise"])

        full = dict(workout)
        full["items"] = items
        return full


    

    def list_workouts(self, user_id, from_date=None, to_date=None):
        workouts = []
        all_workouts = self.db.get("workouts").values()

        for x in all_workouts:
            if x["user_id"] != user_id:
                break

            # These series of conditions check what all valid information was provided in terms of from_date and to_date parameters
            # The results/workouts are filtered accordingly and only the ones within the range will be considered
            if from_date and to_date:
                fd = parse_date(from_date)
                td = parse_date(to_date)
                if parse_date(x["date"] >= fd) and parse_date(x["data"] <= td):
                        workouts.append(x)
            elif from_date:
                fd = parse_date(from_date)
                if parse_date(x["date"] >= fd):
                    workouts.append(x)
            elif to_date:
                td = parse_date(to_date)
                if parse_date(x["date"] <= td):
                    workouts.append(x)
        
        # Here I am sorting the workouts based on the date and the created_at time, making sure the most recent ones are towards the top
        workouts.sort(key=lambda w: (w["date"], w["created_at"]), reverse=True)
    
    def _maybe_update_pr(self, user_id, exercise_id, weight_kg, reps):

        # Updating the one_rm figure and fetching the PRs which currently exist
        one_rm = epley_1rm(weight_kg, reps)
        prs_map = self.db.get("personal_records")
        
        # Here I am finding the specific id of the PR stored based on the match with user_id and exercise_id
        existing_id = None
        for pid, pr in prs_map.items():
            if pr["user_id"] == user_id and pr["exercise_id"] == exercise_id:
                existing_id = pid
                break
        
        if existing_id:
            # If there does already exist a PR entry for the given exercise and user and if the new one_rm is grater than previous one, we are updating the new PR info
            pr = prs_map[existing_id]
            if one_rm > pr["best_1rm_kg"]:
                pr["best_1rm_kg"] = one_rm
                pr["best_weight_kg"] = weight_kg
                pr["best_reps"] = reps
                pr["updated_at"] = now_iso()
                prs_map[existing_id] = pr
                self.db.set("personal_records", prs_map)
                self.dump()
                return pr
            return None
        else:
            # If no such existing PR entry is found, we are creating new PR entry
            new_id = self._next_id("personal_records")
            rec = {
                "id": new_id,
                "user_id": user_id,
                "exercise_id": exercise_id,
                "best_weight_kg": weight_kg,
                "best_reps": reps,
                "best_1rm_kg": one_rm,
                "updated_at": now_iso()
            }
            prs_map[str(new_id)] = rec
            self.db.set("personal_records", prs_map)
            self.dump()
            return rec
    
    def big3_leaderboard(self):

        # Here I am retrieving the ids of the exercises part of the big 3
        exercise_map = self.db.get("exercises")
        name_to_id = {e["name"]: e["id"] for e in exercise_map.values()}
        needed = {
            name_to_id.get("Squat"),
            name_to_id.get("Bench Press"),
            name_to_id.get("Deadlift")
        }

        totals = {}

        # For all existing PR records, whichever ones are for any of the 3 exercises, the user's total for them is being added to the dictionary
        for personal_record in self.db.get("personal_records").values():
            if personal_record["exercise_id"] in needed:
                user_id = personal_record["user_id"]
                if user_id not in totals:
                    totals[user_id] += personal_record["best_1rm_kg"]
        
        # Adding the records to the digital board for the big-3
        users = self.db.get("users")
        board = []
        for user_id, total in totals.items():
            user = users.get(str(user_id))
            if not user:
                continue
            board.append({
                "username": user["username"],
                "display_name": f"{user['first_name']} {user['last_name'][0]}.",
                "big3_total_kg": round(total, 2)
            })
        
        # Sorting the big 3 digital board entries with most wieght to least weight performances
        board.sort(key=lambda row: row["big3_total_kg"], reverse=True)
        return board
    
    #------------------------SCHEDULES--------------------------
    def create_schedule_slot(self, user_id, start_time, end_time, location, note, visibility="friends"):
        schedule_id = self._next_id("schedules")
        
        # Creates a gym workout schedule slot object and then updates it in the list/collection of existing schedules
        slot = {
            "id": schedule_id,
            "user_id": user_id,
            "start_time": start_time, 
            "end_time": end_time,
            "location": location,
            "note": note,
            "visibility": visibility
        }
        schedules = self.db.get("schedules")
        schedules[str(schedule_id)] = slot
        self.db.set("schedules", schedules)
        self.dump()
        return slot
    
    # Simple method to retrieve the specific schedule slot for the user that is requested
    def list_my_slots(self, user_id):
        schedules = self.db.get("schedules").values()
        resp = [schedule for schedule in schedules if schedule["user_id"] == user_id]
        resp.sort(key=lambda sch: sch["start_time"])
        return resp
    

    #-------------------------FRIENDS------------------------------
    def send_friend_request(self, requester_id, to_username):

        # In this portion, I am just making sure that the sender/receiver username passed in are valid combinations
        to_user = self.get_user_by_username(to_username)
        if not to_user:
            raise ValueError("User not found")
        if to_user["id"] == requester_id:
            raise ValueError["Cannot friend yourself"]

        friendship_map = self.db.get("friends")

        # Checks for an already existing friendship or pending request between the two users, if one exists, it raises an Error
        for friend in friendship_map.values():
            if (friend["requester_id"] == requester_id and friend["addressee_id"] == to_user["id"]) or \
                (friend["requester_id"] == to_user["id"] and friend["addressee_id"] == requester_id):
                if friend["status"] in ("pending", "accepted"):
                    raise ValueError("Friendship already exists")
        
        friendship_id = self._next_id("friends")

        # Creates a new friendship record and updates the friendship map
        rec = {
            "id": friendship_id,
            "requester_id": requester_id,
            "addressee_id": to_user["id"],
            "status": "pending",
            "created_at": now_iso()
        }
        friendship_map[str(friendship_id)] = rec
        self.db.set("friends", friendship_map)
        self.dump()
        return rec
    
    #Create a trainer
    def create_trainer(self, first_name, last_name, username, password_hash):
        norm = self._username_normalization(username)
        idx = self.db.get("index_users_username_normalization")
        if norm in idx:
            raise ValueError("Username already exists")
        
        with pyodbc.connect(connection_string_database_copy) as conn:
            cursor = conn.cursor()
            
            sql_person = "INSERT INTO [Person] (FName, LName, Username, PasswordHash) VALUES (?, ?, ?, ?)"
            cursor.execute(sql_person, (first_name, last_name, username, password_hash))
            
            cursor.execute("SELECT SCOPE_IDENTITY()")
            person_id = int(cursor.fetchone()[0])
            
            sql_trainer = "INSERT INTO [Trainer] (ID) VALUES (?)"
            cursor.execute(sql_trainer, (person_id,))
            conn.commit()

        user_id = self._next_id("users")
        
        user = {
            "id": user_id,
            "sql_id": person_id,
            "username": username.strip(),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "role": "trainer",
            "password_hash": password_hash,
            "created_at": now_iso()
        }
        
        users = self.db.get("users")
        users[str(user_id)] = user
        self.db.set("users", users)
        
        idx[norm] = user_id
        self.db.set("index_users_username_normalization", idx)
        
        self.dump()
        
        return user