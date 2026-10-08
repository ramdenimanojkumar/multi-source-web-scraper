"""
Unit tests for processing/validation.py
"""

import unittest
from processing.validation import validate_record, validate_dataset


class TestValidation(unittest.TestCase):
    def setUp(self):
        self.valid_book = {
            "source": "Books to Scrape",
            "source_url": "https://books.toscrape.com/catalogue/page-1.html",
            "name_or_title": "A Light in the Attic",
            "category": "Poetry",
            "price": 51.77,
            "rating": 3.0,
            "author": None,
            "tags": None,
            "description": "Book bio",
            "scraped_at": "2026-10-08T09:00:00Z",
        }

        self.valid_quote = {
            "source": "Quotes to Scrape",
            "source_url": "https://quotes.toscrape.com/",
            "name_or_title": "The world as we have created it...",
            "category": None,
            "price": None,
            "rating": None,
            "author": "Albert Einstein",
            "tags": "change, thinking",
            "description": "Author bio",
            "scraped_at": "2026-10-08T09:00:00Z",
        }

    def test_valid_records(self):
        is_valid_b, errors_b = validate_record(self.valid_book)
        self.assertTrue(is_valid_b)
        self.assertEqual(len(errors_b), 0)

        is_valid_q, errors_q = validate_record(self.valid_quote)
        self.assertTrue(is_valid_q)
        self.assertEqual(len(errors_q), 0)

    def test_missing_required_fields(self):
        invalid_rec = dict(self.valid_book)
        invalid_rec["name_or_title"] = ""
        is_valid, errors = validate_record(invalid_rec)
        self.assertFalse(is_valid)
        self.assertTrue(any("name_or_title" in e for e in errors))

    def test_invalid_price(self):
        invalid_rec = dict(self.valid_book)
        invalid_rec["price"] = -5.0
        is_valid, errors = validate_record(invalid_rec)
        self.assertFalse(is_valid)
        self.assertTrue(any("price" in e for e in errors))

    def test_invalid_rating(self):
        invalid_rec = dict(self.valid_book)
        invalid_rec["rating"] = 10.0
        is_valid, errors = validate_record(invalid_rec)
        self.assertFalse(is_valid)
        self.assertTrue(any("rating" in e for e in errors))

    def test_invalid_url(self):
        invalid_rec = dict(self.valid_book)
        invalid_rec["source_url"] = "ftp://invalid-url"
        is_valid, errors = validate_record(invalid_rec)
        self.assertFalse(is_valid)
        self.assertTrue(any("source_url" in e for e in errors))

    def test_unrecognized_source(self):
        invalid_rec = dict(self.valid_book)
        invalid_rec["source"] = "Unknown Scraper Site"
        is_valid, errors = validate_record(invalid_rec)
        self.assertFalse(is_valid)
        self.assertTrue(any("Unrecognized source" in e for e in errors))

    def test_validate_dataset(self):
        invalid_rec = dict(self.valid_book)
        invalid_rec["name_or_title"] = None

        dataset = [self.valid_book, self.valid_quote, invalid_rec]
        valid_recs, rejected_recs, stats = validate_dataset(dataset)

        self.assertEqual(len(valid_recs), 2)
        self.assertEqual(len(rejected_recs), 1)
        self.assertEqual(stats["valid"], 2)
        self.assertEqual(stats["rejected"], 1)


if __name__ == "__main__":
    unittest.main()
