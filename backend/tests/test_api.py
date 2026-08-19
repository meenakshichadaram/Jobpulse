import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Job, SourceHealth

# Setup isolated in-memory SQLite database with StaticPool so all connections share state
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    # Seed sample test data
    job1 = Job(
        external_id="1",
        title="Python Backend Engineer",
        company="AcdyOn",
        location="Remote",
        description="FastAPI, SQL, Docker",
        url="https://example.com/job1",
        source="remotive",
        skills=["Python", "FastAPI", "SQL", "Docker"],
        dedup_hash="hash1"
    )
    job2 = Job(
        external_id="2",
        title="Frontend Developer",
        company="TechCorp",
        location="New York",
        description="React and JavaScript",
        url="https://example.com/job2",
        source="remotive",
        skills=["React", "JavaScript"],
        dedup_hash="hash2"
    )
    db.add_all([job1, job2])

    health = SourceHealth(
        source_name="remotive",
        status="HEALTHY",
        total_jobs_ingested=2
    )
    db.add(health)
    db.commit()
    db.close()

    yield
    Base.metadata.drop_all(bind=engine)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "HEALTHY"
    assert data["database"] == "HEALTHY"
    assert len(data["sources"]) == 1
    assert data["sources"][0]["source_name"] == "remotive"

def test_jobs_list_endpoint():
    response = client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["jobs"]) == 2

def test_jobs_filtering_by_keyword():
    response = client.get("/api/jobs?keyword=Python")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["jobs"][0]["title"] == "Python Backend Engineer"

def test_job_detail_endpoint():
    response = client.get("/api/jobs/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["company"] == "AcdyOn"

def test_job_not_found():
    response = client.get("/api/jobs/999")
    assert response.status_code == 404
