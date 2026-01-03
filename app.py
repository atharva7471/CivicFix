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

# Upload folder
UPLOAD_FOLDER = "static/uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

#--------------------- All Routes here --------------------------#
@app.route("/")
@app.route("/home")

def home():
    problems = list(
        problems_collection.find().sort("created_at", -1)
    )
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

@app.route("/my_issues")
def my_issues():
    user_id = ObjectId(session["user_id"])

    issues = list(
        problems_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1)
    )
    return render_template(
        "my_issues.html",
        issues=issues,
        admin_email=os.getenv("ADMIN_EMAIL")
    )  

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

if __name__ == "__main__":
    app.run(debug=True)