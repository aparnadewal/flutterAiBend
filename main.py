from fastapi import FastAPI, HTTPException, Header, Form
from typing import Optional, List
from database import init_db, get_db
from auth import hash_password, verify_password, create_token, decode_token
import json

app = FastAPI()

# DB start karo
init_db()

# ── ROOT ENDPOINT ──
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
    cursor = db.cursor()
    
    # Phone already exists check
    existing = cursor.execute(
        "SELECT id FROM users WHERE phone = ?", 
        (phone,)
    ).fetchone()
    
    if existing:
        db.close()
        raise HTTPException(status_code=400, detail="Phone already registered")
    
    # Save user
    hashed = hash_password(password)
    cursor.execute(
        "INSERT INTO users (name, phone, email, password) VALUES (?, ?, ?, ?)",
        (name, phone, email, hashed)
    )
    db.commit()
    user_id = cursor.lastrowid
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
    cursor = db.cursor()
    
    user = cursor.execute(
        "SELECT * FROM users WHERE phone = ?", 
        (phone,)
    ).fetchone()
    db.close()
    
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Wrong phone or password")
    
    token = create_token(user["id"])
    return {
        "success": True,
        "token": token,
        "user_id": user["id"],
        "name": user["name"]
    }

# ── PROFILE SAVE ──
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
    cursor = db.cursor()
    
    skills_json = json.dumps(skills.split(","))
    
    # Already exists toh update, warna insert
    existing = cursor.execute(
        "SELECT id FROM profiles WHERE user_id = ?", 
        (user_id,)
    ).fetchone()
    
    if existing:
        cursor.execute(
            "UPDATE profiles SET skills=?, experience=?, location=? WHERE user_id=?",
            (skills_json, experience, location, user_id)
        )
    else:
        cursor.execute(
            "INSERT INTO profiles (user_id, skills, experience, location) VALUES (?, ?, ?, ?)",
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
    cursor = db.cursor()
    
    user = cursor.execute(
        "SELECT name, phone, email FROM users WHERE id = ?", 
        (user_id,)
    ).fetchone()
    
    profile = cursor.execute(
        "SELECT skills, experience, location FROM profiles WHERE user_id = ?", 
        (user_id,)
    ).fetchone()
    db.close()
    
    return {
        "name": user["name"],
        "phone": user["phone"],
        "email": user["email"],
        "skills": json.loads(profile["skills"]) if profile and profile["skills"] else [],
        "experience": profile["experience"] if profile else 0,
        "location": profile["location"] if profile else ""
    }