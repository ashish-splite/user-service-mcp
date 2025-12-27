import os
from fastmcp import FastMCP
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, User
from dotenv import load_dotenv
from rapidfuzz import fuzz

load_dotenv()

# 1. Initialize FastMCP
mcp = FastMCP("UserManagement")

# 2. Setup Database
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)
Base.metadata.create_all(bind=engine)

# 3. Expose Tools for AI Agents
@mcp.tool()
def create_user(name: str, email: str, age: int) -> str:
    """Create a new user in the database."""
    session = SessionLocal()
    try:
        new_user = User(name=name, email=email, age=age)
        session.add(new_user)
        session.commit()
        return f"User {name} created successfully with ID {new_user.id}"
    finally:
        session.close()

@mcp.tool()
def get_user_by_email(email: str) -> dict:
    """Retrieve user details using their email address."""
    session = SessionLocal()
    user = session.query(User).filter(User.email == email).first()
    session.close()
    return {"name": user.name, "age": user.age} if user else {"error": "User not found"}

@mcp.tool()
def delete_user(user_id: int) -> str:
    """Delete a user by their ID."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Error: User with ID {user_id} not found"
        session.delete(user)
        session.commit()
        return f"User with ID {user_id} deleted successfully"
    finally:
        session.close()

@mcp.tool()
def update_user(user_id: int, name: str = None, email: str = None, age: int = None) -> str:
    """Update user properties (name, email, and/or age)."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if not user:
            return f"Error: User with ID {user_id} not found"
        
        if name:
            user.name = name
        if email:
            user.email = email
        if age:
            user.age = age
        
        session.commit()
        return f"User with ID {user_id} updated successfully"
    finally:
        session.close()

@mcp.tool()
def list_users_by_name(name: str) -> list:
    """Fetch top 5 users matching the provided name using fuzzy matching (handles spelling mistakes)."""
    session = SessionLocal()
    try:
        all_users = session.query(User).all()
        if not all_users:
            return []
        
        # Calculate similarity score for each user
        scored_users = []
        for user in all_users:
            score = fuzz.ratio(name.lower(), user.name.lower())
            scored_users.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "age": user.age,
                "match_score": score
            })
        
        # Sort by score descending and return top 5
        scored_users.sort(key=lambda x: x["match_score"], reverse=True)
        return scored_users[:5]
    finally:
        session.close()

@mcp.tool()
def list_users_by_age(age: int) -> list:
    """Fetch list of users matching the provided age."""
    session = SessionLocal()
    try:
        users = session.query(User).filter(User.age == age).all()
        if not users:
            return []
        return [{"id": u.id, "name": u.name, "email": u.email, "age": u.age} for u in users]
    finally:
        session.close()

if __name__ == "__main__":
    # Run as SSE (Server-Sent Events) for network access
    mcp.run(transport="sse", host="0.0.0.0", port=8001)