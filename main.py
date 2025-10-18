from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
import sqlite3, time, os
from pathlib import Path
from argon2 import PasswordHasher

# Fix database path
BASE = Path(__file__).resolve().parent
DB   = BASE / "database" / "identifier.sqlite"
DB.parent.mkdir(parents=True, exist_ok=True)

def get_conn():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON;")
    return con

ph = PasswordHasher()

# Add this helper function after ph = PasswordHasher()
def get_current_user(request: Request):
    """Get current logged-in user from session"""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    with get_conn() as con:
        row = con.execute("SELECT * FROM user WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

app = FastAPI()

# Add session middleware
app.add_middleware(SessionMiddleware, secret_key="change-this-secret-key-in-production")

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount static files (for serving images later)
app.mount("/static", StaticFiles(directory="static"), name="static")


# Create directories
UPLOAD_DIR = Path("static/uploads")
PROCESSED_DIR = Path("static/processed")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

#######webpages
# Homepage route - serves HTML with Jinja
@app.get("/")
async def home(request: Request):
    # Get any messages from URL params (from redirects)
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    
    # These variables will be available in the HTML template
    context = {
        "request": request,  # Required by Jinja2
        "app_name": "Image Processing App",
        "version": "1.0",
        "description": "Upload and process your images",
        "message": message,  # Add message to context
        "error": error,      # Add error to context
        "features": [
            "Upload images",
            "Process with Python/Bash",
            "View with Papaya viewer"
        ]
    }
    return templates.TemplateResponse("index.html", context)

# Add dashboard route after the home route
@app.get("/dashboard")
async def dashboard(request: Request):
    # Check if user is logged in
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/?error=Please+log+in+first", status_code=303)
    
    # Get any messages from URL params
    message = request.query_params.get("message")
    
    context = {
        "request": request,
        "app_name": "Image Processing App",
        "user": user,
        "message": message
    }
    return templates.TemplateResponse("dashboard.html", context)

# Handle sign up
@app.post("/signup")
def signup(request: Request, email: str = Form(...), username: str = Form(...), password: str = Form(...)):
    ts = int(time.time())
    try:
        with get_conn() as con:
            cursor = con.execute("""
                INSERT INTO user (username, email, password, role, created_at, updated_at)
                VALUES (?, ?, ?, 'doctor', ?, ?)
            """, (username, email, ph.hash(password), ts, ts))
            # Auto-login after signup
            request.session["user_id"] = cursor.lastrowid
            request.session["username"] = username
    except sqlite3.IntegrityError:
        return RedirectResponse("/?error=Username+or+email+already+exists", status_code=303)
    
    # Redirect to dashboard after successful signup
    return RedirectResponse("/dashboard?message=Account+created+successfully", status_code=303)

# Handle login (email OR username + password)
@app.post("/login")
def login(request: Request, email: str = Form(""), username: str = Form(""), password: str = Form(...)):
    ident = email or username
    if not ident:
        return RedirectResponse("/?error=Provide+email+or+username", status_code=303)

    with get_conn() as con:
        row = con.execute("""
            SELECT * FROM user
            WHERE email = ? COLLATE NOCASE OR username = ? COLLATE NOCASE
            LIMIT 1
        """, (ident, ident)).fetchone()

    if not row:
        return RedirectResponse("/?error=Invalid+credentials", status_code=303)

    try:
        ph.verify(row["password"], password)
        # Create session on successful login
        request.session["user_id"] = row["id"]
        request.session["username"] = row["username"]
    except Exception:
        return RedirectResponse("/?error=Invalid+credentials", status_code=303)

    # Redirect to dashboard instead of home page
    return RedirectResponse("/dashboard?message=Logged+in+successfully", status_code=303)

# Update logout to redirect to home page
@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/?message=Logged+out+successfully", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)