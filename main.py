from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# Create FastAPI app
app = FastAPI()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Mount static files (for serving images later)
app.mount("/static", StaticFiles(directory="static"), name="static")


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



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)