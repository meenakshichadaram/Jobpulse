import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from email.utils import parsedate_to_datetime
from app.schemas import JobCreate
from app.services.deduplication import compute_dedup_hash
from app.services.skills import skill_extractor
from app.utils.logger import logger

def clean_html(raw_html: Optional[str]) -> str:
    """Removes HTML tags and cleans up excessive white spaces from raw string."""
    if not raw_html:
        return ""
    # Strip HTML tags
    clean_text = re.sub(r'<[^>]+>', ' ', raw_html)
    # Normalize whitespaces
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    return clean_text

def parse_published_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parses various date string formats into a UTC datetime object."""
    if not date_str:
        return None
    try:
        # Try ISO 8601 standard first
        if "T" in str(date_str):
            dt = datetime.fromisoformat(str(date_str).replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc)
        # Try RFC 2822 format (common in RSS/APIs)
        dt = parsedate_to_datetime(str(date_str))
        return dt.astimezone(timezone.utc)
    except Exception:
        # Fallback to current UTC time if parsing fails
        logger.warning(f"Could not parse date string '{date_str}'; setting None.")
        return None

class JobParser:
    """Parses, validates, and normalizes raw job items from source payloads."""

    def parse_job_item(self, item: Dict[str, Any], source_name: str) -> Optional[JobCreate]:
        """Validates and parses a single raw job dict into a normalized JobCreate schema."""
        title = item.get("title")
        company = item.get("company_name") or item.get("company")
        url = item.get("url")

        # Strict Validation Guardrails
        if not title or not isinstance(title, str) or not title.strip():
            logger.warning(f"Validation Failure: Missing or invalid title in item: {item.get('id')}")
            return None

        if not company or not isinstance(company, str) or not company.strip():
            logger.warning(f"Validation Failure: Missing or invalid company for job '{title}'")
            return None

        if not url or not isinstance(url, str) or not url.startswith("http"):
            logger.warning(f"Validation Failure: Missing or invalid URL for job '{title}'")
            return None

        # Field Extraction & Normalization
        external_id = str(item.get("id")) if item.get("id") else None
        location = item.get("candidate_required_location") or item.get("location") or "Remote"
        raw_description = item.get("description") or ""
        clean_description = clean_html(raw_description)
        
        published_at = parse_published_date(item.get("publication_date") or item.get("published_at"))

        # Skill Extraction
        skills = skill_extractor.extract_skills(clean_description)

        # Deduplication Hash Computation
        dedup_hash = compute_dedup_hash(
            source=source_name,
            company=company,
            title=title,
            url=url,
            external_id=external_id
        )

        return JobCreate(
            external_id=external_id,
            title=title.strip(),
            company=company.strip(),
            location=location.strip(),
            description=clean_description,
            url=url.strip(),
            source=source_name,
            published_at=published_at,
            skills=skills,
            dedup_hash=dedup_hash
        )

job_parser = JobParser()
