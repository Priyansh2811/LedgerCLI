import os
import sqlite3
from pathlib import Path
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="LedgerCLI API",
    description="Backend API for LedgerCLI Portal - Waitlist, Inquiries, and Telemetry",
    version="1.0.0"
)

# Enable CORS for local web server
origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Local SQLite fallback database path
LOCAL_DB = Path(__file__).parent.parent / "web_portal.db"

def init_local_db():
    conn = sqlite3.connect(LOCAL_DB)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS waitlist (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS site_analytics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        page_path TEXT NOT NULL,
        referrer TEXT,
        user_agent TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_local_db()

# Check if real Supabase credentials exist
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
USE_SUPABASE = bool(SUPABASE_URL and "your-project" not in SUPABASE_URL and SUPABASE_KEY != "your-anon-key")

supabase_client = None
if USE_SUPABASE:
    try:
        from supabase import create_client
        supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase_client = None

# Request Schemas
class WaitlistRequest(BaseModel):
    email: EmailStr
    role: str = "developer"

class ContactRequest(BaseModel):
    name: str
    email: EmailStr
    message: str

class AnalyticsRequest(BaseModel):
    page_path: str
    referrer: str | None = None
    user_agent: str | None = None

@app.get("/health")
def health():
    return {"status": "healthy", "service": "LedgerCLI Gateway", "storage": "supabase" if supabase_client else "sqlite"}

@app.post("/api/waitlist", status_code=status.HTTP_201_CREATED)
def register_waitlist(req: WaitlistRequest):
    if supabase_client:
        try:
            supabase_client.table("waitlist").insert({"email": req.email, "role": req.role}).execute()
            return {"success": True, "message": "Enrolled in waitlist via Supabase"}
        except Exception as e:
            if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                raise HTTPException(status_code=400, detail="This email is already registered on the waitlist.")
            # Fall back to local sqlite if network error occurs

    # Local SQLite Storage
    try:
        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()
        cur.execute("INSERT INTO waitlist (email, role) VALUES (?, ?)", (req.email, req.role))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Enrolled in waitlist (Saved Locally)"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="This email is already registered on the waitlist.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record waitlist entry: {str(e)}")

@app.post("/api/contact", status_code=status.HTTP_201_CREATED)
def submit_contact(req: ContactRequest):
    if supabase_client:
        try:
            supabase_client.table("contacts").insert({"name": req.name, "email": req.email, "message": req.message}).execute()
            return {"success": True, "message": "Message sent via Supabase."}
        except Exception:
            pass

    # Local SQLite Storage
    conn = sqlite3.connect(LOCAL_DB)
    cur = conn.cursor()
    cur.execute("INSERT INTO contacts (name, email, message) VALUES (?, ?, ?)", (req.name, req.email, req.message))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Message logged successfully."}

@app.post("/api/analytics", status_code=status.HTTP_201_CREATED)
def log_analytics(req: AnalyticsRequest):
    try:
        conn = sqlite3.connect(LOCAL_DB)
        cur = conn.cursor()
        cur.execute("INSERT INTO site_analytics (page_path, referrer, user_agent) VALUES (?, ?, ?)", 
                    (req.page_path, req.referrer, req.user_agent))
        conn.commit()
        conn.close()
    except Exception:
        pass
    return {"success": True}