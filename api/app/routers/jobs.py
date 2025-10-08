from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import base64
import urllib.request

from ..services.flywheel_client import get_client
from ..services.segmentation import segment_image

router = APIRouter()


class ProcessReq(BaseModel):
    file_id: Optional[str] = Field(None, description="Flywheel file id to fetch")
    image_url: Optional[str] = Field(None, description="Direct image URL (png/jpg)")


@router.post("/process")
def process(req: ProcessReq) -> Dict[str, Any]:
    """
    Orchestrates: fetch image (via Flywheel or URL) -> run segmentation -> return results.
    This is a minimal demonstrator without external SDK dependencies.
    """
    image_b64: Optional[str] = None

    if req.file_id:
        client = get_client()
        try:
            f = client.get_file(req.file_id)
            image_b64 = f.data_b64
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif req.image_url:
        try:
            with urllib.request.urlopen(req.image_url, timeout=10) as resp:
                data = resp.read()
                image_b64 = base64.b64encode(data).decode("utf-8")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to fetch image_url: {e}")
    else:
        raise HTTPException(status_code=422, detail="Provide either file_id or image_url")

    if not image_b64:
        raise HTTPException(status_code=500, detail="Failed to obtain image data")

    seg = segment_image(image_b64)
    return {
        "input": {"source": "flywheel" if req.file_id else "url", "file_id": req.file_id, "image_url": req.image_url},
        "result": {"width": seg.width, "height": seg.height, "mask_b64": seg.mask_b64},
    }
