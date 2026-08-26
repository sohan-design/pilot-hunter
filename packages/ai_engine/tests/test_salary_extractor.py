"""Unit tests for deterministic salary extraction."""

import unittest

from packages.ai_engine.python.salary_extractor import (
    NOT_SPECIFIED,
    extract_salary,
    job_meets_min_salary_lpa,
    salary_ceiling_lpa_inr,
)


class TestSalaryExtractor(unittest.TestCase):
    def test_extracts_usd_range_with_label(self):
        job = {
            'description': 'Salary: $120k – $180k per year plus equity.',
        }
        self.assertEqual(extract_salary(job), '$120k – $180k per year')

    def test_extracts_dollar_range(self):
        job = {'description': 'We offer $90,000 - $110,000 annually.'}
        result = extract_salary(job)
        self.assertIn('$90,000', result)

    def test_extracts_lpa(self):
        job = {'description': 'Compensation up to 35 LPA for the right candidate.'}
        self.assertIn('LPA', extract_salary(job))

    def test_extracts_euro_amount(self):
        job = {'description': 'Package: €80,000 per annum.'}
        result = extract_salary(job)
        self.assertIn('€80,000', result)

    def test_returns_not_specified_when_missing(self):
        job = {'description': 'Great team, flexible hours, no pay details.'}
        self.assertEqual(extract_salary(job), NOT_SPECIFIED)

    def test_prefers_existing_valid_salary_field(self):
        job = {
            'salaryEstimate': 'USD 150k - 180k',
            'description': 'No numbers here.',
        }
        self.assertIn('150k', extract_salary(job))

    def test_salary_ceiling_parses_lpa_range(self):
        ceiling = salary_ceiling_lpa_inr('18 - 25 LPA')
        self.assertIsNotNone(ceiling)
        self.assertGreaterEqual(ceiling or 0, 25)

    def test_job_meets_min_salary_rejects_low_lpa(self):
        job = {'description': 'Compensation: 12 LPA fixed'}
        self.assertFalse(job_meets_min_salary_lpa(job, 20))

    def test_job_meets_min_salary_allows_unknown(self):
        job = {'description': 'No compensation listed'}
        self.assertTrue(job_meets_min_salary_lpa(job, 20))

    def test_job_meets_min_salary_allows_high_usd(self):
        job = {'description': 'Salary: $120k – $180k per year'}
        self.assertTrue(job_meets_min_salary_lpa(job, 20))


if __name__ == '__main__':
    unittest.main()
