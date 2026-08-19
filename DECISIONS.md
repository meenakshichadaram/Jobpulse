# Design Decisions & Engineering Trade-offs — JobPulse

---

### 1. Why this ingestion strategy over the obvious alternative you rejected?

I chose a **public API / RSS feed ingestion strategy** (Remotive API) over scraping protected job platforms (like LinkedIn or Indeed) using headless browsers (Playwright/Selenium). 

**Reasoning**:
- Scraping protected platforms forces an engineer into a fragile cat-and-mouse game involving IP proxy rotation, headless fingerprint evasion, and fragile DOM selector maintenance. When a site changes a CSS class or deploys a CAPTCHA, headless scrapers break silently or get IP-blocked.
- For a production ingestion engine, **reliability and data contract stability** trump brittle stealth techniques. Choosing a public API/RSS endpoint allows us to focus engineering effort on pipeline resilience (retries, rate-limiting, deduplication, schema validation, and health tracking) while respecting source policies.

---

### 2. One trade-off you made under the time limit, and what you would do with a real week?

**Trade-off Made**:
Under the time constraint, I used **SQLite** with synchronous SQLAlchemy sessions and in-process execution instead of an asynchronous background task queue (like Celery/Redis or APScheduler).

**What I would do with a real week**:
1. **Asynchronous Worker Queue**: Decouple ingestion into an asynchronous worker pool (Celery/Redis or Temporal) so API requests and ingestion runs never block the web server thread.
2. **Multi-Source Adapter Pool**: Expand the `BaseJobSource` pattern to ingest from 5+ public feeds (WeWorkRemotely RSS, Jobicy API, Remotive) with rate-limiter circuit breakers per source.
3. **Database Migration to PostgreSQL**: Migrate to PostgreSQL with pgvector for semantic search over job descriptions and full-text indexing.

---

### 3. Where did you use AI tools, and what did you personally verify or change afterward?

**Where AI Tools Were Used**:
- **Scaffolding & Boilerplate Generation**: Used AI to scaffold initial Pydantic schemas, SQLAlchemy models, and basic CSS layout styles.
- **Skill Extraction Engineering**: Used AI to brainstorm technical skill categories and generate regex pattern boundary matchers for job descriptions.

**What I Personally Verified & Changed Afterward**:
- **Resilience & Retry Logic**: Verified and refined the `tenacity` retry decorator parameters to guarantee exponential backoff rather than infinite looping.
- **Deterministic Deduplication**: Replaced naive ID matching with a deterministic SHA-256 fingerprint (`source:company:title:url`) to ensure zero duplicate records on repeated API runs.
- **Error Guardrails**: Enforced strict validation checks in `JobParser` to reject empty or malformed job items, ensuring bad upstream data never corrupts the database.
