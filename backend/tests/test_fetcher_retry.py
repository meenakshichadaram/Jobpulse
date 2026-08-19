import pytest
import httpx
from unittest.mock import patch, MagicMock
from app.ingestion.fetcher import DataFetcher, SourceUnavailableException

def test_fetcher_success():
    fetcher = DataFetcher(max_retries=1)
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"jobs": []}
    mock_response.content = b'{"jobs": []}'

    with patch.object(httpx.Client, 'get', return_value=mock_response):
        res = fetcher.fetch_url("https://mock-url.com")
        assert "jobs" in res

def test_fetcher_retries_and_raises_source_unavailable():
    fetcher = DataFetcher(max_retries=2)
    
    with patch.object(httpx.Client, 'get', side_effect=httpx.ConnectError("Connection refused")):
        with pytest.raises(SourceUnavailableException):
            fetcher.fetch_url("https://mock-failing-url.com")
