"""
Quotes to Scrape Scraper Module.

Scrapes quotes from https://quotes.toscrape.com using automatic pagination.
Extracts quote text, author, tags, author bio/details, and preserves metadata
(source, source_url, scraped_at).
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from scrapers.utils import HttpFetcher

logger = logging.getLogger(__name__)

BASE_URL = "https://quotes.toscrape.com/"
SOURCE_NAME = "Quotes to Scrape"


class QuotesScraper:
    """
    Scraper for Quotes to Scrape website with automatic pagination and author info caching.
    """

    def __init__(self, fetcher: Optional[HttpFetcher] = None):
        """
        Initialize QuotesScraper with an HttpFetcher instance and an author cache.
        """
        self.fetcher = fetcher or HttpFetcher()
        self.author_cache: Dict[str, Optional[str]] = {}

    def scrape(self, start_url: str = BASE_URL, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape quotes starting from start_url following pagination links until complete.

        :param start_url: Initial page URL.
        :param max_pages: Optional maximum page limit for testing/debugging (None for full scrape).
        :return: List of raw extracted record dictionaries.
        """
        logger.info(f"Starting Quotes scraper from URL: {start_url}")
        records: List[Dict[str, Any]] = []
        current_url: Optional[str] = start_url
        page_count = 0

        while current_url:
            page_count += 1
            if max_pages and page_count > max_pages:
                logger.info(f"Reached specified max_pages limit of {max_pages}. Stopping pagination.")
                break

            logger.info(f"Scraping Quotes page {page_count}: {current_url}")
            html_content = self.fetcher.fetch_page(current_url)

            if not html_content:
                logger.error(f"Failed to retrieve content for page: {current_url}. Skipping page.")
                break

            soup = BeautifulSoup(html_content, "html.parser")
            page_records, next_url = self._parse_quotes_page(soup, current_url)
            records.extend(page_records)
            logger.info(f"Extracted {len(page_records)} quotes from page {page_count}. Total so far: {len(records)}")

            current_url = next_url

        logger.info(f"Completed Quotes scraping. Total pages scraped: {page_count}, total records: {len(records)}")
        return records

    def _parse_quotes_page(self, soup: BeautifulSoup, current_url: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Parse a quotes listing page and extract quote items and next page URL.

        :param soup: BeautifulSoup parsed HTML object of current page.
        :param current_url: URL of the current page.
        :return: Tuple of (extracted records list, next page URL or None).
        """
        page_records: List[Dict[str, Any]] = []
        quote_elements = soup.find_all("div", class_="quote")

        for q_elem in quote_elements:
            try:
                record = self._extract_quote_from_elem(q_elem, current_url)
                if record:
                    page_records.append(record)
            except Exception as e:
                logger.warning(f"Error parsing quote element on {current_url}: {e}")

        # Automatic pagination: locate next page link
        next_li = soup.find("li", class_="next")
        next_url = None
        if next_li and next_li.find("a"):
            next_href = next_li.find("a").get("href")
            if next_href:
                next_url = urljoin(current_url, next_href)
                logger.debug(f"Discovered next page link: {next_url}")

        return page_records, next_url

    def _extract_quote_from_elem(self, elem: Any, current_url: str) -> Optional[Dict[str, Any]]:
        """
        Safely extract raw attributes from an individual quote element.

        :param elem: BeautifulSoup Tag representing div.quote.
        :param current_url: URL of page containing element.
        :return: Dict containing extracted raw quote fields.
        """
        # Quote text
        text_span = elem.find("span", class_="text")
        if not text_span:
            logger.warning("Found quote div missing text span. Skipping.")
            return None
        quote_text = text_span.text.strip()

        # Author name
        author_small = elem.find("small", class_="author")
        author_name = author_small.text.strip() if author_small else None

        # Tags
        tag_elems = elem.find_all("a", class_="tag")
        tags = [t.text.strip() for t in tag_elems if t.text]

        # Author link & details
        author_url = None
        author_link_tag = elem.find("a", href=lambda h: h and "/author/" in h)
        if author_link_tag and author_link_tag.get("href"):
            author_url = urljoin(current_url, author_link_tag.get("href"))

        author_info = None
        if author_url:
            author_info = self._fetch_author_info(author_url)

        scraped_at = datetime.now(timezone.utc).isoformat()

        raw_record = {
            "source": SOURCE_NAME,
            "source_url": current_url,
            "quote": quote_text,
            "author": author_name,
            "tags": tags,
            "author_url": author_url,
            "description": author_info,
            "scraped_at": scraped_at,
        }

        return raw_record

    def _fetch_author_info(self, author_url: str) -> Optional[str]:
        """
        Fetch author bio details with caching to avoid duplicate HTTP requests.

        :param author_url: Full URL to the author detail page.
        :return: String containing formatted author info or None.
        """
        if author_url in self.author_cache:
            return self.author_cache[author_url]

        author_info = None
        try:
            html = self.fetcher.fetch_page(author_url)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                born_date_span = soup.find("span", class_="author-born-date")
                born_loc_span = soup.find("span", class_="author-born-location")
                bio_div = soup.find("div", class_="author-description")

                born_date = born_date_span.text.strip() if born_date_span else ""
                born_loc = born_loc_span.text.strip() if born_loc_span else ""
                bio_text = bio_div.text.strip() if bio_div else ""

                parts = []
                if born_date or born_loc:
                    parts.append(f"Born {born_date} {born_loc}".strip())
                if bio_text:
                    parts.append(bio_text)

                author_info = " - ".join(parts) if parts else None
        except Exception as e:
            logger.warning(f"Could not fetch author details from {author_url}: {e}")

        self.author_cache[author_url] = author_info
        return author_info
