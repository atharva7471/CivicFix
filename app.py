from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote_plus
from functools import wraps
from datetime import datetime
from dotenv import load_dotenv
import os

app = Flask(__name__)
load_dotenv()
app.secret_key = os.getenv("APP_SECRET_KEY")

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
    "Public Safety": 6,
    "Other": 4
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

@app.route("/submit", methods=["POST"])
def submit_problem():
    if "user_id" not in session:
        return redirect(url_for("login"))
    category = request.form.get("category")
    description = request.form.get("description")
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
        # 📍 LOCATION DATA
        "location": {
            "type": "Point",
            "coordinates": [longitude, latitude],  # IMPORTANT: lng first
            "area_name": area_name
        },
        "image": f"uploads/{filename}" if filename else None,
        "status": "pending",
        "votes": 0,
        "is_verified": True,
        "likes":0, 
        "user_id": ObjectId(session["user_id"]), # 🔥 ownership
        "created_at": datetime.utcnow(),
    }
    problems_collection.insert_one(problem)
    return redirect(url_for("home"))

@app.route("/vote/<problem_id>", methods=["POST"])
def vote(problem_id):

    if "user_id" not in session:
        return jsonify({"error": "Login required"}), 401

    user_id = session["user_id"]

    # Check if this user already voted on this problem
    existing_vote = votes_collection.find_one({
        "user_id": ObjectId(user_id),
        "problem_id": ObjectId(problem_id)
    })

    if existing_vote:
        return jsonify({"error": "Already voted"}), 400

    # Record vote
    votes_collection.insert_one({
        "user_id": ObjectId(user_id),
        "problem_id": ObjectId(problem_id),
        "created_at": datetime.utcnow()
    })

    # Increment problem vote count
    problems_collection.update_one(
        {"_id": ObjectId(problem_id)},
        {"$inc": {"votes": 1}}
    )
        
    problem = problems_collection.find_one({"_id": problem.obj_id})

    # 🔥 AUTO-VERIFY AFTER 5 VOTES
    if problem["votes"] >= 5 and not problem.get("is_verified"):
        problems_collection.update_one(
            {"_id": problem.obj_id},
            {"$set": {"is_verified": True}}
        )
    return jsonify({"votes": problem["votes"]})

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
    user_id = ObjectId(session["user_id"])

    issues = list(
        problems_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1)
    )
    for issue in issues:
        issue["priority_score"] = calculate_priority(issue)

    # 🔥 SORT BY PRIORITY (DESC)
    issues.sort(key=lambda x: x["priority_score"], reverse=True)
    
    return render_template(
        "my_issues.html",
        issues=issues,
        admin_email=os.getenv("ADMIN_EMAIL")
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

    # Safe defaults
    for problem in resolved:
        problem["likes"] = problem.get("likes", 0)

    if "user_id" in session:
        liked = likes_collection.find_one({
            "user_id": ObjectId(session["user_id"]),
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


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        # Check if user already exists
        if users_collection.find_one({"email": email}):
            return "User already exists"

        hashed_password = generate_password_hash(password)

        users_collection.insert_one({
            "name": name,
            "email": email,
            "password": hashed_password,
            "created_at": datetime.utcnow()
        })

        return redirect(url_for("login"))
    return render_template("register.html")

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
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
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
    if session.get("user_email") != os.getenv("ADMIN_EMAIL"):
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