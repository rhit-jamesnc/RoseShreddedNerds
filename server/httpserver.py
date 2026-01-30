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
        user = ds.create_user(first_name=first_name, last_name=last_name, username=username, password_hash=generate_password_hash(password), dob=dob, weight=weight)
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    
    # Start session
    session["user_id"] = user["id"]
    session.permanent = True
    ds.update_user(user_id=user["id"], last_login_at=dataservice.now_iso())

    return jsonify({"user": user}), 201

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
    return jsonify({"items": ds.big3_leaderboard()})


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

# ----------------------------------- Health ---------------------------------------------
@app.get("/api/health")
def health():
    return jsonify({"ok": True, "time": dataservice.now_iso()})



# -------------------------------------Main----------------------------------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080, debug=True)
