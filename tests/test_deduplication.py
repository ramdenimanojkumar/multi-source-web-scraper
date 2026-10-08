"""
Unit tests for processing/deduplication.py
"""

import unittest
from processing.deduplication import deduplicate_records, generate_dedupe_key


class TestDeduplication(unittest.TestCase):
    def setUp(self):
        self.book1 = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/page-1.html",
            "name_or_title": "A Light in the Attic",
            "category": "Poetry",
            "price": 51.77,
            "rating": 3.0,
            "author": None,
            "tags": None,
            "description": "Desc",
            "scraped_at": "2026-10-08T09:00:00Z",
        }

        self.book1_duplicate_diff_case = {
            "source": "  books to scrape ",
            "source_url": "https://books.toscrape.com/catalogue/page-2.html",
            "name_or_title": "  a light in the attic  ",
            "category": "Poetry",
            "price": 51.77,
            "rating": 3.0,
            "author": None,
            "tags": None,
            "description": "Desc",
            "scraped_at": "2026-10-08T09:05:00Z",
        }

        self.book2 = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/page-1.html",
            "name_or_title": "Tipping the Velvet",
            "category": "Sequential Art",
            "price": 53.74,
            "rating": 1.0,
            "author": None,
            "tags": None,
            "description": "Desc 2",
            "scraped_at": "2026-10-08T09:00:00Z",
        }

        self.quote1 = {
            "source": "Quotes to Scrape",
            "source_url": "https://quotes.toscrape.com/",
            "name_or_title": "The world as we have created it is a process of our thinking.",
            "category": None,
            "price": None,
            "rating": None,
            "author": "Albert Einstein",
            "tags": "change",
            "description": "Bio",
            "scraped_at": "2026-10-08T09:00:00Z",
        }

        self.quote1_dup = {
            "source": "Quotes to Scrape",
            "source_url": "https://quotes.toscrape.com/page/2/",
            "name_or_title": "  the world as we have created it is a process of our thinking.  ",
            "category": None,
            "price": None,
            "rating": None,
            "author": "albert einstein",
            "tags": "change",
            "description": "Bio",
            "scraped_at": "2026-10-08T09:05:00Z",
        }

    def test_key_generation(self):
        key1 = generate_dedupe_key(self.book1)
        key2 = generate_dedupe_key(self.book1_duplicate_diff_case)
        self.assertEqual(key1, key2)
        self.assertEqual(key1, "books|a light in the attic")

    def test_deduplicate_identical_and_variations(self):
        records = [self.book1, self.book1_duplicate_diff_case, self.book2]
        unique_recs, stats = deduplicate_records(records)

        self.assertEqual(len(unique_recs), 2)
        self.assertEqual(stats["detected"], 1)
        self.assertEqual(stats["removed"], 1)
        self.assertEqual(unique_recs[0]["name_or_title"], "A Light in the Attic")
        self.assertEqual(unique_recs[1]["name_or_title"], "Tipping the Velvet")

    def test_deduplicate_quotes(self):
        records = [self.quote1, self.quote1_dup]
        unique_recs, stats = deduplicate_records(records)

        self.assertEqual(len(unique_recs), 1)
        self.assertEqual(stats["detected"], 1)
        self.assertEqual(stats["removed"], 1)

    def test_genuinely_different_records(self):
        records = [self.book1, self.book2, self.quote1]
        unique_recs, stats = deduplicate_records(records)

        self.assertEqual(len(unique_recs), 3)
        self.assertEqual(stats["detected"], 0)


if __name__ == "__main__":
    unittest.main()
