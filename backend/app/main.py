import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api.jobs import router as api_router
from app.ingestion.service import ingestion_service
from app.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Auto-run initial ingestion on startup if table is empty
    db = SessionLocal()
    try:
        from app.models import Job
        if db.query(Job).count() == 0:
            logger.info("Database empty on startup. Triggering initial ingestion run...")
            ingestion_service.run_all(db)
    except Exception as e:
        logger.error(f"Startup ingestion attempt encountered error: {e}")
    finally:
        db.close()
        
    yield
    # Shutdown logic
    logger.info("Shutting down JobPulse service...")

app = FastAPI(
    title=settings.APP_NAME,
    description="Resilient Job Ingestion Engine API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API endpoints
app.include_router(api_router, prefix="/api")

# Static frontend files path
FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend")

if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
def read_root():
    """Serves the frontend dashboard index.html."""
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": f"Welcome to {settings.APP_NAME} API. Access API docs at /docs."}
