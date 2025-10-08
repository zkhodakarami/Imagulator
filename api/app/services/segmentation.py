from dataclasses import dataclass
from typing import Dict, Any, Tuple
import base64

@dataclass
class SegmentationResult:
    width: int
    height: int
    mask_b64: str  # base64-encoded 1x1 mask PNG


def segment_image(image_b64: str) -> SegmentationResult:
    """
    Mock segmentation: accepts base64 PNG input and returns a 1x1 white PNG as mask.
    Replace with actual segmentation (e.g., SynthSeg) later.
    """
    # tiny 1x1 white PNG
    tiny_white_png_b64 = (
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAA"
        "AAC0lEQVR42mP8z8AARgAF/QJ4k9cVAAAAAElFTkSuQmCC"
    )
    return SegmentationResult(width=1, height=1, mask_b64=tiny_white_png_b64)
