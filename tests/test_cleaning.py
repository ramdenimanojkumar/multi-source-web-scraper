"""
Unit tests for processing/cleaning.py
"""

import unittest
from processing.cleaning import (
    clean_whitespace,
    clean_price,
    clean_rating,
    clean_tags,
    clean_url,
    clean_record,
)


class TestCleaning(unittest.TestCase):
    def test_clean_whitespace(self):
        self.assertEqual(clean_whitespace("  The Book Title  "), "The Book Title")
        self.assertEqual(clean_whitespace("Hello\xa0World"), "Hello World")
        self.assertEqual(clean_whitespace("  Multiple   spaces   here "), "Multiple spaces here")
        self.assertIsNone(clean_whitespace("   "))
        self.assertIsNone(clean_whitespace(None))

    def test_clean_price(self):
        self.assertEqual(clean_price("£51.77"), 51.77)
        self.assertEqual(clean_price("  $19.99 "), 19.99)
        self.assertEqual(clean_price(15.5), 15.5)
        self.assertEqual(clean_price("0"), 0.0)
        self.assertIsNone(clean_price("free"))
        self.assertIsNone(clean_price("-10.00"))
        self.assertIsNone(clean_price(None))

    def test_clean_rating(self):
        self.assertEqual(clean_rating("Three"), 3.0)
        self.assertEqual(clean_rating("FIVE"), 5.0)
        self.assertEqual(clean_rating("one"), 1.0)
        self.assertEqual(clean_rating(4), 4.0)
        self.assertEqual(clean_rating("4.5"), 4.5)
        self.assertIsNone(clean_rating("Ten"))
        self.assertIsNone(clean_rating(6.0))
        self.assertIsNone(clean_rating(-1.0))
        self.assertIsNone(clean_rating(None))

    def test_clean_tags(self):
        self.assertEqual(clean_tags(["change", " deep-thoughts ", "world"]), "change, deep-thoughts, world")
        self.assertEqual(clean_tags("change, deep-thoughts, world"), "change, deep-thoughts, world")
        self.assertIsNone(clean_tags([]))
        self.assertIsNone(clean_tags(None))

    def test_clean_url(self):
        self.assertEqual(clean_url("  https://books.toscrape.com/index.html  "), "https://books.toscrape.com/index.html")
        self.assertIsNone(clean_url("not_a_url"))
        self.assertIsNone(clean_url(None))

    def test_clean_record_book(self):
        raw_book = {
            "source": "  Books to Scrape  ",
            "source_url": "https://books.toscrape.com/catalogue/page-1.html",
            "title": "  A Light in the Attic  ",
            "price": "£51.77",
            "rating": "Three",
            "category": "  Poetry  ",
            "description": "  A nice book  ",
            "scraped_at": "2026-10-08T09:00:00Z",
        }
        cleaned = clean_record(raw_book)
        self.assertEqual(cleaned["source"], "Books to Scrape")
        self.assertEqual(cleaned["name_or_title"], "A Light in the Attic")
        self.assertEqual(cleaned["price"], 51.77)
        self.assertEqual(cleaned["rating"], 3.0)
        self.assertEqual(cleaned["category"], "Poetry")
        self.assertIsNone(cleaned["author"])
        self.assertIsNone(cleaned["tags"])

    def test_clean_record_quote(self):
        raw_quote = {
            "source": "Quotes to Scrape",
            "source_url": "https://quotes.toscrape.com/",
            "quote": " “The world as we have created it...” ",
            "author": " Albert Einstein ",
            "tags": ["change", "deep-thoughts"],
            "description": " Born March 14, 1879 ",
            "scraped_at": "2026-10-08T09:00:00Z",
        }
        cleaned = clean_record(raw_quote)
        self.assertEqual(cleaned["source"], "Quotes to Scrape")
        self.assertEqual(cleaned["name_or_title"], "“The world as we have created it...”")
        self.assertEqual(cleaned["author"], "Albert Einstein")
        self.assertEqual(cleaned["tags"], "change, deep-thoughts")
        self.assertIsNone(cleaned["price"])
        self.assertIsNone(cleaned["rating"])


if __name__ == "__main__":
    unittest.main()
