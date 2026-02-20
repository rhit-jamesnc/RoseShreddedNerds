import dataservice
import os
import json
from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

# This is the crucial app setup part which allows us to just create an run one build
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve the react app which has been built from ../server/dist
app = Flask(__name__, static_url_path='', static_folder=os.path.join(BASE_DIR, 'dist'))

# Important configurations
app.config["SECRET_KEY"] = "dev-secret-key-temp"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

ds = dataservice.DataService()

@app.route("/")
def index():
    # Serve the main React index.html for the root path
    return send_from_directory(app.static_folder, "index.html")

@app.route("/<path:path>")
def spa_catch__all(path):
    # In this function, I am serving index.html for any non-API path so React Router can handle it
    # If it is an /api/...path, then I am making use of my normal 404 handler

    if path.startswith("api/"):
        return not_found(None)
    return send_from_directory(app.static_folder, "index.html")

def current_user():
    user_id = session.get("user_id")
    if user_id:
        return ds.get_user_by_id(int(user_id))
    return None

def login_required(fn):
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)

    wrapper.__name__ = fn.__name__
    return wrapper

def require_json():
    if not request.is_json:
        return jsonify({"error": "Expected application/json"}), 400
    return None

# ----------------------------- error handling ---------------------------------
@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Not Found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error", "details": str(e)}), 500

@app.post("/api/auth/register")
def register():
    error = require_json()
    if error:
        return error
    
    data = request.get_json() or {}
    role = data.get("role", "student")
    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    dob = data.get("dob") or ""
    weight = data.get("weight") or ""

    # If all of the fields aren't there then throw error message
    if not (first_name and last_name and username and password):
        return jsonify({"error": "Missing fields"}), 400
    
    try:
        password_hash = generate_password_hash(password)

        user = ds.create_user(
            first_name=first_name,
            last_name=last_name,
            username=username,
            password_hash=password_hash,
            dob=dob,
            weight=weight,
            role=role
        )
        session["user_id"] = user["ID"]
        session.permanent = True

        return jsonify({"user": user}), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/auth/login")
def login():
    error = require_json()
    if error:
        return error
    
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "No username or password given."}), 400
    
    try:
        user = ds.get_user_by_username(username)
        if not user:
            return jsonify({"error": "Invalid credentials"}), 401

        pw_hash = user.get("PasswordHash")
        if isinstance(pw_hash, (bytes, bytearray, memoryview)):
            pw_hash = bytes(pw_hash).decode("utf-8", errors="ignore")
        if not isinstance(pw_hash, str) or not pw_hash:
            return jsonify({"error": "Invalid credentials"}), 401

        try:
            ok = check_password_hash(pw_hash, password)
        except Exception as e:
            print(f"Password hash error: {e}")
            ok = False

        if not ok:
            return jsonify({"error": "Invalid credentials"}), 401
        
        # Set the user for the session and give back/return the user
        session["user_id"] = user["ID"]
        session.permanent = True
        try:
            ds.login(session["user_id"])
        except Exception as e:
            print(f"Login session error: {e}")

        return jsonify({"user": ds._user()}), 200
    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Login failed"}), 500

@app.get("/api/profile")
@login_required
def get_profile():

    user = ds._user()
    if not user:
        session.clear()
        return jsonify({"error": "Unauthorized"}), 401
    
    
    dob_val = user.get("DOB")
    if dob_val is None:
        user["DOB"] = ""
    else:
        try:
            user["DOB"] = dob_val.strftime("%Y-%m-%d")
        except:
            s = str(dob_val)
            user["DOB"] = s[:10] if len(s) >= 10 else ""
    
    return jsonify({"user": user}), 200

@app.put("/api/profile")
@login_required
def update_profile():
    
    user_id = session.get("user_id")
    user = ds._user()
    if not user_id or not user:
        session.clear()
        return jsonify({"error": "Unauthorized"}), 401

    error = require_json()
    if error:
        return error
    
    data = request.get_json() or {}

    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    username = (data.get("username") or "").strip()
    dob = data.get("dob")
    weight = data.get("weight")
    new_password = data.get("password")

    if dob == "":
        dob = None
    else:
        dob = datetime.strptime(dob, "%Y-%m-%d").date()
    if weight == "":
        weight = None
    if new_password == "":
        new_password = None
    
    password_hash = None
    if new_password is not None:
        password_hash = generate_password_hash(new_password)
    
    try:
        ds.update_user(ID=user_id, FName=first_name, LName=last_name, Username=username, PasswordHash=password_hash, DOB=dob, Weight=weight)
        updated_user = ds._user()
        return jsonify({"user": updated_user}), 200
    
    except Exception as e:
        #return jsonify({"error": "Failed to update profile", "details": str(e)}), 500
        return jsonify({"error": str(e), "details": str(e)}), 500


@app.post("/api/auth/logout")
def logout():
    # Simply logs out/the stores session clears out
    session.clear()
    ds.logout()
    return ("", 204)

@app.get("/api/auth/status")
def auth_status():
    # Gets the current user and if the value will be None then even the isAuthenticated feel would be none as I believe None is a falsy value
    current = ds._user()
    return jsonify({"isAuthenticated": bool(current), "user": current})

#-------------------------------Exercises --------------------------------
@app.get("/api/exercises")
def exercises_list():
    items = ds.list_exercises()
    return jsonify({"items": items})

# ----------------------------------- Sets ---------------------------------------------

@app.post("/api/sets")
@login_required
def update_exercise_set():
    error = require_json()
    if error:
        return error
    
    data = request.get_json()
    session_id = data.get("SessionID")
    exercise_id = data.get("ExerciseID")
    set_num = data.get("SetNumber")
    weight = data.get("weight")
    reps = data.get("reps")

    if exercise_id is None or set_num is None or session_id is None:
        return jsonify({"error": "No Session or Exercise Was Edited, Hit 'Close' Instead"}), 400

    try:
        ds.trainer_edit_set(session_id, exercise_id, set_num, weight, reps)
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#------------------------------------Schedule--------------------------------------------
@app.get("/api/schedule/slots")
@login_required
def list_schedule_slots():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401
    try:
        slots = ds.list_my_slots(int(user_id))
        return jsonify({"items": slots}), 200
    except Exception as e:
        print(str(e))
        return jsonify({"error": str(e)}), 500


@app.post("/api/schedule/slots")
@login_required
def create_schedule_slot():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    user = ds.get_user_by_id(int(user_id))
    if not user:
        session.clear()
        return jsonify({"error": "Unauthorized"}), 401

    if not request.is_json:
        return jsonify({"error": "Expected application/json"}), 400

    data = request.get_json() or {}
    date = (data.get("date") or "").strip()
    start_time = (data.get("start_time") or "").strip()
    end_time = (data.get("end_time") or "").strip()
    location = (data.get("location") or "").strip()
    notes = (data.get("note") or "").strip()
    visibility = (data.get("visibility") or "friends").strip()

    if not date:
        return jsonify({"error": "Missing date"}), 400

    try:
        slot = ds.create_schedule_slot(
            ID=int(user_id),
            Date=date,
            StartTime=start_time,
            EndTime=end_time,
            Location=location,
            Notes=notes,
            Visibility=visibility
        )
        return jsonify({"slot": slot}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------- workouts (logs for a session) ---------------------------------

@app.post("/api/workouts")
@login_required
def log_workout_for_session():
    error = require_json()
    if error:
        return error

    user_id = session.get("user_id")
    data = request.get_json() or {}

    session_id = data.get("session_id")
    duration = data.get("duration_minutes")
    notes = (data.get("notes") or "").strip()
    items = data.get("items") or []

    if not session_id:
        return jsonify({"error": "Error, select a schedule slot (session) first."}), 400

    try:
        created_exercise_ids = []
        new_prs = []

        for ex in items:
            name = (ex.get("name") or "").strip()
            category = (ex.get("category") or "strength").strip()
            sets = int(ex.get("sets") or 0)
            reps = int(ex.get("reps") or 0)
            weight = ex.get("weight_kg")
            is_pr = bool(ex.get("is_pr") or False)

            if not name or sets < 1 or reps < 1 or weight is None:
                return jsonify({"error": "Each exercise must include name, sets>=1, reps>=1, and weight."}), 400


            for set_num in range(1, sets + 1):
                new_id = ds.add_exercise_and_info(
                    Name=name,
                    Category=category,
                    Duration=duration if duration is not None else None,
                    SessionID=int(session_id),
                    IsPr=1 if is_pr else 0,
                    SetNumber=set_num,
                    Weight=float(weight),
                    Reps=int(reps)
                )
                created_exercise_ids.append(new_id)

            pr = ds._maybe_update_pr_sql(int(user_id), name, float(weight), int(reps))
            if pr:
                new_prs.append(pr)

        return jsonify({"ok": True, "created_exercise_ids": created_exercise_ids, "result": {"new_prs": new_prs}}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/workouts")
@login_required
def list_workouts():
    user_id = session.get("user_id")
    try:
        items = ds.list_my_slots(int(user_id), num_rows=50)
        return jsonify({"items": items}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/workouts/campus")
def list_campus_workouts():
    items = ds.list_campus_workouts()
    return jsonify({"items": items}), 200

@app.get("/api/dashboard/stats")
def dashboard_stats():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        totals = ds.workout_totals(int(user_id))
        return jsonify({"totals": totals}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#--------------------------------------Leadersboard and PR stuff-------------------------------------------

@app.get("/api/leaderboards/big3")
def big3():
    return jsonify({"items": ds.big3_leaderboard_sql()})

@app.get("/api/leaderboards/exercises")
def exercise_leaderboards():
    return jsonify({"items": ds.exercise_leaderboards_sql(["Squat", "Bench Press", "Deadlift"], limit=10)})


#pr's
@app.get("/api/personal-records")
def personal_records():
    user = current_user()
    sql_id = user.get("sql_id") or user.get("ID")
    if not sql_id:
        return jsonify({"items": [], "message": "no sql server link for this account"}), 200
    items = ds.get_personal_records_sql(sql_id)
    return jsonify({"items": items})

@app.get("/api/personal-records/progression")
@login_required
def personal_records_progression():
    user = current_user()
    sql_id = user.get("sql_id") or user.get("ID")
    if not sql_id:
        return jsonify({"items": [], "message": "no sql server link for this account"}), 200
    items = ds.get_pr_progression_sql(sql_id)
    return jsonify({"items": items})


# ----------------------------------- Classes ---------------------------------------------

@app.get('/api/classes')
@login_required
def get_all_classes():
    user = current_user()
    print(user.get("role"))
    try:
        classes = ds.get_classes()
        return jsonify(classes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post('/api/classes/create')
@login_required
def register_class():
    data = request.get_json(force=True, silent=True)
    
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return jsonify({"error": "Invalid JSON format"}), 400

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Data must be a JSON object"}), 400
        
    name = (data.get("name") or "").strip()

    user = current_user()
    trainer_sql_id = user.get("ID")
    role = user.get("role").lower()

    if not name:
        return jsonify({"error": "Missing class name"}), 400
    
    if role != "trainer" or not trainer_sql_id:
        return jsonify({"error": "Only registered trainers can create classes"}), 403

    try:
        result = ds.create_class(trainer_sql_id, name)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/classes/<int:class_id>", methods=["DELETE"])
@login_required
def delete_class(class_id):
    user = current_user()
    trainer_sql_id = user.get("ID")
    
    if user.get("role").lower() != "trainer" or not trainer_sql_id:
        return jsonify({"error": "Only trainers can delete classes"}), 403

    try:
        result = ds.delete_class(trainer_sql_id, class_id)
        if "error" in result:
            status_code = 403 if "Unauthorized" in result["error"] else 400
            return jsonify(result), status_code
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
    
@app.post("/api/classes/<int:class_id>/enroll")
@login_required
def enroll_in_class(class_id):
    user = current_user()
    
    if user.get("role").lower() != "student":
        return jsonify({"error": "Only students can enroll in classes"}), 403

    student_sql_id = user.get("ID")
    if not student_sql_id:
        return jsonify({"error": "Student record not found in SQL database"}), 404

    result = ds.enroll_student(student_sql_id, class_id)
    
    if "error" in result:
        return jsonify(result), 400
        
    return jsonify(result), 200

@app.post("/api/classes/<int:class_id>/unenroll")
@login_required
def unenroll_from_class(class_id):
    user = current_user()
    if user.get("role").lower() != "student":
        return jsonify({"error": "Only students can unenroll"}), 403

    student_sql_id = user.get("ID")
    result = ds.unenroll_student(student_sql_id, class_id)
    
    if "error" in result:
        return jsonify(result), 400
        
    return jsonify(result), 200

@app.get("/api/my-classes")
@login_required
def get_my_classes():
    user = current_user()
    
    if user.get("role").lower() != "student":
        return jsonify({"error": "Unauthorized"}), 403
        
    student_sql_id = user.get("ID")
    if not student_sql_id:
        return jsonify({"error": "Student profile not found"}), 404
        
    classes = ds.get_student_enrollments(student_sql_id)
    return jsonify(classes)

@app.get("/api/trainer-classes")
@login_required
def get_trainer_dashboard_classes():
    user = current_user()
    
    if user.get("role").lower() != "trainer":
        return jsonify({"error": "Unauthorized"}), 403
        
    trainer_sql_id = user.get("ID")
    if not trainer_sql_id:
        return jsonify({"error": "Trainer profile not found"}), 404
        
    classes = ds.get_trainer_classes(trainer_sql_id)
    return jsonify({"items": classes})

@app.route("/api/classes/<int:class_id>/update-session", methods=["POST"])
@login_required
def update_session_route(class_id):
    data = request.get_json(force=True, silent=True)
    
    if not isinstance(data, dict):
        return jsonify({"error": "Data must be a JSON object"}), 400
        
    session_date = data.get('session_date')
    exercises = data.get('exercises', "")

    if not session_date:
        return jsonify({"error": "Missing session_date"}), 400
        
    result = ds.update_class_session(class_id, session_date, exercises)
    
    if "error" in result:
        return jsonify(result), 500
    return jsonify(result), 200

@app.get("/api/classes/<int:class_id>/sessions")
@login_required
def get_class_sessions(class_id):
    user = current_user()
    if user.get("role").lower() != "trainer":
        return jsonify({"error": "Unauthorized"}), 403

    try:
        sessions = ds.get_class_sessions(class_id)
        return jsonify({"items": sessions}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/classes/<int:class_id>/delete-session", methods=["DELETE"])
@login_required
def delete_class_session_route(class_id):
    data = request.get_json(force=True, silent=True)
    
    if not data:
        return jsonify({"error": "No JSON data received"}), 400
        
    session_date = data.get('session_date')

    if not session_date:
        return jsonify({"error": "Missing session_date"}), 400

    try:
        result = ds.delete_class_session(class_id, session_date)
        
        if "error" in result:
            return jsonify(result), 404
            
        return jsonify(result), 200
    except Exception as e:
        print(f"SERVER ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.post("/api/sessions/<int:session_id>/update")
@login_required
def update_specific_session(session_id):
    error = require_json()
    if error:
        return error
        
    data = request.get_json()
    new_date = data.get("date")

    if not new_date:
        return jsonify({"error": "Missing date"}), 400

    try:
        result = ds.update_session_date(session_id, new_date)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.get("/api/sessions")
@login_required
def list_all_sessions():
    try:
        sessions = ds.get_all_sessions_sql() 
        return jsonify(sessions), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/logs")
@login_required
def create_exercise_log():
    error = require_json()
    if error: return error
    
    data = request.get_json()
    ex_id = data.get("exercise_id")
    sess_id = data.get("session_id")
    is_pr = data.get("is_pr", 0)

    if not ex_id or not sess_id:
        return jsonify({"error": "Missing exercise_id or session_id"}), 400

    try:
        result = ds.log_exercise_to_session(ex_id, sess_id, is_pr)
        return jsonify(result), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post("/api/exercises")
@login_required
def create_exercise():
    error = require_json()
    if error: return error
    
    data = request.get_json()
    name = data.get("name")
    category = data.get("category", "General")
    
    if not name:
        return jsonify({"error": "Name is required"}), 400
        
    new_ex = ds.create_exercise(name, category)
    return jsonify(new_ex), 201

@app.route("/api/sessions/<int:session_id>/exercises/<int:exercise_id>", methods=["DELETE"])
@login_required
def delete_session_exercise(session_id, exercise_id):
    user = current_user()
    
    if user.get("role").lower() != "trainer":
        return jsonify({"error": "Only trainers can modify session exercises"}), 403

    try:
        result = ds.delete_exercise_from_session(session_id, exercise_id)
        
        if "error" in result:
            return jsonify(result), 404
            
        return jsonify(result), 200
    except Exception as e:
        print(f"DELETE ERROR: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/api/sessions/<int:session_id>/content", methods=["GET"])
@login_required
def get_session_content(session_id):
    try:
        content_dict = ds.get_session_content(session_id)
        content_list = []
        for name, data in content_dict.items():
            content_list.append({
                "name": name,
                "category": data["category"],
                "is_pr": data["is_pr"],
                "sets": data["sets"]
            })
            
        return jsonify(content_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/api/sessions/details', methods=['GET'])
@login_required
def get_session_details():
    date_str = request.args.get('date')
    class_id = request.args.get('classId')
    
    if not date_str or not class_id:
        return jsonify({"error": "Missing date or classId"}), 400

    try:
        details = ds.get_session_details_by_date(date_str, class_id)
        return jsonify(details), 200
    except Exception as e:
        print(f"Error fetching session details: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/api/viewer/sessions")
def viewer_sessions():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        items = ds.viewer_list_sessions(int(user_id))
        return jsonify({"items": items}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.get("/api/viewer/sessions/<int:session_id>")
def viewer_session_detail(session_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = ds.viewer_get_session_full(int(user_id), int(session_id))
        return jsonify({"session": data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.put("/api/viewer/sessions/<int:session_id>")
def viewer_update_session(session_id):
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}

    try:
        ds.viewer_update_session(
            session_id=int(session_id),
            date=data.get("date"),
            start_time=data.get("start_time"),
            end_time=data.get("end_time"),
            location=data.get("location"),
            notes=data.get("notes"),
            visibility=data.get("visibility"),
        )
        return jsonify({"success": True}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.put("/api/viewer/exercise")
def viewer_update_exercise():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json() or {}

    try:
        ds.viewer_update_exercise(
            session_id=data.get("session_id"),
            exercise_id=data.get("exercise_id"),
            set_number=data.get("set_number"),
            weight=data.get("weight"),
            reps=data.get("reps"),
        )
        return jsonify({"success": True}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ----------------------------------- Health ---------------------------------------------
@app.get("/api/health")
def health():
    return jsonify({"ok": True, "time": dataservice.now_iso()})

# -------------------------------------Main----------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
