import hashlib
from typing import Optional

def compute_dedup_hash(source: str, company: str, title: str, url: str, external_id: Optional[str] = None) -> str:
    """
    Computes a deterministic SHA-256 fingerprint for deduplication.
    Uses external_id if present; falls back to normalized combination of source + company + title + url.
    """
    if external_id and str(external_id).strip():
        raw_key = f"{source.strip().lower()}:{str(external_id).strip()}"
    else:
        norm_company = (company or "").strip().lower()
        norm_title = (title or "").strip().lower()
        norm_url = (url or "").strip().lower()
        raw_key = f"{source.strip().lower()}:{norm_company}:{norm_title}:{norm_url}"
    
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
