from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.schemas import JobCreate

class BaseJobSource(ABC):
    """Abstract interface for all job ingestion sources."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Unique identifier for the source."""
        pass

    @abstractmethod
    def fetch_raw_data(self) -> Dict[str, Any]:
        """Fetch raw response payload from source."""
        pass

    @abstractmethod
    def parse(self, raw_data: Dict[str, Any]) -> List[JobCreate]:
        """Parse raw data into normalized JobCreate items."""
        pass
