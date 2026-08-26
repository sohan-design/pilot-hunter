"""Profile-driven filters applied before expensive AI enrichment."""

from dataclasses import dataclass
from typing import Dict, List

from packages.scanner_sdk.python.salary import job_meets_min_salary_lpa
from packages.config.python.remote_policy import analyze_remote_eligibility


@dataclass(frozen=True)
class PreferenceDecision:
    allowed: bool
    reason: str = ''


def _matches_any(value: str, patterns: List[str]) -> bool:
    normalized = value.lower()
    return any(str(pattern).strip().lower() in normalized for pattern in patterns if str(pattern).strip())


def evaluate_job_preferences(
    job: Dict,
    profile: Dict,
    existing_jobs: List[Dict],
) -> PreferenceDecision:
    """Reject jobs excluded by explicit profile preferences."""
    preferences = profile.get('preferences') or {}
    checks = (
        ('company', 'companyBlacklist', 'company_blacklist'),
        ('title', 'titleBlacklist', 'title_blacklist'),
        ('location', 'locationBlacklist', 'location_blacklist'),
    )
    for field, preference, reason in checks:
        if _matches_any(str(job.get(field) or ''), preferences.get(preference) or []):
            return PreferenceDecision(False, reason)

    title_whitelist = [
        str(pattern).strip()
        for pattern in (preferences.get('titleWhitelist') or [])
        if str(pattern).strip()
    ]
    if title_whitelist and not _matches_any(str(job.get('title') or ''), title_whitelist):
        return PreferenceDecision(False, 'title_whitelist')

    if preferences.get('applyOncePerCompany'):
        company = str(job.get('company') or '').strip().lower()
        if company and any(str(item.get('company') or '').strip().lower() == company for item in existing_jobs):
            return PreferenceDecision(False, 'already_seen_company')

    levels = [str(level).strip().lower() for level in preferences.get('experienceLevels') or []]
    seniority = str(job.get('seniority') or '').strip().lower()
    if levels and seniority and not any(level in seniority or seniority in level for level in levels):
        return PreferenceDecision(False, 'experience_level')

    if preferences.get('remotePreference') == 'Remote':
        text = f"{job.get('location', '')} {job.get('description', '')}"
        if analyze_remote_eligibility(text).hard_restriction:
            return PreferenceDecision(False, 'remote_restriction')

    min_salary_lpa = preferences.get('minSalaryLpa')
    if min_salary_lpa is not None and str(min_salary_lpa).strip() != '':
        try:
            floor = float(min_salary_lpa)
        except (TypeError, ValueError):
            floor = None
        if floor is not None and floor > 0 and not job_meets_min_salary_lpa(job, floor):
            return PreferenceDecision(False, 'salary_below_minimum')

    return PreferenceDecision(True)
