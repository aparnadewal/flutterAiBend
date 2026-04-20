from pydantic import BaseModel
from typing import List, Optional

class RegisterModel(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    password: str

class LoginModel(BaseModel):
    phone: str
    password: str

class ProfileModel(BaseModel):
    skills: List[str]
    experience: int
    location: str