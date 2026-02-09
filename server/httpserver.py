import dataservice
import os
import json
from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta



# This is the crucial app setup part which allows us to just create an run one build
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Serve the react app which has been built from ../server/dist
app = Flask(__name__, static_url_path='', static_folder=os.path.join(BASE_DIR, 'dist'))

# Important configurations
app.config["SECRET_KEY"] = "dev-secret-key-temp"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=7)

# Instantiate the DB service
ds = dataservice.DataService("shredded-nerds.db")
ds.init_store(seed_exercises=True)


# ----------------------------- static routes (React) ---------------------------------
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

#-------------------------Helpers--------------------------

def current_user():
    user_id = session.get("user_id")
    if user_id:
        return ds.get_user_by_id(user_id)
    else:
        return None

def require_json():
    if not request.is_json:
        return jsonify({"error": "Expected application/json"}), 400
    
    return None

# This sets up a wrapper which can be added to any route to execute this wrapper function first instead of that routes dedicated function
# So if for example a route has this decorator/wrapper, if there is no current user logged in, an error would be thrown, otherwise the route function will be executed as it is supposed to
def login_required(fn):
    def wrapper(*args, **kwargs):
        if not current_user():
            return jsonify({"error": "Unauthorized"}), 401
        return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


#------------------------Error Handling-----------------------

@app.errorhandler(404)
def not_found(_e):
    return jsonify({"error": "Not Found"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Server error", "details": str(e)}), 500

#------------------------Authentication-------------------------

@app.post("/api/auth/register")
def register():
    error = require_json()
    if error:
        return error
    
    # Here I am simply retrieving the form data from the post requester to this path
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

    # Create the user
    try:
        password_hash = generate_password_hash(password)

        if role == "trainer":
            user = ds.create_user(
                first_name=first_name,
                last_name=last_name,
                username=username,
                password_hash=password_hash,
                weight=weight,
                role=role
            )
        else:
            user = ds.create_user(
                first_name=first_name,
                last_name=last_name,
                username=username,
                password_hash=password_hash,
                dob=dob,
                weight=weight,
                role=role
            )
        session["user_id"] = user["id"]
        session.permanent = True

        return jsonify({"user": user}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409

@app.post("/api/auth/login")
def login():
    error = require_json()
    if error:
        return error
    
    # Retrieve the data from the post request for the login form
    # If the credentials aren't valid or do not match, throw an error
    data = request.get_json() or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    user = ds.get_user_by_username(username)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Set the user for the session and give back/return the user
    session["user_id"] = user["id"]
    session.permanent = True
    ds.update_user(user_id=user["id"], last_login_at=dataservice.now_iso())

    return jsonify({"user": ds._user(user)}), 200

@app.post("/api/auth/logout")
def logout():
    # Simply logs out/the stores session clears out
    session.clear()
    return ("", 204)

@app.get("/api/auth/status")
def auth_status():
    # Gets the current user and if the value will be None then even the isAuthenticated feel would be none as I believe None is a falsy value
    current = current_user()
    return jsonify({"isAuthenticated": bool(current), "user": ds._user(current) if current else None})


#-------------------------------Exercises --------------------------------
@app.get("/api/exercises")
def exercises_list():
    return jsonify(ds.list_exercises())

#-------------------------------Workouts (my core value-add feature path)---------------------
@app.post("/api/workouts")
@login_required
def create_workout():
    error = require_json()
    if error:
        return error
    
    data = request.get_json() or {}

    # Getting the form fields form the post request
    day = (data.get("date") or "").strip()
    duration = data.get("duration_minutes")
    notes = data.get("notes") or ""
    items = data.get("items") or []

    if not day or duration is None:
        return jsonify({"error": "Missing date or duration_minutes"}), 400
    
    # Creating a workout session
    workout_session = ds.create_workout(current_user()["id"], day=day, duration_minutes=duration, notes=notes)

    # Optionally add rows, trigger PR updates
    added = {"added": 0, "new_prs": []}
    if isinstance(items, list) and len(items) > 0:
        try:
            added = ds.add_workout_exercises(current_user()["id"], workout_session["id"], items)
        except (ValueError, KeyError) as e:
            return jsonify({"error": str(e)}), 400
    
    # Return full workout with rows for immediate UI feedback
    full = ds.get_workout(current_user()["id"], workout_session["id"])
    return jsonify({"workout": full, "result": added}), 201


@app.get("/api/workouts")
@login_required
def list_workouts():

    # Takes the from and to date parameters and returns list of workouts which have been filtered form that range
    from_date = request.args.get("from")
    to_date = request.args.get("to")
    items = ds.list_workouts(current_user()["id"], from_date=from_date, to_date=to_date)
    return jsonify({"items": items})

# Campus-wide workouts (for homepage stats)
@app.get("/api/workouts/campus")
def list_workouts_campus():
    items = ds.list_all_workouts()
    return jsonify({"items": items})

# -----------------------------------Leaderboards------------------------------
@app.get("/api/leaderboards/big3")
def big3():
    return jsonify({"items": ds.big3_leaderboard_sql()})


#pr's
@app.get("/api/personal-records")
@login_required
def personal_records():
    user = current_user()
    sql_id = user.get("sql_id")
    if not sql_id:
        return jsonify({"items": [], "message": "no sql server link for this account"}), 200
    items = ds.get_personal_records_sql(sql_id)
    return jsonify({"items": items})


#-------------------------------------Schedule-----------------------------------
@app.get("/api/schedule/slots")
@login_required
def list_schedule_slots():

    # Here I am returning the current user's schedule slots.
    slots = ds.list_my_slots(current_user()["id"])
    return jsonify({"items": slots})

@app.post("/api/schedule/slots")
@login_required
def create_schedule_slot():

    # Creating a new schedule slot for the current user
    error = require_json()
    if error:
        return error
    
    data = request.get_json() or {}
    start_time = (data.get("start_time") or "").strip()
    end_time = (data.get("end_time") or "").strip()
    location = (data.get("location") or "").strip()
    note = (data.get("note") or "").strip()
    visibility = (data.get("visibility") or "friends").strip()

    # Here I am doing basic validation: require start, end, and lcoation
    if not (start_time and end_time and location):
        return jsonify({"error": "Missing start time, end time, or location"}), 400

    slot = ds.create_schedule_slot(
        current_user()["id"],
        start_time=start_time,
        end_time=end_time,
        location=location,
        note=note,
        visibility=visibility,
    )

    return jsonify({"slot": slot}), 201

# ----------------------------------- Classes ---------------------------------------------

@app.get('/api/classes')
@login_required
def get_all_classes():
    try:
        classes = ds.get_classes()
        return jsonify(classes), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.post('/api/classes/create')
@login_required
def register_class():
    data = request.get_json(force=True, silent=True)
    
    # If Flask thinks it's a string, manually convert it to a dict
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return jsonify({"error": "Invalid JSON format"}), 400

    if not data or not isinstance(data, dict):
        return jsonify({"error": "Data must be a JSON object"}), 400
        
    name = (data.get("name") or "").strip()
    
    # Debugging: Check your terminal for this!
    print(f"DEBUG: Data Type: {type(data)}, Name: {name}")

    user = current_user()
    trainer_sql_id = user.get("sql_id")
    role = user.get("role")

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
    trainer_sql_id = user.get("sql_id")
    
    if user.get("role") != "trainer" or not trainer_sql_id:
        return jsonify({"error": "Only trainers can delete classes"}), 403

    try:
        result = ds.delete_class(trainer_sql_id, class_id)
        if "error" in result:
            return jsonify(result), 403
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.post("/api/classes/<int:class_id>/enroll")
@login_required
def enroll_in_class(class_id):
    user = current_user()

    print(f"DEBUG ENROLL: User={user.get('username')}, Role={user.get('role')}, SQL_ID={user.get('sql_id')}")
    
    if user.get("role") != "student":
        return jsonify({"error": "Only students can enroll in classes"}), 403

    student_sql_id = user.get("sql_id")
    if not student_sql_id:
        return jsonify({"error": "Student record not found in SQL database"}), 404

    result = ds.enroll_student(student_sql_id, class_id)
    
    if "error" in result:
        return jsonify(result), 400
        
    return jsonify(result), 200

@app.get("/api/my-classes")
@login_required
def get_my_classes():
    user = current_user()
    
    if user.get("role") != "student":
        return jsonify({"error": "Unauthorized"}), 403
        
    student_sql_id = user.get("sql_id")
    if not student_sql_id:
        return jsonify({"error": "Student profile not found"}), 404
        
    classes = ds.get_student_enrollments(student_sql_id)
    return jsonify(classes)

@app.get("/api/trainer-classes")
@login_required
def get_trainer_dashboard_classes():
    user = current_user()
    
    if user.get("role") != "trainer":
        return jsonify({"error": "Unauthorized"}), 403
        
    trainer_sql_id = user.get("sql_id")
    if not trainer_sql_id:
        return jsonify({"error": "Trainer profile not found"}), 404
        
    classes = ds.get_trainer_classes(trainer_sql_id)
    return jsonify({"items": classes})

@app.post("/api/classes/<int:class_id>/unenroll")
@login_required
def unenroll_from_class(class_id):
    user = current_user()
    if user.get("role") != "student":
        return jsonify({"error": "Only students can unenroll"}), 403

    student_sql_id = user.get("sql_id")
    result = ds.unenroll_student(student_sql_id, class_id)
    
    if "error" in result:
        return jsonify(result), 400
        
    return jsonify(result), 200

# ----------------------------------- Health ---------------------------------------------
@app.get("/api/health")
def health():
    return jsonify({"ok": True, "time": dataservice.now_iso()})



# -------------------------------------Main----------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
