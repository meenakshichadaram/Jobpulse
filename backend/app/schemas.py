from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from datetime import datetime

class JobBase(BaseModel):
    title: str
    company: str
    location: Optional[str] = "Remote"
    description: Optional[str] = None
    url: str
    source: str = "remotive"
    published_at: Optional[datetime] = None
    skills: List[str] = Field(default_factory=list)

class JobCreate(JobBase):
    external_id: Optional[str] = None
    dedup_hash: str

class JobResponse(JobBase):
    id: int
    external_id: Optional[str] = None
    fetched_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class JobListResponse(BaseModel):
    total: int
    page: int
    limit: int
    jobs: List[JobResponse]

class SourceHealthResponse(BaseModel):
    source_name: str
    status: str
    last_successful_fetch: Optional[datetime] = None
    last_attempted_fetch: Optional[datetime] = None
    consecutive_failures: int
    last_error_message: Optional[str] = None
    total_jobs_ingested: int

    model_config = ConfigDict(from_attributes=True)

class SystemHealthResponse(BaseModel):
    status: str
    database: str
    sources: List[SourceHealthResponse]

