import xml.etree.ElementTree as ET
from typing import Dict, List

from packages.scanner_sdk.python.base import BaseScanner
from packages.scanner_sdk.python.http import fetch_ok, get_text
from packages.scanner_sdk.python.normalize import build_canonical_job, is_design_job_title, strip_html

RSS_URL = 'https://weworkremotely.com/categories/remote-design-jobs.rss'
FALLBACK_RSS_URL = 'https://weworkremotely.com/remote-jobs.rss'


class WeWorkRemotelyScanner(BaseScanner):
    """We Work Remotely design-category RSS (falls back to full feed)."""

    @property
    def name(self) -> str:
        return 'We Work Remotely'

    def discover_jobs(self, limit: int = 10) -> List[Dict]:
        jobs = self._parse_feed(RSS_URL, limit, design_only=False)
        if jobs:
            return jobs
        return self._parse_feed(FALLBACK_RSS_URL, limit, design_only=True)

    def _parse_feed(self, url: str, limit: int, *, design_only: bool) -> List[Dict]:
        xml_text = get_text(url)
        if not xml_text:
            return []

        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            print(f'[WeWorkRemotelyScanner] RSS parse error: {exc}')
            return []

        jobs: List[Dict] = []
        for item in root.findall('.//item'):
            title = (item.findtext('title') or '').strip()
            link = (item.findtext('link') or '').strip()
            description = (item.findtext('description') or '').strip()
            region = (item.findtext('region') or 'Remote').strip()
            if not title or not link:
                continue
            role = title.split(':', 1)[-1].strip() if ':' in title else title
            if design_only and not is_design_job_title(role):
                continue
            jobs.append(
                {
                    'title': title,
                    'link': link,
                    'description': description,
                    'region': region,
                }
            )
            if len(jobs) >= limit:
                break
        return jobs

    def normalize(self, raw_job: Dict) -> Dict:
        title = raw_job.get('title', 'Unknown Role')
        company = title
        role = title
        if ':' in title:
            company, role = [part.strip() for part in title.split(':', 1)]

        link = raw_job.get('link', '')
        job_id = link.rstrip('/').split('/')[-1] or title.replace(' ', '-').lower()

        return build_canonical_job(
            id=f'wwr-{job_id}',
            title=role,
            company=company,
            location=raw_job.get('region', 'Remote'),
            remote_type='Remote',
            source=self.name,
            url=link,
            description=strip_html(raw_job.get('description', '')),
        )

    def health_check(self) -> bool:
        return fetch_ok(RSS_URL) or fetch_ok(FALLBACK_RSS_URL)
