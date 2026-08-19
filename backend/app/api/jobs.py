from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional

from app.database import get_db
from app.models import Job, SourceHealth
from app.schemas import JobResponse, JobListResponse, SystemHealthResponse, SourceHealthResponse
from app.ingestion.service import ingestion_service

router = APIRouter()

@router.get("/health", response_model=SystemHealthResponse)
def get_system_health(db: Session = Depends(get_db)):
    """Health check endpoint exposing database status and real source operational health."""
    db_status = "HEALTHY"
    try:
        db.query(Job).first()
    except Exception:
        db_status = "UNHEALTHY"

    sources_health = db.query(SourceHealth).all()
    overall_status = "HEALTHY" if db_status == "HEALTHY" else "UNHEALTHY"
    
    if any(s.status == "FAILED" for s in sources_health):
        overall_status = "DEGRADED"

    return SystemHealthResponse(
        status=overall_status,
        database=db_status,
        sources=[SourceHealthResponse.model_validate(s) for s in sources_health]
    )

@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    keyword: Optional[str] = Query(None, description="Search term for title, company, or skills"),
    location: Optional[str] = Query(None, description="Filter by location"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    source: Optional[str] = Query(None, description="Filter by job source"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Lists jobs with keyword searching, filtering, and pagination."""
    query = db.query(Job)

    if keyword:
        term = f"%{keyword.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(term),
                Job.company.ilike(term),
                Job.description.ilike(term)
            )
        )

    if location:
        query = query.filter(Job.location.ilike(f"%{location.strip()}%"))

    if company:
        query = query.filter(Job.company.ilike(f"%{company.strip()}%"))

    if source:
        query = query.filter(Job.source == source.strip())

    total = query.count()
    offset = (page - 1) * limit
    jobs = query.order_by(Job.published_at.desc().nullslast(), Job.id.desc()).offset(offset).limit(limit).all()

    return JobListResponse(
        total=total,
        page=page,
        limit=limit,
        jobs=[JobResponse.model_validate(j) for j in jobs]
    )

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job_detail(job_id: int, db: Session = Depends(get_db)):
    """Retrieves single job details by primary ID."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job listing not found.")
    return JobResponse.model_validate(job)

@router.post("/ingest")
def trigger_manual_ingestion(db: Session = Depends(get_db)):
    """Triggers on-demand ingestion run across configured sources."""
    results = ingestion_service.run_all(db)
    return {"message": "Ingestion cycle completed.", "summary": results}
