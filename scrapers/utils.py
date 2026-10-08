"""
HTTP Request Helper Utilities.

Provides a robust HTTP fetcher with retry logic, exponential backoff,
timeout management, rate limiting, and exception logging.
"""

import logging
import time
from typing import Optional
import requests

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36 MultiSourceScraper/1.0"
    )
}


class HttpFetcher:
    """
    HTTP Fetcher class that manages session requests with automatic retries,
    exponential backoff, rate limiting, and timeout configuration.
    """

    def __init__(
        self,
        timeout: int = 10,
        max_retries: int = 3,
        backoff_factor: float = 1.0,
        delay_between_requests: float = 0.1,
    ):
        """
        Initialize the HTTP Fetcher.

        :param timeout: Timeout in seconds for HTTP requests.
        :param max_retries: Maximum retry attempts for transient errors.
        :param backoff_factor: Multiplier for exponential backoff delay.
        :param delay_between_requests: Rate limiting delay (seconds) between requests.
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.delay = delay_between_requests
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def fetch_page(self, url: str) -> Optional[str]:
        """
        Fetch HTML content from a URL with retry logic and error logging.

        :param url: Page URL to fetch.
        :return: HTML string if successful, None if fetch failed.
        """
        if self.delay > 0:
            time.sleep(self.delay)

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(f"Requesting URL: {url} (Attempt {attempt}/{self.max_retries})")
                response = self.session.get(url, timeout=self.timeout)

                # Handle standard HTTP status codes
                if response.status_code == 200:
                    logger.info(f"Successfully fetched page: {url}")
                    return response.text
                elif response.status_code == 404:
                    logger.warning(f"Page not found (404): {url}")
                    return None
                else:
                    logger.warning(
                        f"HTTP {response.status_code} for {url} (Attempt {attempt}/{self.max_retries})"
                    )

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout accessing {url} (Attempt {attempt}/{self.max_retries})")
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"Connection error for {url}: {e} (Attempt {attempt}/{self.max_retries})")
            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed for {url}: {e} (Attempt {attempt}/{self.max_retries})")

            # Exponential backoff sleep before retrying
            if attempt < self.max_retries:
                sleep_time = self.backoff_factor * (2 ** (attempt - 1))
                logger.info(f"Retrying in {sleep_time:.1f}s for {url}")
                time.sleep(sleep_time)

        logger.error(f"Failed to fetch page after {self.max_retries} attempts: {url}")
        return None
