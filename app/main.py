from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel, EmailStr
from .core.database import get_db_cursor
from .core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token
)
from .core.config import get_settings

settings = get_settings()
app = FastAPI(title="User Profile Audit System")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Models
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

class UserAudit(UserBase):
    version: int
    action: str
    changed_at: datetime
    changed_by: Optional[str]

class Token(BaseModel):
    access_token: str
    token_type: str

# Dependencies
async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception
    return payload

# Auth endpoints
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, password_hash FROM users WHERE email = %s",
            (form_data.username,)
        )
        user = cursor.fetchone()
        
        if not user or not verify_password(form_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(user["id"])},
            expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}

# User endpoints
@app.post("/users", response_model=User)
async def create_user(user: UserCreate):
    with get_db_cursor() as cursor:
        # Check if email already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (user.email,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create user
        cursor.execute(
            """
            INSERT INTO users (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING id, name, email, created_at, updated_at
            """,
            (user.name, user.email, get_password_hash(user.password))
        )
        new_user = cursor.fetchone()
        
        # Create audit entry
        cursor.execute(
            """
            INSERT INTO user_audit (user_id, version, name, email, action)
            VALUES (%s, 1, %s, %s, 'CREATE')
            """,
            (new_user["id"], user.name, user.email)
        )
        
        return new_user

@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int, current_user: dict = Depends(get_current_user)):
    with get_db_cursor() as cursor:
        cursor.execute(
            "SELECT id, name, email, created_at, updated_at FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

@app.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: int,
    user_update: UserBase,
    current_user: dict = Depends(get_current_user)
):
    with get_db_cursor() as cursor:
        # Check if user exists
        cursor.execute(
            "SELECT version FROM user_audit WHERE user_id = %s ORDER BY version DESC LIMIT 1",
            (user_id,)
        )
        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        next_version = result["version"] + 1
        
        # Update user
        cursor.execute(
            """
            UPDATE users
            SET name = %s, email = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id, name, email, created_at, updated_at
            """,
            (user_update.name, user_update.email, user_id)
        )
        updated_user = cursor.fetchone()
        
        # Create audit entry
        cursor.execute(
            """
            INSERT INTO user_audit (user_id, version, name, email, action, changed_by)
            VALUES (%s, %s, %s, %s, 'UPDATE', %s)
            """,
            (user_id, next_version, user_update.name, user_update.email, current_user.get("sub"))
        )
        
        return updated_user

@app.delete("/users/{user_id}")
async def delete_user(user_id: int, current_user: dict = Depends(get_current_user)):
    with get_db_cursor() as cursor:
        # Get latest version
        cursor.execute(
            "SELECT version FROM user_audit WHERE user_id = %s ORDER BY version DESC LIMIT 1",
            (user_id,)
        )
        result = cursor.fetchone()
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        next_version = result["version"] + 1
        
        # Get user data before deletion
        cursor.execute(
            "SELECT name, email FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()
        
        # Create audit entry before deletion
        cursor.execute(
            """
            INSERT INTO user_audit (user_id, version, name, email, action, changed_by)
            VALUES (%s, %s, %s, %s, 'DELETE', %s)
            """,
            (user_id, next_version, user["name"], user["email"], current_user.get("sub"))
        )
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        
        return {"message": "User deleted successfully"}

@app.get("/audit/users/{user_id}", response_model=List[UserAudit])
async def get_user_audit(
    user_id: int,
    current_user: dict = Depends(get_current_user)
):
    with get_db_cursor() as cursor:
        cursor.execute(
            """
            SELECT version, name, email, action, changed_at, changed_by
            FROM user_audit
            WHERE user_id = %s
            ORDER BY version DESC
            """,
            (user_id,)
        )
        audit_entries = cursor.fetchall()
        if not audit_entries:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No audit entries found for this user"
            )
        return audit_entries

@app.post("/audit/users/{user_id}/restore/{version}")
async def restore_user_version(
    user_id: int,
    version: int,
    current_user: dict = Depends(get_current_user)
):
    with get_db_cursor() as cursor:
        # Get specified version
        cursor.execute(
            """
            SELECT name, email
            FROM user_audit
            WHERE user_id = %s AND version = %s
            """,
            (user_id, version)
        )
        old_version = cursor.fetchone()
        if not old_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Specified version not found"
            )
        
        # Get latest version
        cursor.execute(
            "SELECT version FROM user_audit WHERE user_id = %s ORDER BY version DESC LIMIT 1",
            (user_id,)
        )
        result = cursor.fetchone()
        next_version = result["version"] + 1
        
        # Update user
        cursor.execute(
            """
            UPDATE users
            SET name = %s, email = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
            """,
            (old_version["name"], old_version["email"], user_id)
        )
        
        if cursor.rowcount == 0:
            # User was deleted, re-create it
            cursor.execute(
                """
                INSERT INTO users (id, name, email, password_hash)
                VALUES (%s, %s, %s, 'RESTORED')
                """,
                (user_id, old_version["name"], old_version["email"])
            )
        
        # Create audit entry
        cursor.execute(
            """
            INSERT INTO user_audit (user_id, version, name, email, action, changed_by)
            VALUES (%s, %s, %s, %s, 'RESTORE', %s)
            """,
            (user_id, next_version, old_version["name"], old_version["email"], current_user.get("sub"))
        )
        
        return {"message": f"User restored to version {version}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
