# api/app/routers/flywheel.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
from ..settings import settings
from ..services.flywheel_client import FlywheelClient

router = APIRouter()

_client_cache = None


def fw() -> FlywheelClient:
    """Get or create Flywheel client."""
    global _client_cache

    if not settings.FW_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Flywheel not configured. Set FW_API_KEY in .env file."
        )

    if _client_cache is not None:
        return _client_cache

    try:
        _client_cache = FlywheelClient(
            api_key=settings.FW_API_KEY,
            cache_dir=settings.CACHE_DIR
        )
        return _client_cache
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect: {type(e).__name__}: {e}"
        )


@router.get("/status")
def flywheel_status():
    """Check connection status."""
    if not settings.FW_API_KEY:
        return {
            "configured": False,
            "connected": False,
            "message": "FW_API_KEY not set"
        }

    try:
        _ = fw()  # This will test the connection
        return {
            "configured": True,
            "connected": True,
            "message": "Connected successfully"
        }
    except HTTPException as e:
        return {
            "configured": True,
            "connected": False,
            "message": e.detail
        }
    except Exception as e:
        return {
            "configured": True,
            "connected": False,
            "message": str(e)
        }


@router.get("/acquisition/{acquisition_id}")
def get_acquisition(acquisition_id: str):
    """Get acquisition details and file list."""
    try:
        return fw().get_acquisition(acquisition_id)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Error: {type(e).__name__}: {e}")


class DownloadRequest(BaseModel):
    acquisition_id: str
    filenames: List[str]


@router.post("/download")
def download_files(request: DownloadRequest):
    """Download specific files from an acquisition."""
    if not request.filenames:
        raise HTTPException(400, detail="No filenames provided")

    try:
        return fw().download_files(request.acquisition_id, request.filenames)
    except HTTPException:
        raise
    except RuntimeError as e:
        raise HTTPException(400, detail=str(e))
    except Exception as e:
        raise HTTPException(500, detail=f"Download failed: {type(e).__name__}: {e}")