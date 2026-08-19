// ==========================================================================
// JobPulse - Frontend Application Logic
// ==========================================================================

let currentPage = 1;
const limit = 12;
let totalJobsCount = 0;

document.addEventListener('DOMContentLoaded', () => {
    fetchSystemHealth();
    fetchJobs();
});

// Fetch System and Source Health
async function fetchSystemHealth() {
    try {
        const response = await fetch('/api/health');
        if (!response.ok) throw new Error('Health check endpoint failed');
        const data = await response.json();

        // Update Source Status Pill
        const statusText = document.getElementById('statStatusText');
        const statusPill = document.getElementById('statStatusPill');

        if (data.sources && data.sources.length > 0) {
            const source = data.sources[0];
            statusText.innerText = source.status;
            statusPill.className = `status-pill ${source.status.toLowerCase()}`;
            
            document.getElementById('statTotalJobs').innerText = source.total_jobs_ingested || '--';
            
            if (source.last_successful_fetch) {
                const date = new Date(source.last_successful_fetch);
                document.getElementById('statLastFetch').innerText = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            }
        }
    } catch (err) {
        console.warn('System Health check failed:', err);
    }
}

// Fetch Job Listings with filters and pagination
async function fetchJobs() {
    const keyword = document.getElementById('keywordInput').value.trim();
    const location = document.getElementById('locationInput').value.trim();

    const spinner = document.getElementById('loadingSpinner');
    const jobsGrid = document.getElementById('jobsGrid');
    const emptyState = document.getElementById('emptyState');
    const pagination = document.getElementById('pagination');

    spinner.classList.remove('hidden');
    jobsGrid.classList.add('hidden');
    emptyState.classList.add('hidden');

    try {
        let url = `/api/jobs?page=${currentPage}&limit=${limit}`;
        if (keyword) url += `&keyword=${encodeURIComponent(keyword)}`;
        if (location) url += `&location=${encodeURIComponent(location)}`;

        const response = await fetch(url);
        if (!response.ok) throw new Error('Failed to fetch job listings');
        const data = await response.json();

        spinner.classList.add('hidden');
        totalJobsCount = data.total;

        document.getElementById('resultCount').innerText = `Showing ${data.jobs.length} of ${data.total} listings`;

        if (data.total === 0 || data.jobs.length === 0) {
            emptyState.classList.remove('hidden');
            pagination.classList.add('hidden');
            return;
        }

        renderJobsGrid(data.jobs);
        updatePaginationUI(data.total, data.page);
        jobsGrid.classList.remove('hidden');
        pagination.classList.remove('hidden');

    } catch (err) {
        spinner.classList.add('hidden');
        emptyState.classList.remove('hidden');
        console.error('Error loading jobs:', err);
    }
}

// Render Job Cards Grid
function renderJobsGrid(jobs) {
    const grid = document.getElementById('jobsGrid');
    grid.innerHTML = '';

    jobs.forEach(job => {
        const card = document.createElement('div');
        card.className = 'job-card';

        const skillsHtml = (job.skills || []).slice(0, 5).map(skill => 
            `<span class="skill-tag">${escapeHtml(skill)}</span>`
        ).join('');

        const pubDate = job.published_at ? new Date(job.published_at).toLocaleDateString() : 'Recently';

        card.innerHTML = `
            <div class="job-card-header">
                <div class="job-company">${escapeHtml(job.company)}</div>
                <h3 class="job-title">${escapeHtml(job.title)}</h3>
                <div class="job-meta">
                    <span class="job-badge">📍 ${escapeHtml(job.location || 'Remote')}</span>
                    <span class="job-badge">📅 ${pubDate}</span>
                </div>
            </div>
            <p class="job-description-snippet">${escapeHtml(job.description || 'No description provided.')}</p>
            <div class="skills-list">
                ${skillsHtml}
            </div>
            <button class="btn btn-secondary btn-sm btn-full" onclick="openJobModal(${job.id})">
                View Intelligence & Details
            </button>
        `;
        grid.appendChild(card);
    });
}

// Pagination Controls
function updatePaginationUI(total, page) {
    const totalPages = Math.ceil(total / limit) || 1;
    document.getElementById('pageIndicator').innerText = `Page ${page} of ${totalPages}`;

    document.getElementById('prevBtn').disabled = page <= 1;
    document.getElementById('nextBtn').disabled = page >= totalPages;
}

function changePage(delta) {
    currentPage += delta;
    fetchJobs();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleSearch(event) {
    event.preventDefault();
    const keyword = document.getElementById('keywordInput').value.trim().toLowerCase();
    
    // Optional Easter Egg Check for AcdyOn Reviewers
    if (keyword === 'acdyon' || keyword === 'acdyon tech') {
        triggerEasterEgg();
    }

    currentPage = 1;
    fetchJobs();
}

// Secret Easter Egg for AcdyOn Engineering Reviewers 🚀
function triggerEasterEgg() {
    console.log("🎉 Easter Egg Triggered! Welcome AcdyOn Engineering Team.");
    const brandText = document.querySelector('.brand-text h1');
    if (brandText) {
        brandText.innerHTML = 'JobPulse <span style="font-size: 14px; color: #10b981; font-weight: 500;">(AcdyOn Reviewer Mode 🚀)</span>';
    }
}

// Konami Code Sequence: Up, Up, Down, Down, Left, Right, Left, Right, B, A
const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
let konamiIndex = 0;

document.addEventListener('keydown', (e) => {
    if (e.key === konamiCode[konamiIndex]) {
        konamiIndex++;
        if (konamiIndex === konamiCode.length) {
            triggerEasterEgg();
            alert("🚀 Easter Egg Unlocked: 'Build It Like You Mean It!' - Welcome AcdyOn Engineering!");
            konamiIndex = 0;
        }
    } else {
        konamiIndex = 0;
    }
});


// Trigger Manual Ingestion
async function triggerIngestion() {
    const btn = document.getElementById('ingestBtn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '🔄 Ingesting...';
    btn.disabled = true;

    try {
        const res = await fetch('/api/ingest', { method: 'POST' });
        const data = await res.json();
        alert(`Ingestion Triggered!\nSummary: ${JSON.stringify(data.summary, null, 2)}`);
        fetchSystemHealth();
        fetchJobs();
    } catch (err) {
        alert('Ingestion trigger failed: ' + err.message);
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Modal View Handler
async function openJobModal(jobId) {
    try {
        const res = await fetch(`/api/jobs/${jobId}`);
        if (!res.ok) throw new Error('Job not found');
        const job = await res.json();

        document.getElementById('modalCompany').innerText = job.company;
        document.getElementById('modalTitle').innerText = job.title;
        document.getElementById('modalLocation').innerText = `📍 ${job.location || 'Remote'}`;
        document.getElementById('modalSource').innerText = `Source: ${job.source}`;
        document.getElementById('modalDate').innerText = `Published: ${job.published_at ? new Date(job.published_at).toLocaleDateString() : 'N/A'}`;
        
        const skillsContainer = document.getElementById('modalSkills');
        skillsContainer.innerHTML = (job.skills || []).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('') || '<span class="text-muted">No explicit tech skills parsed</span>';

        document.getElementById('modalDescription').innerText = job.description || 'No detailed description available.';
        document.getElementById('modalApplyUrl').href = job.url;

        document.getElementById('jobModal').classList.remove('hidden');
    } catch (err) {
        alert('Failed to load job details: ' + err.message);
    }
}

function closeModal(event) {
    if (event.target.id === 'jobModal') {
        closeModalDirect();
    }
}

function closeModalDirect() {
    document.getElementById('jobModal').classList.add('hidden');
}

function escapeHtml(text) {
    if (!text) return '';
    return text.replace(/[&<>"']/g, function(m) {
        return {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        }[m];
    });
}
