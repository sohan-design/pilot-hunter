"""Deterministic salary extraction — re-exported from scanner_sdk."""

from packages.scanner_sdk.python.salary import (
    NOT_SPECIFIED,
    extract_salary,
    extract_salary_with_source,
    job_meets_min_salary_lpa,
    salary_ceiling_lpa_inr,
)

__all__ = [
    'NOT_SPECIFIED',
    'extract_salary',
    'extract_salary_with_source',
    'job_meets_min_salary_lpa',
    'salary_ceiling_lpa_inr',
]
