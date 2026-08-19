from typing import List, Dict, Any
from app.ingestion.base import BaseJobSource
from app.ingestion.fetcher import DataFetcher
from app.ingestion.parser import job_parser
from app.schemas import JobCreate
from app.config import settings
from app.utils.logger import logger

class RemotiveJobSource(BaseJobSource):
    """Source adapter for the public Remotive Remote Jobs API."""

    def __init__(self, fetcher: DataFetcher = None):
        self.fetcher = fetcher or DataFetcher()
        self.url = settings.REMOTE_SOURCE_URL

    @property
    def source_name(self) -> str:
        return "remotive"

    def fetch_raw_data(self) -> Dict[str, Any]:
        """Fetch raw payload from Remotive API."""
        return self.fetcher.fetch_url(self.url)

    def parse(self, raw_data: Dict[str, Any]) -> List[JobCreate]:
        """Parses the 'jobs' array from Remotive JSON response."""
        jobs_list = raw_data.get("jobs", [])
        if not isinstance(jobs_list, list):
            logger.error("Remotive response payload missing expected 'jobs' array.")
            return []

        parsed_jobs: List[JobCreate] = []
        for raw_item in jobs_list:
            job = job_parser.parse_job_item(raw_item, self.source_name)
            if job:
                parsed_jobs.append(job)

        logger.info(f"Remotive Source Parser: Successfully parsed {len(parsed_jobs)} valid jobs out of {len(jobs_list)} items.")
        return parsed_jobs
