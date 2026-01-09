from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote_plus
from functools import wraps
from datetime import datetime,timedelta
from flask_mail import Mail, Message
from dotenv import load_dotenv
import random
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("APP_SECRET_KEY")
# Mail configuration
app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER")
app.config["MAIL_PORT"] = os.getenv("MAIL_PORT")
app.config["MAIL_USE_TLS"] = os.getenv("MAIL_USE_TLS")
app.config["MAIL_USERNAME"] = os.getenv("ADMIN_EMAIL")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")  # Gmail App Password
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)
# MongoDB storage
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["civicfix"]
problems_collection = db["problems"]
users_collection = db["users"]
votes_collection = db["votes"]
likes_collection = db["likes"]

# Upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

CATEGORY_WEIGHTS = {
    "Road / Pothole": 3,
    "Garbage": 4,
    "Water Supply": 5,
    "Drainage": 5,
    "Electricity": 4,
    "Public Safety": 7,
    "Education":7,
    "Healthcare":9,
    "Corruption":10,
    "Pollution":6,
    "Woman Safety":8,
    "Child Labour":6,
    "Illiteracy":7,
    "Poverty":6,
    "Environment":6,
    "Other":6
}


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            # AJAX / fetch request
            if request.headers.get("Accept") == "application/json":
                return jsonify({"error": "LOGIN_REQUIRED"}), 401
            return jsonify({"error": "LOGIN_REQUIRED"}), 401
        return view_func(*args, **kwargs)
    return wrapped

def calculate_priority(problem):
    votes_score = problem.get("votes", 0) * 2
    days_pending = (datetime.utcnow() - problem["created_at"]).days
    category_score = CATEGORY_WEIGHTS.get(problem.get("category"), 1)
    verification_bonus = 5 if problem.get("is_verified") else 0

    return votes_score + days_pending + category_score + verification_bonus

def get_top_priority_issue_ids(limit=5):
    problems = list(problems_collection.find())
    for p in problems:
        p["priority_score"] = calculate_priority(p)
    problems.sort(key=lambda x: x["priority_score"], reverse=True)
    return set(p["_id"] for p in problems[:limit])

@app.route("/submit", methods=["POST"])
def submit_problem():
    if "user_id" not in session:
        return redirect(url_for("login"))
    category = request.form.get("category")
    description = request.form.get("description")
    long_des = request.form.get("long_des")
    latitude = float(request.form.get("latitude"))
    longitude = float(request.form.get("longitude"))
    area_name = request.form.get("area_name") 
    image = request.files.get("image")
    # ✅ Verification for latitude & longitude
    if not latitude or not longitude:
        return jsonify({"error": "Location is required"}), 400
    filename = None
    if image and image.filename != "":
        filename = secure_filename(image.filename)
        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    problem = {
        "category": category,
        "description": description,
        "long_des": long_des,
        # 📍 LOCATION DATA
        "location": {
            "type": "Point",
            "coordinates": [longitude, latitude],  # IMPORTANT: lng first
            "area_name": area_name
        },
        "image": f"uploads/{filename}" if filename else None,
        "status": "pending",
        "votes": 0,
        "is_verified": False,
        "likes":0, 
        "user_id": ObjectId(session["user_id"]), # 🔥 ownership
        "reported_by": session.get("name"),
        "created_at": datetime.utcnow(),
    }
    problems_collection.insert_one(problem)
    return redirect(url_for("home"))

@app.route("/vote/<problem_id>", methods=["POST"])
def vote(problem_id):

    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    user_id = session["user_id"]

    problem = problems_collection.find_one({"_id": ObjectId(problem_id)})
    if not problem:
        return jsonify({"error": "Problem not found"}), 404

    existing_vote = votes_collection.find_one({
        "user_id": ObjectId(user_id),
        "problem_id": ObjectId(problem_id)
    })

    if existing_vote:
        return jsonify({"error": "Already voted"}), 400

    votes_collection.insert_one({
        "user_id": ObjectId(user_id),
        "problem_id": ObjectId(problem_id),
        "created_at": datetime.utcnow()
    })

    problems_collection.update_one(
        {"_id": ObjectId(problem_id)},
        {"$inc": {"votes": 1}}
    )

    updated_problem = problems_collection.find_one({"_id": ObjectId(problem_id)})

    return jsonify({"votes": updated_problem["votes"]})

@app.route("/like/<problem_id>", methods=["POST"])
def like(problem_id):

    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    user_id = session["user_id"]

    # ✅ Allow likes ONLY for resolved problems
    problem = problems_collection.find_one({
        "_id": ObjectId(problem_id),
        "status": "Resolved"
    })

    if not problem:
        return jsonify({"error": "Invalid problem"}), 400

    # 🔒 Check if user already liked
    existing_like = likes_collection.find_one({
        "user_id": ObjectId(user_id),
        "problem_id": ObjectId(problem_id)
    })

    if existing_like:
        return jsonify({"error": "Already liked"}), 400

    # ✅ Record like
    likes_collection.insert_one({
        "user_id": ObjectId(user_id),
        "problem_id": ObjectId(problem_id),
        "created_at": datetime.utcnow()
    })

    # ✅ Increment like count
    problems_collection.update_one(
        {"_id": ObjectId(problem_id)},
        {"$inc": {"likes": 1}}
    )

    updated_problem = problems_collection.find_one(
        {"_id": ObjectId(problem_id)}
    )

    return jsonify({
        "likes": updated_problem.get("likes", 0)
    })
    
@app.route("/update_status/<issue_id>", methods=["POST"])
def update_status(issue_id):
    user = users_collection.find_one(
        {"_id": ObjectId(session["user_id"])}
    )
    if user["email"] != os.getenv("ADMIN_EMAIL"):
        return "Unauthorized", 403

    new_status = request.form.get("status")

    if new_status not in ["Pending", "Acknowledged", "Resolved"]:
        return "Invalid status", 400

    problems_collection.update_one(
        {"_id": ObjectId(issue_id)},
        {"$set": {"status": new_status}}
    )

    return redirect(request.referrer)

@app.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    pending = session.get("pending_user")

    if not pending:
        return redirect("/register")

    if request.method == "POST":
        entered_otp = request.form["otp"]

        if entered_otp != pending["otp"]:
            return "Invalid OTP"

        # Check expiry
        if datetime.utcnow() > datetime.fromisoformat(pending["expires"]):
            session.pop("pending_user", None)
            return "OTP expired. Please register again."

        # ✅ Create user NOW
        users_collection.insert_one({
            "name": pending["name"],
            "email": pending["email"],
            "password": pending["password"],
            "created_at": datetime.utcnow(),
            "is_verified": True
        })

        session.pop("pending_user", None)

        return redirect("/login")
    return render_template("verify_otp.html")

#--------------------- All Routes here --------------------------#
@app.route("/")
@app.route("/home")
def home():
    problems = list(
        problems_collection.find({"status": "pending"})
    )

    for problem in problems:
        problem["priority_score"] = calculate_priority(problem)

    # 🔥 SORT BY PRIORITY (DESC)
    problems.sort(key=lambda x: x["priority_score"], reverse=True)
    
    # 🔥 Mark top 5
    top_ids = set(p["_id"] for p in problems[:5])
    for problem in problems:
        problem["is_top_priority"] = problem["_id"] in top_ids

    return render_template(
        "home.html",
        problems=problems,
        admin_email=os.getenv("ADMIN_EMAIL")
    )

@app.route("/add_problem")
def add_problem():
    return render_template("add_problem.html")

@app.route("/issue/<issue_id>")
def issue_detail(issue_id):
    problem = problems_collection.find_one(
        {"_id": ObjectId(issue_id)}
    )

    if not problem:
        abort(404)

    priority_score = calculate_priority(problem)

    # ✅ compute top 5 dynamically
    top_ids = get_top_priority_issue_ids()
    is_top_priority = problem["_id"] in top_ids

    return render_template(
        "issue_detail.html",
        problem=problem,
        priority_score=priority_score,
        is_top_priority=is_top_priority
    )

@app.route("/export/<problem_id>")
def export_issue(problem_id):
    problem = problems_collection.find_one(
        {"_id": ObjectId(problem_id)}
    )

    if not problem:
        return "Issue not found", 404

    # Recalculate priority
    problem["priority_score"] = calculate_priority(problem)

    # Get top 5 IDs again (backend truth)
    problems = list(problems_collection.find())
    for p in problems:
        p["priority_score"] = calculate_priority(p)

    problems.sort(key=lambda x: x["priority_score"], reverse=True)
    top_ids = set(p["_id"] for p in problems[:5])

    # 🔒 HARD CHECK
    if not problem.get("is_verified") or problem["_id"] not in top_ids:
        return "Export not allowed for this issue", 403

    return render_template(
        "export_issue.html",
        problem=problem,
        priority_score=problem["priority_score"]
    )

@app.route("/my_issues")
def my_issues():
    if "user_id" not in session:
        abort(401)

    issues = list(
        problems_collection.find(
            {"user_id": ObjectId(session["user_id"])}
        )
    )

    # ✅ calculate priority for each issue
    for issue in issues:
        issue["priority_score"] = calculate_priority(issue)

    return render_template(
        "my_issues.html",
        issues=issues
    )
@app.route("/impact")
def impact():

    in_progress = list(
        problems_collection.find({"status": "Acknowledged"})
        .sort("created_at", -1)
    )

    resolved = list(
        problems_collection.find({"status": "Resolved"})
        .sort("created_at", -1)
    )

    user_id = session.get("user_id")

    # Process resolved problems safely
    for problem in resolved:
        problem["likes"] = problem.get("likes", 0)

        if user_id:
            liked = likes_collection.find_one({
                "user_id": ObjectId(user_id),
                "problem_id": problem["_id"]
            })
            problem["has_liked"] = bool(liked)
        else:
            problem["has_liked"] = False

    stats = {
        "reported": problems_collection.count_documents({}),
        "pending": problems_collection.count_documents({"status": "Pending"}),
        "in_progress": len(in_progress),
        "resolved": len(resolved),
    }

    return render_template(
        "impact.html",
        in_progress=in_progress,
        resolved=resolved,
        stats=stats
    )
    
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect("/login")

    user = users_collection.find_one(
        {"_id": ObjectId(session["user_id"])},
        {"password": 0}  # exclude password
    )

    # stats (optional)
    total_votes = votes_collection.count_documents(
        {"user_id": ObjectId(session["user_id"])}
    )

    return render_template(
        "profile.html",
        user=user,
        total_votes=total_votes
    )

@app.route("/profile/update", methods=["POST"])
def update_profile():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    name = request.form.get("name")

    users_collection.update_one(
        {"_id": ObjectId(session["user_id"])},
        {"$set": {"name": name}}
    )

    return jsonify({"success": True})

@app.route("/profile/password", methods=["POST"])
def change_password():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    current = request.form.get("current_password")
    new = request.form.get("new_password")

    user = users_collection.find_one(
        {"_id": ObjectId(session["user_id"])}
    )

    if not check_password_hash(user["password"], current):
        return jsonify({"error": "Wrong current password"}), 400

    users_collection.update_one(
        {"_id": ObjectId(session["user_id"])},
        {"$set": {"password": generate_password_hash(new)}}
    )

    return jsonify({"success": True})

@app.route("/working")
def working():
    return render_template("works.html")

@app.route("/community-guidelines")
def community_guidelines():
    return render_template("community_guidelines.html")

@app.route("/terms")
def terms():
    return render_template("terms.html")

@app.route("/privacy")
def privacy():
    return render_template("privacy.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    otp_sent = False
    error = None

    if request.method == "POST":

        # STEP 2: OTP verification
        if "otp" in request.form:
            pending = session.get("pending_user")

            if not pending:
                error = "Session expired. Please register again."
                return render_template("register.html", otp_sent=False, error=error)

            if request.form["otp"] != pending["otp"]:
                error = "Invalid OTP"
                return render_template("register.html", otp_sent=True, error=error)

            if datetime.utcnow() > datetime.fromisoformat(pending["expires"]):
                session.pop("pending_user", None)
                error = "OTP expired. Please try again."
                return render_template("register.html", otp_sent=False, error=error)

            # ✅ Create user
            users_collection.insert_one({
                "name": pending["name"],
                "email": pending["email"],
                "password": pending["password"],
                "created_at": datetime.utcnow(),
                "is_verified": True
            })

            session.pop("pending_user", None)
            session["toast_success"] = "Account created successfully! Please log in."
            return redirect("/login")

        # STEP 1: Registration → Send OTP
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        if users_collection.find_one({"email": email}):
            error = "Email already registered"
            return render_template("register.html", otp_sent=False, error=error)

        otp = str(random.randint(100000, 999999))

        session["pending_user"] = {
            "name": name,
            "email": email,
            "password": generate_password_hash(password),
            "otp": otp,
            "expires": (datetime.utcnow() + timedelta(minutes=5)).isoformat()
        }

        # 🔔 Send email
        msg = Message(
            subject="Your CivicFix OTP",
            recipients=[email],
            body=f"Your OTP is {otp}. Valid for 5 minutes."
        )
        mail.send(msg)

        otp_sent = True

    return render_template("register.html", otp_sent=otp_sent, error=error)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = users_collection.find_one({"email": email})

        if not user or not check_password_hash(user["password"], password):
            return render_template("login.html", error="Invalid credentials")

        # Store user session
        session["user_id"] = str(user["_id"])
        session["name"] = user["name"]
        session["email"] = user["email"]
        next_page = request.args.get("next")
        return redirect(next_page or url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/admin/dashboard")
def admin_dashboard():

    # 🔒 Admin check
    if session.get("email") != os.getenv("ADMIN_EMAIL"):
        return "Unauthorized", 403

    total_issues = problems_collection.count_documents({})
    resolved_issues = problems_collection.count_documents({"status": "Resolved"})
    pending_issues = problems_collection.count_documents({"status": "Pending"})
    in_progress_issues = problems_collection.count_documents({"status": "Acknowledged"})

    # Category-wise count
    category_stats = list(problems_collection.aggregate([
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))

    # Area-wise count (top 5)
    area_stats = list(problems_collection.aggregate([
        {"$group": {"_id": "$location.area_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]))

    return render_template(
        "admin_dashboard.html",
        total_issues=total_issues,
        resolved_issues=resolved_issues,
        pending_issues=pending_issues,
        in_progress_issues=in_progress_issues,
        category_stats=category_stats,
        area_stats=area_stats
    )

if __name__ == "__main__":
    app.run(debug=True)