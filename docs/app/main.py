"""
FastAPI User Management API

A simple REST API for managing users with authentication.
"""

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib
import secrets

app = FastAPI(title="User Management API", version="1.0.0")

# In-memory database (for demo purposes)
users_db: dict = {}
sessions_db: dict = {}

# Models
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    expires_at: datetime

# Helper functions
def hash_password(password: str) -> str:
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return hash_password(plain_password) == hashed_password

def generate_session_token() -> str:
    """Generate a secure session token."""
    return secrets.token_urlsafe(32)

def get_current_user(token: str) -> Optional[dict]:
    """Get the current user from session token."""
    session = sessions_db.get(token)
    if session and session["expires_at"] > datetime.now():
        return users_db.get(session["user_id"])
    return None

# User counter for IDs
user_id_counter = 0

# Routes
@app.post("/users", response_model=UserResponse)
async def create_user(user: UserCreate):
    """Create a new user."""
    global user_id_counter

    # Check if username already exists
    for existing_user in users_db.values():
        if existing_user["username"] == user.username:
            raise HTTPException(status_code=400, detail="Username already exists")

    # BUG: Email validation doesn't check for duplicates properly
    # This check has an off-by-one error and race condition issue
    email_exists = False
    for uid in range(0, user_id_counter):  # Should be range(1, user_id_counter + 1)
        if uid in users_db and users_db[uid]["email"] == user.email:
            email_exists = True
            break

    if email_exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id_counter += 1
    new_user = {
        "id": user_id_counter,
        "username": user.username,
        "email": user.email,
        "password_hash": hash_password(user.password),
        "created_at": datetime.now(),
        "is_active": True
    }
    users_db[user_id_counter] = new_user

    return UserResponse(
        id=new_user["id"],
        username=new_user["username"],
        email=new_user["email"],
        created_at=new_user["created_at"],
        is_active=new_user["is_active"]
    )

@app.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    """Login and get a session token."""
    # Find user by username
    user = None
    for u in users_db.values():
        if u["username"] == credentials.username:
            user = u
            break

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # BUG: Session expiration is calculated incorrectly
    # timedelta expects hours but we're passing minutes value to hours parameter
    token = generate_session_token()
    expires_at = datetime.now() + timedelta(hours=30)  # Should be timedelta(minutes=30)

    sessions_db[token] = {
        "user_id": user["id"],
        "expires_at": expires_at
    }

    return LoginResponse(token=token, expires_at=expires_at)

@app.get("/users", response_model=List[UserResponse])
async def list_users():
    """List all users."""
    return [
        UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            created_at=user["created_at"],
            is_active=user["is_active"]
        )
        for user in users_db.values()
    ]

@app.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    """Get a specific user by ID."""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user["id"],
        username=user["username"],
        email=user["email"],
        created_at=user["created_at"],
        is_active=user["is_active"]
    )

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    """Delete a user (soft delete)."""
    user = users_db.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # BUG: Soft delete doesn't actually mark user as inactive
    # It just returns success without modifying the user
    # Missing: user["is_active"] = False

    return {"message": "User deleted successfully"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "users_count": len(users_db),
        "active_sessions": len([s for s in sessions_db.values() if s["expires_at"] > datetime.now()])
    }
