# LedgerCLI & Web Portal 

A complete, production-ready solution featuring:
1. **LedgerCLI Engine (`cli/`)**: A rich-terminal, SQLite-backed CLI expense tracker with natural language quick-add, budget thresholds, categorization, and reporting.
2. **Backend API (`backend/`)**: FastAPI server connected to Supabase/PostgreSQL with Row Level Security (RLS) enforcement, validation schemas, and REST endpoints for waitlist, contact submissions, and site analytics telemetry.
3. **Frontend Web Portal (`frontend/`)**: Modern responsive web application featuring:
4. **Supabase Migration (`supabase/schema.sql`)**: PostgreSQL DDL + RLS security policies on all tables.

---

## Quickstart

### 1. Database Setup (Local run on SQlite)
Execute `supabase/schema.sql` in your Supabase SQL editor or PostgreSQL terminal. It establishes `waitlist`, `contacts`, and `site_analytics` tables with strict RLS policies (insert allowed, public read denied).

### 2. Backend (FastAPI)
```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend
Serve the `frontend/` directory with any static server or Nginx:
```bash
cd frontend
python3 -m http.server 3000
```
Open `http://localhost:3000`.

### 4. CLI Tool
```bash
cd cli
pip install -r requirements.txt
python tracker.py quick "450 for lunch via upi"
python tracker.py list
python tracker.py budget set --category Lunch --limit 3000
```
