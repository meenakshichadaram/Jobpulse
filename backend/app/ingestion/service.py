from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.ingestion.base import BaseJobSource
from app.ingestion.remotive import RemotiveJobSource
from app.models import Job
from app.services.health import record_health_success, record_health_failure
from app.utils.logger import logger

class IngestionService:
    """Orchestrates ingestion workflow across registered job sources."""

    def __init__(self, sources: List[BaseJobSource] = None):
        self.sources = sources or [RemotiveJobSource()]

    def run_ingestion_for_source(self, source: BaseJobSource, db: Session) -> Dict[str, Any]:
        """Runs end-to-end ingestion pipeline for a single source with full resilience."""
        source_name = source.source_name
        logger.info(f"=== Ingestion Started for Source: [{source_name}] ===")

        try:
            # 1. Fetch raw data
            raw_payload = source.fetch_raw_data()
            
            # 2. Parse & validate items
            parsed_jobs = source.parse(raw_payload)

            if not parsed_jobs:
                logger.warning(f"Ingestion Alert: Source [{source_name}] returned zero valid jobs.")
                # We record a failure or degraded health if source returned empty data unexpectedly
                record_health_failure(db, source_name, "Source returned zero valid jobs.")
                return {"source": source_name, "status": "DEGRADED", "fetched": 0, "inserted": 0, "duplicates_skipped": 0}

            # 3. Deduplication & Database Persistence
            inserted_count = 0
            duplicates_skipped = 0

            for job_schema in parsed_jobs:
                # Deduplication Check
                existing = db.query(Job).filter(Job.dedup_hash == job_schema.dedup_hash).first()
                if existing:
                    duplicates_skipped += 1
                    continue

                # Insert new job
                new_job = Job(
                    external_id=job_schema.external_id,
                    title=job_schema.title,
                    company=job_schema.company,
                    location=job_schema.location,
                    description=job_schema.description,
                    url=job_schema.url,
                    source=job_schema.source,
                    published_at=job_schema.published_at,
                    skills=job_schema.skills,
                    dedup_hash=job_schema.dedup_hash
                )
                db.add(new_job)
                inserted_count += 1

            db.commit()

            # 4. Record Successful Health Metric
            record_health_success(db, source_name, inserted_count)

            summary = {
                "source": source_name,
                "status": "SUCCESS",
                "fetched": len(parsed_jobs),
                "inserted": inserted_count,
                "duplicates_skipped": duplicates_skipped
            }
            logger.info(f"=== Ingestion Finished for [{source_name}]: Inserted {inserted_count}, Skipped {duplicates_skipped} duplicates ===")
            return summary

        except Exception as e:
            db.rollback()
            error_msg = str(e)
            logger.error(f"=== Ingestion Failed for [{source_name}]: {error_msg} ===")
            record_health_failure(db, source_name, error_msg)
            return {
                "source": source_name,
                "status": "FAILED",
                "error": error_msg,
                "fetched": 0,
                "inserted": 0,
                "duplicates_skipped": 0
            }

    def run_all(self, db: Session) -> List[Dict[str, Any]]:
        """Runs ingestion across all configured sources."""
        results = []
        for source in self.sources:
            res = self.run_ingestion_for_source(source, db)
            results.append(res)
        return results

ingestion_service = IngestionService()
