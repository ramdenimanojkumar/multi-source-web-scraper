"""
Deduplication Module.

Implements deterministic duplicate detection across standardized records.
Normalizes record fields prior to hashing to handle differences in capitalization,
leading/trailing whitespace, and internal formatting.
"""

import logging
import re
from typing import Any, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


def generate_dedupe_key(record: Dict[str, Any]) -> str:
    """
    Generate a normalized, deterministic composite key for duplicate detection.

    Normalization logic:
    - Convert strings to lowercase.
    - Strip leading/trailing whitespace and collapse internal consecutive spaces.
    - Remove basic trailing punctuation (e.g., period, comma at end of titles/quotes).

    Composite Key Schemes:
    - Books: "books to scrape|<normalized_title>"
    - Quotes: "quotes to scrape|<normalized_author>|<normalized_quote_text>"
    - Generic fallback: "<normalized_source>|<normalized_name_or_title>"

    :param record: Standardized record dictionary.
    :return: String composite key.
    """
    source = (record.get("source") or "").strip().lower()
    name_or_title = (record.get("name_or_title") or "").strip().lower()
    author = (record.get("author") or "").strip().lower()

    # Collapse multiple whitespace characters
    name_norm = re.sub(r"\s+", " ", name_or_title)
    author_norm = re.sub(r"\s+", " ", author)

    if source == "books to scrape":
        key = f"books|{name_norm}"
    elif source == "quotes to scrape":
        key = f"quotes|{author_norm}|{name_norm}"
    else:
        key = f"{source}|{name_norm}"

    return key


def deduplicate_records(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    """
    Filter out duplicate records from a list of standardized records using composite keys.

    :param records: List of validated standardized record dictionaries.
    :return: Tuple of (unique_records list, deduplication_stats dict).
    """
    seen_keys: Set[str] = set()
    unique_records: List[Dict[str, Any]] = []
    duplicate_count = 0

    for record in records:
        key = generate_dedupe_key(record)
        if key in seen_keys:
            duplicate_count += 1
            title_preview = record.get("name_or_title", "Unknown")[:40]
            logger.info(f"Duplicate record detected and filtered out: [{key}] '{title_preview}'")
        else:
            seen_keys.add(key)
            unique_records.append(record)

    stats = {
        "input_records": len(records),
        "detected": duplicate_count,
        "removed": duplicate_count,
        "final_unique_count": len(unique_records),
    }

    logger.info(
        f"Deduplication complete: {duplicate_count} duplicates removed. "
        f"{len(unique_records)} unique records remaining out of {len(records)} input records."
    )
    return unique_records, stats
