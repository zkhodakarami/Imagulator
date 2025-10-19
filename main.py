from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
import shutil
import sqlite3, time, os
from pathlib import Path
from argon2 import PasswordHasher

# Add this import at the top with other imports
from urllib.parse import quote_plus, unquote_plus

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


# Use the existing Images directory structure
UPLOAD_DIR = BASE / "database" / "Images" / "uploaded"
PROCESSED_DIR = BASE / "database" / "Images" / "processed"
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
        "message": message,
        "current_page": "dashboard"  # Add this to highlight active nav item
    }
    return templates.TemplateResponse("dashboard/dashboard.html", context)


# Add new routes for the different job pages
@app.get("/new-patient")
async def new_patient(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/?error=Please+log+in+first", status_code=303)
    
    # Get and decode messages from URL params
    message = request.query_params.get("message")
    error = request.query_params.get("error")
    
    # Decode URL-encoded messages
    if message:
        message = unquote_plus(message)
    if error:
        error = unquote_plus(error)
    
    context = {
        "request": request,
        "app_name": "Image Processing App",
        "user": user,
        "current_page": "new_patient",
        "message": message,
        "error": error
    }
    return templates.TemplateResponse("dashboard/new_patient.html", context)

@app.post("/new-patient")
async def create_patient(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/?error=Please+log+in+first", status_code=303)

    try:
        # Parse form data manually to handle multiple images
        form_data = await request.form()
        
        # Get patient data
        patient_code = form_data.get("patient_code")
        birthdate = form_data.get("birthdate") 
        sex = form_data.get("sex")
        clinical_diagnosis = form_data.get("clinical_diagnosis", "")
        action = form_data.get("action")
        
        # Validate required fields
        if not all([patient_code, birthdate, sex, action]):
            return RedirectResponse("/new-patient?error=Missing+required+fields", status_code=303)

        with get_conn() as con:
            # Check if patient_code already exists
            existing = con.execute("SELECT id FROM patient WHERE patient_code = ?", (patient_code,)).fetchone()
            if existing:
                return RedirectResponse("/new-patient?error=Patient+code+already+exists", status_code=303)

            # Insert patient record
            timestamp = int(time.time())
            cursor = con.execute("""
                INSERT INTO patient (doctor_username, patient_code, birthdate, sex, clinical_diagnosis,
                                   created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user['username'], patient_code, birthdate, sex, clinical_diagnosis, timestamp, timestamp))

            patient_id = cursor.lastrowid
            images_saved = 0

            # Handle image uploads if action includes images
            if action == "patient_and_images":
                # Find all image fields in form data
                image_index = 0
                while True:
                    # Check if this image index exists in form data
                    mri_date_key = f"mri_date_{image_index}"
                    modality_key = f"modality_{image_index}"
                    image_file_key = f"image_file_{image_index}"
                    image_notes_key = f"image_notes_{image_index}"
                    
                    mri_date = form_data.get(mri_date_key)
                    modality = form_data.get(modality_key)
                    image_file = form_data.get(image_file_key)
                    image_notes = form_data.get(image_notes_key, "")
                    
                    # If no more image fields, break
                    if mri_date is None and modality is None and image_file is None:
                        break
                    
                    # Process image if we have the required fields and a file
                    if image_file and hasattr(image_file, 'filename') and image_file.filename:
                        if mri_date and modality:
                            try:
                                # Generate unique filename
                                file_extension = Path(image_file.filename).suffix
                                unique_filename = f"{patient_code}_{modality}_{image_index}_{int(time.time())}{file_extension}"
                                storage_path = UPLOAD_DIR / unique_filename

                                # Read and save file
                                contents = await image_file.read()
                                
                                # Make sure the directory exists
                                storage_path.parent.mkdir(parents=True, exist_ok=True)
                                
                                with open(storage_path, "wb") as f:
                                    f.write(contents)

                                # Verify file was saved and has content
                                if storage_path.exists() and storage_path.stat().st_size > 0:
                                    print(f"✅ File saved successfully: {storage_path}")
                                    print(f"   Size: {storage_path.stat().st_size} bytes")
                                    
                                    # Insert image record with relative path for portability
                                    relative_path = f"database/Images/uploaded/{unique_filename}"
                                    con.execute("""
                                        INSERT INTO image (patient_id, uploader_username, mri_date, image_name, storage_path, modality, notes, created_at, updated_at)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (patient_id, user['username'], mri_date, unique_filename, relative_path, modality, image_notes, timestamp, timestamp))
                                    
                                    images_saved += 1
                                    print(f"✅ Database record created for image {image_index + 1}")
                                else:
                                    print(f"❌ Failed to save image file: {storage_path}")
                                    
                            except Exception as e:
                                print(f"❌ Error processing image {image_index}: {e}")
                                import traceback
                                traceback.print_exc()
                        
                    image_index += 1

            # Create success message
            message = "Patient saved successfully"
            if action == "patient_and_images":
                if images_saved > 0:
                    message += f" with {images_saved} image{'s' if images_saved != 1 else ''} uploaded"
                else:
                    message += " (no images were uploaded)"

            # Use proper URL encoding
            return RedirectResponse(f"/new-patient?message={quote_plus(message)}", status_code=303)

    except Exception as e:
        print(f"Error creating patient: {e}")
        import traceback
        traceback.print_exc()
        # Use proper URL encoding for error message too
        return RedirectResponse(f"/new-patient?error={quote_plus('Failed to save patient')}", status_code=303)


@app.get("/patients")
async def view_patients(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/?error=Please+log+in+first", status_code=303)
    
    context = {
        "request": request,
        "app_name": "Image Processing App",
        "user": user,
        "current_page": "patients"
    }

    # For now, redirect to new_patient - you can change this later
    return RedirectResponse("/new-patient", status_code=303)
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/?error=Please+log+in+first", status_code=303)
    
    context = {
        "request": request,
        "app_name": "Image Processing App",
        "user": user,
        "current_page": "process_images"
    }
    return templates.TemplateResponse("process_images.html", context)

@app.get("/papaya")
async def papaya_viewer(request: Request):
    user = get_current_user(request)
    if not user:
        return RedirectResponse("/?error=Please+log+in+first", status_code=303)
    
    context = {
        "request": request,
        "app_name": "Image Processing App",
        "user": user,
        "current_page": "papaya_viewer"
    }
    return templates.TemplateResponse("papaya.html", context)

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