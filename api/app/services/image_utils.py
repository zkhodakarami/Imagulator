# api/app/services/image_utils.py
from pathlib import Path
from typing import Optional
import numpy as np
from PIL import Image
import io


def list_cached_sessions(cache_dir: str = "cache"):
    """List all cached sessions with their available modalities."""
    cache_path = Path(cache_dir)
    sessions = []

    if not cache_path.exists():
        return sessions

    for sub_dir in cache_path.glob("sub-*"):
        if not sub_dir.is_dir():
            continue
        subject_id = sub_dir.name

        for ses_dir in sub_dir.glob("ses-*"):
            if not ses_dir.is_dir():
                continue
            session_id = ses_dir.name
            anat_dir = ses_dir / "anat"

            if not anat_dir.exists():
                continue

            files = []
            for nii_file in anat_dir.glob("*.nii*"):
                # Extract modality from filename (e.g., sub-X_ses-Y_T1w.nii.gz -> T1w)
                parts = nii_file.stem.replace('.nii', '').split('_')
                modality = parts[-1] if parts else "unknown"

                files.append({
                    "filename": nii_file.name,
                    "modality": modality,
                    "path": str(nii_file.relative_to(cache_path)),
                    "size": nii_file.stat().st_size
                })

            if files:
                sessions.append({
                    "subject": subject_id,
                    "session": session_id,
                    "files": files
                })

    return sessions


def nifti_to_png(nifti_path: Path, slice_idx: Optional[int] = None,
                 axis: int = 2, window: tuple = (0, 99)) -> bytes:
    """
    Convert a NIfTI file slice to PNG bytes.

    Args:
        nifti_path: Path to .nii or .nii.gz file
        slice_idx: Slice index (if None, uses middle slice)
        axis: Which axis to slice (0=sagittal, 1=coronal, 2=axial)
        window: Percentile window for intensity normalization (min, max)
    """
    try:
        import nibabel as nib
    except ImportError:
        raise ImportError("nibabel is required for NIfTI viewing. Install: pip install nibabel")

    # Load NIfTI
    img = nib.load(str(nifti_path))
    data = img.get_fdata()

    # Select slice
    if slice_idx is None:
        slice_idx = data.shape[axis] // 2

    if axis == 0:
        slice_data = data[slice_idx, :, :]
    elif axis == 1:
        slice_data = data[:, slice_idx, :]
    else:  # axis == 2
        slice_data = data[:, :, slice_idx]

    # Normalize using percentile window
    vmin, vmax = np.percentile(slice_data, window)
    slice_data = np.clip(slice_data, vmin, vmax)
    slice_data = ((slice_data - vmin) / (vmax - vmin) * 255).astype(np.uint8)

    # Rotate for correct orientation (axial view)
    slice_data = np.rot90(slice_data)

    # Convert to PIL Image and save as PNG
    pil_img = Image.fromarray(slice_data, mode='L')

    # Resize if too large
    max_size = 512
    if max(pil_img.size) > max_size:
        pil_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

    # Save to bytes
    buf = io.BytesIO()
    pil_img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()