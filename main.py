from fastapi import FastAPI, Request, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
import os
import shutil
from datetime import datetime
from pathlib import Path
# Create FastAPI app
app = FastAPI()

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
    # These variables will be available in the HTML template
    context = {
        "request": request,  # Required by Jinja2
        "app_name": "Image Processing App",
        "version": "1.0",
        "description": "Upload and process your images",
        "features": [
            "Upload images",
            "Process with Python/Bash",
            "View with Papaya viewer"
        ]
    }
    return templates.TemplateResponse("index.html", context)


# ==================== API ENDPOINTS ====================

@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    Upload an image file

    Returns:
        - success: boolean
        - filename: stored filename
        - url: URL to access the file
        - message: status message
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{timestamp}_{file.filename}"
        file_path = UPLOAD_DIR / unique_filename

        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "success": True,
            "filename": unique_filename,
            "url": f"/static/uploads/{unique_filename}",
            "message": "File uploaded successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)