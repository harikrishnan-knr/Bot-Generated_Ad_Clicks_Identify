# app.py
import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import joblib
import pandas as pd
import numpy as np
from datetime import datetime

app = Flask(__name__)
app.secret_key = "replace_with_a_secure_random_secret"  # change for production

# -------------------------
# Config
# -------------------------
MODEL_PATH = os.path.join("model", "model.pkl")
FEATURES_PATH = os.path.join("model", "features.pkl")
USERS_FILE = "users.json"

# Background image provided by you (used in templates)
BACKGROUND_IMAGE_URL = "https://media.istockphoto.com/id/2224177627/photo/fraud-detection-and-cyber-security.jpg?s=2048x2048&w=is&k=20&c=g2iHz5Jqnyxv5WEic4DCYaeQac6bEJutbHYbxkggKro="

# -------------------------
# Load model & features (if available)
# -------------------------
model = None
features = None
if os.path.exists(MODEL_PATH) and os.path.exists(FEATURES_PATH):
    try:
        model = joblib.load(MODEL_PATH)
        features = joblib.load(FEATURES_PATH)
        print("Loaded model and feature list.")
    except Exception as e:
        print("Failed to load model:", e)
else:
    print("Model not found. Place model.pkl and features.pkl inside ./model/ to enable predictions.")

# -------------------------
# Simple user store helpers
# -------------------------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)

# ensure users file exists
if not os.path.exists(USERS_FILE):
    save_users({})

# -------------------------
# Routes
# -------------------------
@app.context_processor
def inject_globals():
    # make background available in all templates
    return dict(BG_IMAGE=BACKGROUND_IMAGE_URL)

@app.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("overview"))
    return redirect(url_for("login"))

# ----- Register -----
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = load_users()
        username = request.form.get("username", "").strip().lower()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not username or not password:
            flash("Please provide username and password.", "danger")
            return redirect(url_for("register"))

        if username in users:
            flash("Username already exists. Please choose another.", "warning")
            return redirect(url_for("register"))

        # store user (note: plain text password for demo only; hash in production)
        users[username] = {"email": email, "password": password}
        save_users(users)
        flash("Registration successful — please log in.", "success")
        return redirect(url_for("login"))

    return render_template("register.html")

# ----- Login -----
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = load_users()
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "").strip()
        u = users.get(username)
        if u and u.get("password") == password:
            session["user"] = username
            flash("Login successful!", "success")
            return redirect(url_for("overview"))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))

    return render_template("login.html")

# ----- Logout -----
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Logged out.", "info")
    return redirect(url_for("login"))

# ----- Overview -----
@app.route("/overview")
def overview():
    if not session.get("user"):
        return redirect(url_for("login"))

    # quick dataset/model stats (if model present)
    stats = {}
    if features:
        stats["features_count"] = len(features)
    else:
        stats["features_count"] = "Model not loaded"

    # you can extend this to show training metrics loaded from disk
    return render_template("overview.html", stats=stats, user=session.get("user"))

# ----- Predict page -----
@app.route("/predict", methods=["GET", "POST"])
def predict_page():
    if not session.get("user"):
        return redirect(url_for("login"))

    if request.method == "POST":
        if model is None or features is None:
            flash("Model not available. Place model.pkl and features.pkl in ./model/", "danger")
            return redirect(url_for("predict_page"))

        # Form data to DataFrame
        payload = {}
        for f in features:
            v = request.form.get(f)
            # cast to numeric when possible
            try:
                if v is None or v == "":
                    payload[f] = np.nan
                else:
                    # detect ints/floats
                    if "." in v:
                        payload[f] = float(v)
                    else:
                        payload[f] = int(v)
            except:
                payload[f] = v

        row = pd.DataFrame([payload])
        # prediction
        try:
            pred = int(model.predict(row)[0])
            prob = float(model.predict_proba(row)[0][1]) if hasattr(model, "predict_proba") else None
        except Exception as e:
            flash(f"Prediction error: {e}", "danger")
            return redirect(url_for("predict_page"))

        return render_template("predict.html", pred=pred, prob=prob, features=features, user=session.get("user"))

    # GET: show page
    return render_template("predict.html", pred=None, prob=None, features=features, user=session.get("user"))

# ----- API predict (JSON) -----
@app.route("/api/predict", methods=["POST"])
def api_predict():
    if model is None or features is None:
        return jsonify({"error": "Model not loaded"}), 400

    if not request.is_json:
        return jsonify({"error": "Send JSON body"}), 400

    data = request.get_json()
    # create row with same feature order
    row = {f: data.get(f, None) for f in features}
    df = pd.DataFrame([row])
    # try numeric conversion
    for c in df.columns:
        try:
            df[c] = pd.to_numeric(df[c])
        except:
            pass

    try:
        pred = int(model.predict(df)[0])
        prob = float(model.predict_proba(df)[0][1]) if hasattr(model, "predict_proba") else None
        return jsonify({"prediction": pred, "probability": prob})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------
# Run
# -------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5000)
