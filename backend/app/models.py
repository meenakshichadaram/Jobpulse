from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from app.database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, index=True, nullable=True)
    title = Column(String, index=True, nullable=False)
    company = Column(String, index=True, nullable=False)
    location = Column(String, default="Remote", nullable=True)
    description = Column(Text, nullable=True)
    url = Column(String, nullable=False)
    source = Column(String, nullable=False, default="remotive")
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=utc_now)
    skills = Column(JSON, default=list)
    dedup_hash = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class SourceHealth(Base):
    __tablename__ = "source_health"

    id = Column(Integer, primary_key=True, index=True)
    source_name = Column(String, unique=True, index=True, nullable=False)
    status = Column(String, nullable=False, default="UNKNOWN")  # HEALTHY, DEGRADED, FAILED, UNKNOWN
    last_successful_fetch = Column(DateTime, nullable=True)
    last_attempted_fetch = Column(DateTime, nullable=True)
    consecutive_failures = Column(Integer, default=0)
    last_error_message = Column(Text, nullable=True)
    total_jobs_ingested = Column(Integer, default=0)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
