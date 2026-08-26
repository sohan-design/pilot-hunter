import unittest

from scanners.linkedin.scanner import LinkedInScanner


SAMPLE_CARD_HTML = """
<li>
  <div class="base-card relative w-full base-card--link base-search-card base-search-card--link job-search-card">
    <a class="base-card__full-link absolute top-0"
       href="https://in.linkedin.com/jobs/view/senior-product-designer-at-sense-4453425441?position=1"></a>
    <h3 class="base-search-card__title">
        Senior Product Designer
    </h3>
    <h4 class="base-search-card__subtitle">
      <a href="https://www.linkedin.com/company/sense">
            Sense
      </a>
    </h4>
    <span class="job-search-card__location">
      Bengaluru, Karnataka, India
    </span>
  </div>
</li>
"""


class TestLinkedInScanner(unittest.TestCase):
    def test_parse_cards_extracts_title_company_location(self):
        cards = LinkedInScanner()._parse_cards(SAMPLE_CARD_HTML)
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]['title'], 'Senior Product Designer')
        self.assertEqual(cards[0]['company'], 'Sense')
        self.assertIn('Bengaluru', cards[0]['location'])
        self.assertIn('/jobs/view/', cards[0]['url'])

    def test_normalize_builds_canonical_job(self):
        scanner = LinkedInScanner()
        job = scanner.normalize(
            {
                'id': '4453425441',
                'title': 'Senior Product Designer',
                'company': 'Sense',
                'location': 'Bengaluru, Karnataka, India',
                'url': 'https://in.linkedin.com/jobs/view/senior-product-designer-at-sense-4453425441',
                '_query': 'Senior Product Designer',
            }
        )
        self.assertEqual(job['id'], 'linkedin-4453425441')
        self.assertEqual(job['source'], 'LinkedIn')
        self.assertEqual(job['title'], 'Senior Product Designer')


if __name__ == '__main__':
    unittest.main()
