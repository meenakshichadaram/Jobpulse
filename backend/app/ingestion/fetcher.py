import httpx
import time
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type, before_sleep_log
import logging
from app.config import settings
from app.utils.logger import logger

class IngestionException(Exception):
    """Base exception for ingestion issues."""
    pass

class SourceUnavailableException(IngestionException):
    """Raised when HTTP request to source fails completely."""
    pass

class MalformedResponseException(IngestionException):
    """Raised when source returns non-JSON or invalid payload structure."""
    pass

class DataFetcher:
    """HTTP client responsible for fetching data with rate limiting, timeouts, and exponential backoff retries."""

    def __init__(self, timeout: int = settings.REQUEST_TIMEOUT_SECONDS, max_retries: int = settings.MAX_RETRIES):
        self.timeout = timeout
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": f"{settings.APP_NAME}/1.0 (Public Ingestion Engine Demo; Respectful Pacing)",
            "Accept": "application/json"
        }

    def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch URL with exponential backoff retries on network/HTTP errors."""

        @retry(
            stop=stop_after_attempt(self.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True
        )
        def _execute_request() -> Dict[str, Any]:
            logger.info(f"Ingestion Request -> GET {url}")
            start_time = time.time()
            
            with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
                response = client.get(url, headers=self.headers)
                latency = round(time.time() - start_time, 3)

                if response.status_code != 200:
                    logger.error(f"Source HTTP Error {response.status_code} from {url} (latency: {latency}s)")
                    response.raise_for_status()

                try:
                    payload = response.json()
                    logger.info(f"Successfully fetched raw payload from {url} (size: {len(response.content)} bytes, latency: {latency}s)")
                    return payload
                except Exception as e:
                    logger.error(f"Malformed JSON response from {url}: {str(e)}")
                    raise MalformedResponseException(f"Failed to parse JSON response from {url}: {str(e)}")

        try:
            return _execute_request()
        except httpx.HTTPError as e:
            logger.error(f"Max retries exceeded for GET {url}: {str(e)}")
            raise SourceUnavailableException(f"Source unreachable after {self.max_retries} attempts: {str(e)}")
