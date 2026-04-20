from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

SECRET_KEY = "tumhari-app-secret-key-change-this"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def create_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=30)
    return jwt.encode(
        {"user_id": user_id, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("user_id")
    except:
        return None