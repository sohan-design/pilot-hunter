from typing import Dict, List, Set

from packages.scanner_sdk.python.base import BaseScanner
from packages.scanner_sdk.python.http import fetch_ok, get_json
from packages.scanner_sdk.python.normalize import build_canonical_job, is_design_job_title, strip_html

# Prefer design category; also search product-designer keywords.
API_URLS = (
    'https://remotive.com/api/remote-jobs?category=design',
    'https://remotive.com/api/remote-jobs?search=product%20designer',
    'https://remotive.com/api/remote-jobs?search=ui%20ux%20designer',
)


class RemotiveScanner(BaseScanner):
    """Remotive public API focused on design / product design roles."""

    @property
    def name(self) -> str:
        return 'Remotive'

    def discover_jobs(self, limit: int = 10) -> List[Dict]:
        jobs: List[Dict] = []
        seen: Set[str] = set()
        for url in API_URLS:
            data = get_json(url)
            if not data:
                continue
            for job in data.get('jobs', []):
                if not isinstance(job, dict):
                    continue
                title = str(job.get('title') or '')
                if not is_design_job_title(title):
                    continue
                job_id = str(job.get('id') or title)
                if job_id in seen:
                    continue
                seen.add(job_id)
                jobs.append(job)
                if len(jobs) >= limit:
                    return jobs
        return jobs

    def normalize(self, raw_job: Dict) -> Dict:
        location = str(raw_job.get('candidate_required_location') or 'Remote')
        salary = str(raw_job.get('salary') or '').strip()
        description = strip_html(str(raw_job.get('description') or ''))
        if salary:
            description = f'Salary: {salary}\n\n{description}'
        return build_canonical_job(
            id=f"remotive-{raw_job.get('id', 'unknown')}",
            title=str(raw_job.get('title') or 'Unknown Role'),
            company=str(raw_job.get('company_name') or 'Unknown Company'),
            location=location,
            remote_type='Remote',
            source=self.name,
            url=str(raw_job.get('url') or ''),
            description=description,
        )

    def health_check(self) -> bool:
        return fetch_ok(API_URLS[0])
