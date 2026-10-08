"""
Books to Scrape Scraper Module.

Scrapes books from https://books.toscrape.com using automatic pagination.
Extracts title, price, availability, rating, category, product URL, description,
and preserves metadata (source, source_url, scraped_at).
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from scrapers.utils import HttpFetcher

logger = logging.getLogger(__name__)

BASE_URL = "https://books.toscrape.com/"
SOURCE_NAME = "Books to Scrape"


class BooksScraper:
    """
    Scraper for Books to Scrape website with automatic pagination support.
    """

    def __init__(self, fetcher: Optional[HttpFetcher] = None):
        """
        Initialize BooksScraper with an HttpFetcher instance.
        """
        self.fetcher = fetcher or HttpFetcher()

    def scrape(self, start_url: str = BASE_URL, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Scrape books starting from start_url following pagination links until complete.

        :param start_url: Initial page URL.
        :param max_pages: Optional maximum page limit for testing/debugging (None for full scrape).
        :return: List of raw extracted record dictionaries.
        """
        logger.info(f"Starting Books scraper from URL: {start_url}")
        records: List[Dict[str, Any]] = []
        current_url: Optional[str] = start_url
        page_count = 0

        while current_url:
            page_count += 1
            if max_pages and page_count > max_pages:
                logger.info(f"Reached specified max_pages limit of {max_pages}. Stopping pagination.")
                break

            logger.info(f"Scraping Books page {page_count}: {current_url}")
            html_content = self.fetcher.fetch_page(current_url)

            if not html_content:
                logger.error(f"Failed to retrieve content for page: {current_url}. Skipping page.")
                # Attempt to determine next page or stop
                break

            soup = BeautifulSoup(html_content, "html.parser")
            page_records, next_url = self._parse_catalog_page(soup, current_url)
            records.extend(page_records)
            logger.info(f"Extracted {len(page_records)} books from page {page_count}. Total so far: {len(records)}")

            current_url = next_url

        logger.info(f"Completed Books scraping. Total pages scraped: {page_count}, total records: {len(records)}")
        return records

    def _parse_catalog_page(self, soup: BeautifulSoup, current_url: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Parse a catalog listing page and extract book pods and next page URL.

        :param soup: BeautifulSoup parsed HTML object of current page.
        :param current_url: URL of the current page.
        :return: Tuple of (extracted records list, next page URL or None).
        """
        page_records: List[Dict[str, Any]] = []
        product_pods = soup.find_all("article", class_="product_pod")

        for pod in product_pods:
            try:
                record = self._extract_book_from_pod(pod, current_url)
                if record:
                    page_records.append(record)
            except Exception as e:
                logger.warning(f"Error parsing book pod on {current_url}: {e}")

        # Automatic pagination: locate next page link
        next_li = soup.find("li", class_="next")
        next_url = None
        if next_li and next_li.find("a"):
            next_href = next_li.find("a").get("href")
            if next_href:
                next_url = urljoin(current_url, next_href)
                logger.debug(f"Discovered next page link: {next_url}")

        return page_records, next_url

    def _extract_book_from_pod(self, pod: Any, current_url: str) -> Optional[Dict[str, Any]]:
        """
        Safely extract raw attributes from an individual product pod element.
        Fetches the product detail page to retrieve category and full description.

        :param pod: BeautifulSoup Tag representing article.product_pod.
        :param current_url: URL of page containing pod.
        :return: Dict containing extracted raw book fields.
        """
        # Title
        h3_a = pod.find("h3").find("a") if pod.find("h3") else None
        if not h3_a:
            logger.warning("Found product_pod missing title link. Skipping pod.")
            return None

        title = h3_a.get("title") or h3_a.text.strip()
        rel_product_url = h3_a.get("href", "")
        product_url = urljoin(current_url, rel_product_url) if rel_product_url else current_url

        # Price
        price_tag = pod.find("p", class_="price_color")
        price = price_tag.text.strip() if price_tag else None

        # Availability
        avail_tag = pod.find("p", class_="instock availability")
        availability = avail_tag.text.strip() if avail_tag else None

        # Rating (extracted from class e.g. "star-rating Three")
        rating = None
        rating_tag = pod.find("p", class_=lambda c: c and "star-rating" in c)
        if rating_tag and "class" in rating_tag.attrs:
            classes = [c for c in rating_tag["class"] if c != "star-rating"]
            rating = classes[0] if classes else None

        # Fetch detail page for Category and Description
        category = None
        description = None
        if product_url:
            detail_category, detail_desc = self._fetch_book_details(product_url)
            category = detail_category
            description = detail_desc

        scraped_at = datetime.now(timezone.utc).isoformat()

        raw_record = {
            "source": SOURCE_NAME,
            "source_url": current_url,
            "product_url": product_url,
            "title": title,
            "price": price,
            "availability": availability,
            "rating": rating,
            "category": category,
            "description": description,
            "scraped_at": scraped_at,
        }

        return raw_record

    def _fetch_book_details(self, detail_url: str) -> tuple[Optional[str], Optional[str]]:
        """
        Fetch product detail page to extract Category and Description.

        :param detail_url: URL of product detail page.
        :return: Tuple of (category, description).
        """
        category = None
        description = None

        try:
            detail_html = self.fetcher.fetch_page(detail_url)
            if detail_html:
                detail_soup = BeautifulSoup(detail_html, "html.parser")

                # Category from breadcrumbs (Home > Books > Category > Title)
                breadcrumb_ul = detail_soup.find("ul", class_="breadcrumb")
                if breadcrumb_ul:
                    lis = breadcrumb_ul.find_all("li")
                    if len(lis) >= 3:
                        category = lis[2].text.strip()

                # Description from product description section
                desc_div = detail_soup.find("div", id="product_description")
                if desc_div:
                    p_sibling = desc_div.find_next_sibling("p")
                    if p_sibling:
                        description = p_sibling.text.strip()

        except Exception as e:
            logger.warning(f"Could not fetch/parse detail page for {detail_url}: {e}")

        return category, description
