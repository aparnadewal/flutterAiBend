from fastapi import FastAPI, HTTPException, Header, Form
from typing import Optional
from database import init_db, get_db
from auth import hash_password, verify_password, create_token, decode_token
import json
import psycopg2.extras

app = FastAPI()

init_db()

@app.get("/")
def root():
    return {"message": "Flutter AI Backend API", "docs": "/docs", "status": "running"}

# ── REGISTER ──
@app.post("/register")
def register(
    name: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(None),
    password: str = Form(...)
):
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT id FROM users WHERE phone = %s", (phone,))
    if cursor.fetchone():
        db.close()
        raise HTTPException(status_code=400, detail="Phone already registered")

    hashed = hash_password(password)
    cursor.execute(
        "INSERT INTO users (name, phone, email, password) VALUES (%s, %s, %s, %s) RETURNING id",
        (name, phone, email, hashed)
    )
    user_id = cursor.fetchone()["id"]
    db.commit()
    db.close()

    token = create_token(user_id)
    return {"success": True, "token": token, "user_id": user_id}

# ── LOGIN ──
@app.post("/login")
def login(
    phone: str = Form(...),
    password: str = Form(...)
):
    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT * FROM users WHERE phone = %s", (phone,))
    user = cursor.fetchone()
    db.close()

    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Wrong phone or password")

    token = create_token(user["id"])
    return {"success": True, "token": token, "user_id": user["id"], "name": user["name"]}

# ── SAVE PROFILE ──
@app.post("/save-profile")
def save_profile(
    skills: str = Form(...),
    experience: int = Form(...),
    location: str = Form(...),
    authorization: str = Header(...)
):
    user_id = decode_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    skills_json = json.dumps(skills.split(","))

    cursor.execute("SELECT id FROM profiles WHERE user_id = %s", (user_id,))
    if cursor.fetchone():
        cursor.execute(
            "UPDATE profiles SET skills=%s, experience=%s, location=%s WHERE user_id=%s",
            (skills_json, experience, location, user_id)
        )
    else:
        cursor.execute(
            "INSERT INTO profiles (user_id, skills, experience, location) VALUES (%s, %s, %s, %s)",
            (user_id, skills_json, experience, location)
        )

    db.commit()
    db.close()
    return {"success": True, "message": "Profile saved!"}

# ── GET PROFILE ──
@app.get("/profile")
def get_profile(authorization: str = Header(...)):
    user_id = decode_token(authorization)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    db = get_db()
    cursor = db.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT name, phone, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT skills, experience, location FROM profiles WHERE user_id = %s", (user_id,))
    profile = cursor.fetchone()
    db.close()

    return {
        "name": user["name"],
        "phone": user["phone"],
        "email": user["email"],
        "skills": json.loads(profile["skills"]) if profile and profile["skills"] else [],
        "experience": profile["experience"] if profile else 0,
        "location": profile["location"] if profile else ""
    }
