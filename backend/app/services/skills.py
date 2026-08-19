import re
from typing import List, Optional
from app.config import settings
from app.utils.logger import logger

# Common engineering & technical skills catalog
KNOWN_SKILLS = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI", "Django", "Flask",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "GraphQL", "REST API",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD", "Git", "Linux",
    "Machine Learning", "Deep Learning", "PyTorch", "TensorFlow", "Pandas", "NumPy", "Scikit-Learn",
    "NLP", "LLM", "Generative AI", "LangChain", "Vector DB", "Pinecone", "ChromaDB",
    "System Design", "Microservices", "Java", "C++", "Go", "Rust", "Swift", "Kotlin",
    "Power BI", "Tableau", "Kibana", "Prometheus", "Grafana"
]

class SkillExtractor:
    """Service to extract technical skills from raw job descriptions."""

    def __init__(self):
        self.known_skills = KNOWN_SKILLS

    def extract_skills_deterministic(self, description: str) -> List[str]:
        """Extract skills using deterministic word boundary regex matching."""
        if not description:
            return []

        extracted = set()
        desc_lower = description.lower()

        for skill in self.known_skills:
            # Handle special skill cases like C++ or .NET
            escaped_skill = re.escape(skill)
            pattern = r'\b' + escaped_skill + r'\b'
            if re.search(pattern, description, re.IGNORECASE):
                extracted.add(skill)

        return sorted(list(extracted))

    def extract_skills(self, description: str) -> List[str]:
        """
        Primary entry point. Performs deterministic regex matching first.
        If GEMINI_API_KEY is available, LLM extraction could be invoked; otherwise falls back gracefully.
        """
        extracted = self.extract_skills_deterministic(description)
        
        # Log extraction result
        if extracted:
            logger.debug(f"Extracted {len(extracted)} skills: {extracted[:5]}...")
            
        return extracted

skill_extractor = SkillExtractor()
