import pytest
from app.ingestion.parser import job_parser, clean_html, parse_published_date

def test_valid_source_response_parses_correctly():
    raw_item = {
        "id": "12345",
        "title": "Senior AI Backend Engineer",
        "company_name": "AcdyOn Tech",
        "url": "https://example.com/jobs/12345",
        "description": "<p>Looking for <b>Python</b>, <b>FastAPI</b>, and <b>SQL</b> expertise.</p>",
        "candidate_required_location": "Worldwide",
        "publication_date": "2026-08-19T10:00:00Z"
    }

    job = job_parser.parse_job_item(raw_item, "remotive")
    assert job is not None
    assert job.title == "Senior AI Backend Engineer"
    assert job.company == "AcdyOn Tech"
    assert job.location == "Worldwide"
    assert "Python" in job.skills
    assert "FastAPI" in job.skills
    assert "SQL" in job.skills
    assert job.description == "Looking for Python , FastAPI , and SQL expertise."

def test_missing_title_is_handled():
    raw_item = {
        "id": "12345",
        "company_name": "AcdyOn Tech",
        "url": "https://example.com/jobs/12345"
    }
    job = job_parser.parse_job_item(raw_item, "remotive")
    assert job is None  # Must reject missing title

def test_missing_company_is_handled():
    raw_item = {
        "id": "12345",
        "title": "Backend Dev",
        "url": "https://example.com/jobs/12345"
    }
    job = job_parser.parse_job_item(raw_item, "remotive")
    assert job is None  # Must reject missing company

def test_clean_html_strips_tags():
    html_input = "<div><h1>Title</h1><p>Description text</p></div>"
    cleaned = clean_html(html_input)
    assert cleaned == "Title Description text"
