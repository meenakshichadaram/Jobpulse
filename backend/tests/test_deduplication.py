import pytest
from app.services.deduplication import compute_dedup_hash

def test_deduplication_hash_consistency():
    hash1 = compute_dedup_hash("remotive", "AcdyOn", "AI Engineer", "https://example.com/job1", "ext-100")
    hash2 = compute_dedup_hash("remotive", "acdyon ", " ai engineer ", "https://example.com/job1", "ext-100")
    
    # Hash must be identical regardless of case or whitespace padding
    assert hash1 == hash2

def test_deduplication_hash_detects_differences():
    hash1 = compute_dedup_hash("remotive", "AcdyOn", "AI Engineer", "https://example.com/job1")
    hash2 = compute_dedup_hash("remotive", "AcdyOn", "Frontend Engineer", "https://example.com/job2")
    
    assert hash1 != hash2
