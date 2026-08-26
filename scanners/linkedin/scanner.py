"""LinkedIn Jobs guest search (public HTML cards — no OAuth)."""

from __future__ import annotations

import html as html_lib
import re
from typing import Dict, List, Set
from urllib.parse import quote_plus, urlencode

from packages.scanner_sdk.python.base import BaseScanner
from packages.scanner_sdk.python.config import parse_env_list
from packages.scanner_sdk.python.http import get_response
from packages.scanner_sdk.python.normalize import (
    build_canonical_job,
    infer_remote_type,
    is_design_job_title,
    strip_html,
)

GUEST_API = 'https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search'
BROWSER_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US,en;q=0.9',
}

DEFAULT_QUERIES = (
    'Senior Product Designer',
    'Product Designer II',
    'Product Designer',
    'UI UX Designer',
    'UI/UX Designer',
)
DEFAULT_LOCATIONS = (
    'Bengaluru',
    'India',
    'Remote',
)


class LinkedInScanner(BaseScanner):
    """
    Discover LinkedIn job cards via the public guest search endpoint.

    Configure with ``LINKEDIN_JOB_QUERIES`` and ``LINKEDIN_JOB_LOCATIONS``
    (comma-separated). Defaults target Product Designer roles in India / Remote.
    """

    @property
    def name(self) -> str:
        return 'LinkedIn'

    def _queries(self) -> List[str]:
        configured = parse_env_list('LINKEDIN_JOB_QUERIES')
        return configured or list(DEFAULT_QUERIES)

    def _locations(self) -> List[str]:
        configured = parse_env_list('LINKEDIN_JOB_LOCATIONS')
        return configured or list(DEFAULT_LOCATIONS)

    def _search_url(self, query: str, location: str, start: int = 0) -> str:
        params = {
            'keywords': query,
            'location': location,
            'start': str(start),
            'f_TPR': 'r604800',  # past week
        }
        return f'{GUEST_API}?{urlencode(params)}'

    def _parse_cards(self, markup: str) -> List[Dict]:
        cards: List[Dict] = []
        # Guest markup repeats compact card blocks; extract via tolerant regexes.
        blocks = re.split(r'base-card(?:\s|")', markup)
        for block in blocks[1:]:
            title_match = re.search(
                r'base-search-card__title[^>]*>\s*([^<]+)',
                block,
                flags=re.IGNORECASE,
            )
            company_match = re.search(
                r'base-search-card__subtitle[^>]*>\s*(?:<a[^>]*>)?\s*([^<]+)',
                block,
                flags=re.IGNORECASE,
            )
            link_match = re.search(
                r'href="(https://[^"]+/jobs/view/[^"]+)"',
                block,
                flags=re.IGNORECASE,
            )
            location_match = re.search(
                r'job-search-card__location[^>]*>\s*([^<]+)',
                block,
                flags=re.IGNORECASE,
            )
            if not title_match or not link_match:
                continue
            title = html_lib.unescape(title_match.group(1)).strip()
            company = html_lib.unescape(company_match.group(1)).strip() if company_match else 'Unknown Company'
            location = (
                html_lib.unescape(location_match.group(1)).strip() if location_match else 'Remote'
            )
            url = html_lib.unescape(link_match.group(1)).split('?')[0]
            job_id_match = re.search(r'/(\d+)/?$', url)
            job_id = job_id_match.group(1) if job_id_match else quote_plus(title)[:48]
            cards.append(
                {
                    'id': job_id,
                    'title': title,
                    'company': company,
                    'location': location,
                    'url': url,
                }
            )
        return cards

    def discover_jobs(self, limit: int = 10) -> List[Dict]:
        jobs: List[Dict] = []
        seen: Set[str] = set()
        queries = self._queries()
        locations = self._locations()
        per_combo = max(1, limit // max(1, len(queries) * len(locations)))

        for location in locations:
            for query in queries:
                response = get_response(
                    self._search_url(query, location),
                    headers=BROWSER_HEADERS,
                )
                if not response:
                    print(f'[LinkedInScanner] Failed guest search for "{query}" @ {location}')
                    continue
                for card in self._parse_cards(response.text)[:per_combo]:
                    title = str(card.get('title') or '')
                    if not is_design_job_title(title):
                        continue
                    job_id = str(card.get('id') or title)
                    if job_id in seen:
                        continue
                    seen.add(job_id)
                    card['_query'] = query
                    jobs.append(card)
                    if len(jobs) >= limit:
                        return jobs
        return jobs

    def normalize(self, raw_job: Dict) -> Dict:
        location = str(raw_job.get('location') or 'Remote')
        query = str(raw_job.get('_query') or '')
        description = (
            f'LinkedIn guest listing for query "{query}". '
            'Open the job URL for full description and compensation.'
        )
        return build_canonical_job(
            id=f"linkedin-{raw_job.get('id', 'unknown')}",
            title=str(raw_job.get('title') or 'Unknown Role'),
            company=str(raw_job.get('company') or 'Unknown Company'),
            location=location,
            remote_type=infer_remote_type(None, location),
            source=self.name,
            url=str(raw_job.get('url') or ''),
            description=strip_html(description),
        )

    def health_check(self) -> bool:
        response = get_response(
            self._search_url(self._queries()[0], self._locations()[0]),
            headers=BROWSER_HEADERS,
        )
        return bool(response and self._parse_cards(response.text))
