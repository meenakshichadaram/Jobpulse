from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import SourceHealth
from app.utils.logger import logger

def get_or_create_source_health(db: Session, source_name: str) -> SourceHealth:
    """Retrieve existing source health record or create a default initial row."""
    record = db.query(SourceHealth).filter(SourceHealth.source_name == source_name).first()
    if not record:
        record = SourceHealth(
            source_name=source_name,
            status="UNKNOWN",
            consecutive_failures=0,
            total_jobs_ingested=0
        )
        db.add(record)
        db.commit()
        db.refresh(record)
    return record

def record_health_success(db: Session, source_name: str, ingested_count: int) -> SourceHealth:
    """Record a successful ingestion run, reset failures, and update status to HEALTHY."""
    record = get_or_create_source_health(db, source_name)
    now = datetime.now(timezone.utc)
    
    record.status = "HEALTHY"
    record.last_successful_fetch = now
    record.last_attempted_fetch = now
    record.consecutive_failures = 0
    record.last_error_message = None
    record.total_jobs_ingested += ingested_count
    
    db.commit()
    db.refresh(record)
    logger.info(f"SourceHealth [{source_name}]: STATUS=HEALTHY | Ingested: +{ingested_count} (Total: {record.total_jobs_ingested})")
    return record

def record_health_failure(db: Session, source_name: str, error_message: str) -> SourceHealth:
    """Record an ingestion failure attempt, increment failure count, and mark DEGRADED/FAILED."""
    record = get_or_create_source_health(db, source_name)
    now = datetime.now(timezone.utc)
    
    record.last_attempted_fetch = now
    record.consecutive_failures += 1
    record.last_error_message = error_message
    
    # Degraded after 1-2 failures, FAILED after 3+ consecutive failures
    if record.consecutive_failures >= 3:
        record.status = "FAILED"
    else:
        record.status = "DEGRADED"

    db.commit()
    db.refresh(record)
    logger.error(f"SourceHealth [{source_name}]: STATUS={record.status} | Failure #{record.consecutive_failures} | Error: {error_message}")
    return record
