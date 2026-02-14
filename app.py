from flask import Flask, render_template, request, jsonify
import mediapipe as mp
import cv2
import numpy as np
import base64
import os
import json

app = Flask(__name__)

mp_face_mesh = mp.solutions.face_mesh

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f)

def calculate_symmetry(landmarks):
    left = landmarks[33]
    right = landmarks[263]
    nose = landmarks[1]

    d1 = abs(left.x - nose.x)
    d2 = abs(right.x - nose.x)

    diff = abs(d1 - d2)
    symmetry_score = max(0, 1 - diff*5)
    return symmetry_score

def golden_ratio_score(landmarks):
    chin = landmarks[152]
    forehead = landmarks[10]
    face_height = abs(chin.y - forehead.y)

    left_cheek = landmarks[234]
    right_cheek = landmarks[454]
    face_width = abs(left_cheek.x - right_cheek.x)

    ratio = face_height / face_width if face_width != 0 else 1
    ideal = 1.618

    diff = abs(ratio - ideal)
    score = max(0, 1 - diff)
    return score

def get_tier(score):
    if score < 5: return "sub5"
    if score < 6: return "ltn"
    if score < 7: return "mtn"
    if score < 8: return "htn"
    if score < 8.8: return "chadlite"
    if score < 9.5: return "chad"
    return "true adam"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.json
    img_data = data["image"].split(",")[1]
    user_id = data.get("user_id", "guest")

    img_bytes = base64.b64decode(img_data)
    np_arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    with mp_face_mesh.FaceMesh(static_image_mode=True) as face_mesh:
        results = face_mesh.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        if not results.multi_face_landmarks:
            return jsonify({"error": "Face not found"})

        landmarks = results.multi_face_landmarks[0].landmark

        sym = calculate_symmetry(landmarks)
        golden = golden_ratio_score(landmarks)

        final_score = (sym*0.5 + golden*0.5) * 10
        final_score = round(final_score, 2)

        tier = get_tier(final_score)

        users = load_users()
        is_pro = users.get(str(user_id), {}).get("pro", False)

        response = {
            "score": final_score,
            "tier": tier,
            "symmetry": round(sym*10,2),
            "golden_ratio": round(golden*10,2),
            "pro": is_pro
        }

        if is_pro:
            response["tips"] = [
                "Lower body fat %",
                "Improve jawline via gym",
                "Skin care routine",
                "Hairstyle optimization"
            ]

        return jsonify(response)

@app.route("/activate_pro", methods=["POST"])
def activate_pro():
    data = request.json
    user_id = str(data["user_id"])

    users = load_users()
    users[user_id] = {"pro": True}
    save_users(users)

    return jsonify({"status": "PRO activated"})

if name == "__main__":
    app.run()
