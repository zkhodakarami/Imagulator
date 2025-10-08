# api/app/services/flywheel_client.py
from pathlib import Path
from typing import Optional, List
import re
import flywheel

SAFE = re.compile(r"[^a-zA-Z0-9._-]+")


def _slug(v: Optional[str], fallback: str) -> str:
    if not v:
        return fallback
    return SAFE.sub("-", v.strip()).strip("-").lower() or fallback


class FlywheelClient:
    """Simplified client for getting specific acquisitions and downloading files."""

    def __init__(self, api_key: str, cache_dir: str = "cache"):
        if not api_key:
            raise RuntimeError("FW_API_KEY is required")
        if ":" not in api_key:
            raise RuntimeError("FW_API_KEY must be 'host:token' (e.g., upenn.flywheel.io:abcd...).")

        try:
            self.fw = flywheel.Client(api_key)
            # Test the connection
            self.current_user = self.fw.get_current_user()
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Flywheel: {e}")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def search_by_session(self, session_id: str) -> dict:
        """Get all acquisitions for a session with their files."""
        try:
            session = self.fw.get(session_id)
        except Exception as e:
            raise RuntimeError(f"Cannot get session {session_id}: {e}")

        try:
            acquisitions = session.acquisitions() or []
            if not isinstance(acquisitions, list):
                acquisitions = list(acquisitions)
        except Exception as e:
            raise RuntimeError(f"Cannot list acquisitions: {e}")

        acq_list = []
        for acq in acquisitions:
            files = []
            for f in (getattr(acq, "files", []) or []):
                measurement = (getattr(f, "classification", {}) or {}).get("Measurement", [])
                files.append({
                    "name": getattr(f, "name", ""),
                    "type": getattr(f, "type", ""),
                    "size": getattr(f, "size", 0),
                    "measurement": measurement,
                })

            acq_list.append({
                "id": getattr(acq, "id", getattr(acq, "_id", None)),
                "label": getattr(acq, "label", None),
                "files": files
            })

        return {
            "session_id": session_id,
            "session_label": getattr(session, "label", None),
            "acquisitions": acq_list
        }

    def get_acquisition(self, acquisition_id: str) -> dict:
        """Get acquisition details and file list."""
        try:
            acq = self.fw.get(acquisition_id)
        except Exception as e:
            raise RuntimeError(f"Cannot get acquisition {acquisition_id}: {e}")

        files = []
        for f in (getattr(acq, "files", []) or []):
            measurement = (getattr(f, "classification", {}) or {}).get("Measurement", [])
            files.append({
                "name": getattr(f, "name", ""),
                "type": getattr(f, "type", ""),
                "size": getattr(f, "size", 0),
                "measurement": measurement,
            })

        return {
            "id": getattr(acq, "id", getattr(acq, "_id", None)),
            "label": getattr(acq, "label", None),
            "files": files
        }

    def download_files(self, acquisition_id: str, filenames: List[str]) -> dict:
        """Download specific files from an acquisition to cache."""
        try:
            acq = self.fw.get(acquisition_id)
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "access" in error_msg.lower():
                raise RuntimeError(
                    f"Access denied to acquisition {acquisition_id}. "
                    "Your API key may have read-only access. "
                    "Try using a session ID instead, or request write permissions from your Flywheel admin."
                )
            raise RuntimeError(f"Cannot get acquisition {acquisition_id}: {e}")

        # Get parent hierarchy for organized storage
        try:
            session = self.fw.get(acq.parents.session)
            subject = self.fw.get(acq.parents.subject)

            sub_label = _slug(getattr(subject, "label", None), "sub")
            ses_label = _slug(getattr(session, "label", None), "ses")
            acq_label = _slug(getattr(acq, "label", None), getattr(acq, "id", "acq"))
        except Exception:
            # Fallback if hierarchy not available
            sub_label = "unknown"
            ses_label = "unknown"
            acq_label = _slug(getattr(acq, "label", None), getattr(acq, "id", "acq"))

        # Create directory structure
        download_dir = self.cache_dir / f"sub-{sub_label}" / f"ses-{ses_label}" / f"acq-{acq_label}"
        download_dir.mkdir(parents=True, exist_ok=True)

        downloaded = []
        errors = []

        for filename in filenames:
            # Find the file in acquisition
            file_obj = None
            for f in (getattr(acq, "files", []) or []):
                if getattr(f, "name", "") == filename:
                    file_obj = f
                    break

            if not file_obj:
                errors.append(f"{filename}: not found in acquisition")
                continue

            # Download the file
            output_path = download_dir / filename
            try:
                file_obj.download(str(output_path))
                downloaded.append(str(output_path.relative_to(self.cache_dir)))
            except Exception as e:
                error_msg = str(e)
                if "403" in error_msg or "permission" in error_msg.lower():
                    errors.append(f"{filename}: Access denied - read-only API key")
                else:
                    errors.append(f"{filename}: {error_msg}")

        if not downloaded and errors:
            raise RuntimeError(
                "All downloads failed. Your API key may have read-only access. "
                "Contact your Flywheel admin to request download permissions."
            )

        return {
            "acquisition_id": acquisition_id,
            "cache_path": str(download_dir.relative_to(self.cache_dir)),
            "downloaded": downloaded,
            "errors": errors
        }