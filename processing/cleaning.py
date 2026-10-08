"""
Data Cleaning Module.

Provides reusable functions to clean whitespace, convert prices to numeric float,
standardize ratings, format tags, validate URLs, and transform raw records into
the standardized pipeline data model.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

# Rating lookup mapping for word-based ratings
RATING_MAP = {
    "one": 1.0,
    "two": 2.0,
    "three": 3.0,
    "four": 4.0,
    "five": 5.0,
}


def clean_whitespace(text: Optional[str]) -> Optional[str]:
    """
    Remove leading/trailing whitespace, replace non-breaking spaces,
    and collapse multiple internal whitespace characters into a single space.

    :param text: Input raw string or None.
    :return: Cleaned normalized string or None.
    """
    if text is None:
        return None
    if not isinstance(text, str):
        text = str(text)

    # Replace non-breaking space \xa0 with standard space
    cleaned = text.replace("\xa0", " ")
    # Collapse multiple whitespace characters (spaces, tabs, newlines) into one space
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned if cleaned else None


def clean_price(price_raw: Union[str, float, int, None]) -> Optional[float]:
    """
    Convert raw price input (e.g. "£51.77", "  51.77 ") into a float.

    :param price_raw: Raw price value.
    :return: Numeric float value or None if invalid/missing.
    """
    if price_raw is None:
        return None

    if isinstance(price_raw, (float, int)):
        val = float(price_raw)
        return val if val >= 0 else None

    price_str = str(price_raw).strip()
    if not price_str:
        return None

    # Extract numeric digits with optional leading sign and optional decimal point using regex
    match = re.search(r"(-?\d+(?:\.\d+)?)", price_str)
    if match:
        try:
            val = float(match.group(1))
            return val if val >= 0 else None
        except ValueError:
            return None

    return None


def clean_rating(rating_raw: Union[str, float, int, None]) -> Optional[float]:
    """
    Standardize rating to a float scale of 1.0 to 5.0.
    Handles word ratings (e.g. "Three", "Five") and numeric inputs.

    :param rating_raw: Raw rating value.
    :return: Float rating between 1.0 and 5.0, or None if invalid.
    """
    if rating_raw is None:
        return None

    if isinstance(rating_raw, (float, int)):
        r_float = float(rating_raw)
        return r_float if 1.0 <= r_float <= 5.0 else None

    rating_str = str(rating_raw).strip().lower()
    if not rating_str:
        return None

    # Check word map
    if rating_str in RATING_MAP:
        return RATING_MAP[rating_str]

    # Check numeric string
    match = re.search(r"(-?\d+(?:\.\d+)?)", rating_str)
    if match:
        try:
            r_float = float(match.group(1))
            return r_float if 1.0 <= r_float <= 5.0 else None
        except ValueError:
            return None

    return None


def clean_tags(tags_raw: Union[List[str], str, None]) -> Optional[str]:
    """
    Convert tags list or raw string into a clean comma-separated string.

    :param tags_raw: List of tag strings or a single comma-separated string.
    :return: Cleaned comma-separated string or None.
    """
    if tags_raw is None:
        return None

    if isinstance(tags_raw, list):
        cleaned_list = [clean_whitespace(t) for t in tags_raw if clean_whitespace(t)]
        return ", ".join(cleaned_list) if cleaned_list else None

    if isinstance(tags_raw, str):
        parts = tags_raw.split(",")
        cleaned_list = [clean_whitespace(p) for p in parts if clean_whitespace(p)]
        return ", ".join(cleaned_list) if cleaned_list else None

    return None


def clean_url(url_raw: Optional[str]) -> Optional[str]:
    """
    Clean and validate URL format.

    :param url_raw: Raw URL string.
    :return: Cleaned URL or None if invalid.
    """
    cleaned = clean_whitespace(url_raw)
    if not cleaned:
        return None

    try:
        parsed = urlparse(cleaned)
        if parsed.scheme in ("http", "https") and parsed.netloc:
            return cleaned
    except Exception:
        pass

    return None


def clean_record(raw_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform a raw extracted record dictionary into the standardized schema format.

    Standardized Schema:
    - source
    - source_url
    - name_or_title
    - category
    - price
    - rating
    - author
    - tags
    - description
    - scraped_at

    :param raw_record: Raw record from books or quotes scraper.
    :return: Standardized cleaned record dictionary.
    """
    source = clean_whitespace(raw_record.get("source"))
    source_url = clean_url(raw_record.get("source_url"))
    scraped_at = clean_whitespace(raw_record.get("scraped_at"))

    if source == "Books to Scrape":
        name_or_title = clean_whitespace(raw_record.get("title"))
        category = clean_whitespace(raw_record.get("category"))
        price = clean_price(raw_record.get("price"))
        rating = clean_rating(raw_record.get("rating"))
        author = None
        tags = None
        description = clean_whitespace(raw_record.get("description"))

    elif source == "Quotes to Scrape":
        name_or_title = clean_whitespace(raw_record.get("quote"))
        category = None
        price = None
        rating = None
        author = clean_whitespace(raw_record.get("author"))
        tags = clean_tags(raw_record.get("tags"))
        description = clean_whitespace(raw_record.get("description"))

    else:
        # Fallback / generic mapping
        name_or_title = clean_whitespace(
            raw_record.get("name_or_title") or raw_record.get("title") or raw_record.get("quote")
        )
        category = clean_whitespace(raw_record.get("category"))
        price = clean_price(raw_record.get("price"))
        rating = clean_rating(raw_record.get("rating"))
        author = clean_whitespace(raw_record.get("author"))
        tags = clean_tags(raw_record.get("tags"))
        description = clean_whitespace(raw_record.get("description"))

    standardized_record = {
        "source": source,
        "source_url": source_url,
        "name_or_title": name_or_title,
        "category": category,
        "price": price,
        "rating": rating,
        "author": author,
        "tags": tags,
        "description": description,
        "scraped_at": scraped_at,
    }

    return standardized_record
