"""Deterministic salary extraction from job descriptions (no LLM)."""

from __future__ import annotations

import re
from typing import Dict, Iterable, List, Optional

NOT_SPECIFIED = 'Not Specified'

# Ordered patterns — first match wins. Groups capture the human-readable salary span.
_SALARY_PATTERNS: List[re.Pattern[str]] = [
    re.compile(
        r'(?:salary|compensation|pay(?:\s+range)?|package|remuneration)'
        r'[:\s-]*'
        r'((?:USD|INR|EUR|GBP|CAD|AUD|\$|€|£|₹)\s*[\d,]+(?:\.\d+)?\s*[kK]?'
        r'(?:\s*[-–—]\s*(?:USD|INR|EUR|GBP|CAD|AUD|\$|€|£|₹)?\s*[\d,]+(?:\.\d+)?\s*[kK]?)?'
        r'(?:\s*(?:per\s+(?:year|annum|annually)|/yr|/year|p\.?a\.?|LPA|lpa))?'
        r')',
        re.IGNORECASE,
    ),
    re.compile(
        r'((?:USD|INR|EUR|GBP|CAD|AUD|\$|€|£|₹)\s*[\d,]+(?:\.\d+)?\s*[kK]'
        r'\s*[-–—]\s*(?:USD|INR|EUR|GBP|CAD|AUD|\$|€|£|₹)?\s*[\d,]+(?:\.\d+)?\s*[kK]'
        r'(?:\s*(?:per\s+(?:year|annum)|/yr|/year|p\.?a\.?|LPA|lpa))?)',
        re.IGNORECASE,
    ),
    re.compile(
        r'([\d,]+(?:\.\d+)?\s*(?:LPA|lpa))',
        re.IGNORECASE,
    ),
    re.compile(
        r'((?:USD|INR|EUR|GBP|CAD|AUD|\$|€|£|₹)\s*[\d,]+(?:\.\d+)?\s*[kK]?'
        r'(?:\s*(?:per\s+(?:year|annum|annually)|/yr|/year|p\.?a\.?))?)',
        re.IGNORECASE,
    ),
    re.compile(
        r'(\$[\d,]+(?:\.\d+)?\s*(?:[-–—]\s*\$[\d,]+(?:\.\d+)?)?)',
    ),
]


def _normalize_match(raw: str) -> str:
    """Collapse whitespace and trim punctuation from a salary span."""
    cleaned = re.sub(r'\s+', ' ', raw).strip(' .,;:')
    return cleaned if cleaned else NOT_SPECIFIED


def _search_texts(job: Dict) -> Iterable[str]:
    """Yield searchable text fields from a job record."""
    for key in ('description', 'title', 'salaryEstimate', 'compensation'):
        value = job.get(key)
        if value and str(value).strip() and str(value).strip().lower() not in {
            'not specified',
            'unknown',
            'n/a',
        }:
            yield str(value)


def extract_salary(job: Dict) -> str:
    """
    Extract a salary string from job text using regex/heuristics only.

    Returns ``Not Specified`` when no confident match is found.
    """
    for text in _search_texts(job):
        for pattern in _SALARY_PATTERNS:
            match = pattern.search(text)
            if match:
                normalized = _normalize_match(match.group(1))
                if normalized != NOT_SPECIFIED and len(normalized) >= 3:
                    return normalized
    return NOT_SPECIFIED


def extract_salary_with_source(job: Dict) -> tuple[str, Optional[str]]:
    """Return salary text and the field it was extracted from."""
    for key in ('description', 'title', 'salaryEstimate', 'compensation'):
        value = job.get(key)
        if not value or str(value).strip().lower() in {'not specified', 'unknown', 'n/a'}:
            continue
        text = str(value)
        for pattern in _SALARY_PATTERNS:
            match = pattern.search(text)
            if match:
                normalized = _normalize_match(match.group(1))
                if normalized != NOT_SPECIFIED and len(normalized) >= 3:
                    return normalized, key
    return NOT_SPECIFIED, None


# Approximate FX used only for salary-floor comparisons (not payroll).
_USD_TO_INR = 83.0
_EUR_TO_INR = 90.0
_GBP_TO_INR = 105.0
_LPA_INR = 100_000.0


def _parse_money_token(token: str) -> Optional[float]:
    """Parse a single money token into a raw numeric amount (pre-currency)."""
    cleaned = token.strip().lower().replace(',', '')
    cleaned = re.sub(r'^(usd|inr|eur|gbp|cad|aud|\$|€|£|₹)\s*', '', cleaned)
    match = re.match(r'^([\d.]+)\s*([kmb])?$', cleaned)
    if not match:
        return None
    value = float(match.group(1))
    suffix = match.group(2)
    if suffix == 'k':
        value *= 1_000
    elif suffix == 'm':
        value *= 1_000_000
    elif suffix == 'b':
        value *= 1_000_000_000
    return value


def salary_ceiling_lpa_inr(salary_text: str) -> Optional[float]:
    """
    Convert a salary string to an approximate annual ceiling in Lakh INR (LPA).

    Returns ``None`` when the text cannot be parsed confidently.
    For ranges, uses the upper bound so roles that can clear the floor still pass.
    """
    text = (salary_text or '').strip()
    if not text or text.lower() in {NOT_SPECIFIED.lower(), 'unknown', 'n/a'}:
        return None

    lower = text.lower()

    lpa_matches = re.findall(r'([\d.]+)\s*lpa', lower)
    if lpa_matches:
        return max(float(value) for value in lpa_matches)

    lakh_matches = re.findall(r'([\d.]+)\s*(?:lakh|lac)s?', lower)
    if lakh_matches:
        return max(float(value) for value in lakh_matches)

    inr_matches = re.findall(r'(?:₹|inr)\s*([\d,]+(?:\.\d+)?)', lower)
    if inr_matches:
        amounts = [float(value.replace(',', '')) for value in inr_matches]
        return max(amounts) / _LPA_INR

    usd_matches = re.findall(r'(?:\$|usd)\s*([\d,]+(?:\.\d+)?\s*[kmb]?)', lower)
    if usd_matches:
        amounts = [_parse_money_token(value) for value in usd_matches]
        valid = [amount for amount in amounts if amount is not None]
        if valid:
            return (max(valid) * _USD_TO_INR) / _LPA_INR

    eur_matches = re.findall(r'(?:€|eur)\s*([\d,]+(?:\.\d+)?\s*[kmb]?)', lower)
    if eur_matches:
        amounts = [_parse_money_token(value) for value in eur_matches]
        valid = [amount for amount in amounts if amount is not None]
        if valid:
            return (max(valid) * _EUR_TO_INR) / _LPA_INR

    gbp_matches = re.findall(r'(?:£|gbp)\s*([\d,]+(?:\.\d+)?\s*[kmb]?)', lower)
    if gbp_matches:
        amounts = [_parse_money_token(value) for value in gbp_matches]
        valid = [amount for amount in amounts if amount is not None]
        if valid:
            return (max(valid) * _GBP_TO_INR) / _LPA_INR

    # Bare "120k - 180k" / year style when currency markers are missing.
    bare = re.findall(r'([\d,]+(?:\.\d+)?\s*[k])', lower)
    if bare and any(token in lower for token in ('year', 'annum', '/yr', 'p.a', 'pa')):
        amounts = [_parse_money_token(value) for value in bare]
        valid = [amount for amount in amounts if amount is not None]
        if valid:
            return (max(valid) * _USD_TO_INR) / _LPA_INR

    return None


def job_meets_min_salary_lpa(job: Dict, min_lpa: float) -> bool:
    """
    Return True when salary is unknown or the parsed ceiling is >= ``min_lpa``.

    Unknown salaries are allowed so ATS postings without pay data are not dropped.
    """
    salary = extract_salary(job)
    ceiling = salary_ceiling_lpa_inr(salary)
    if ceiling is None:
        return True
    return ceiling + 1e-9 >= float(min_lpa)
