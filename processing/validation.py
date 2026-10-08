"""
Data Validation Module.

Validates standardized records against defined quality and schema rules.
Filters out invalid records, logs specific validation failure details,
and returns validation metrics.
"""

import logging
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

RECOGNIZED_SOURCES = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(record: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single standardized record.

    Validation Rules:
    1. Required fields must be present and non-empty: source, source_url, name_or_title, scraped_at.
    2. Source must be one of the recognized source names.
    3. source_url must be a valid HTTP/HTTPS URL.
    4. If price is present (not None), it must be a float/int >= 0.0.
    5. If rating is present (not None), it must be a float/int between 1.0 and 5.0 inclusive.

    :param record: Standardized record dictionary.
    :return: Tuple of (is_valid boolean, list of error messages).
    """
    errors: List[str] = []

    # Rule 1: Check source presence & recognition
    source = record.get("source")
    if not source:
        errors.append("Missing required field: 'source'")
    elif source not in RECOGNIZED_SOURCES:
        errors.append(f"Unrecognized source: '{source}'. Expected one of {RECOGNIZED_SOURCES}")

    # Rule 2: Check name_or_title presence
    name_or_title = record.get("name_or_title")
    if not name_or_title or not str(name_or_title).strip():
        errors.append("Missing or empty required field: 'name_or_title'")

    # Rule 3: Check source_url valid URL
    source_url = record.get("source_url")
    if not source_url:
        errors.append("Missing required field: 'source_url'")
    else:
        try:
            parsed = urlparse(source_url)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append(f"Invalid URL structure in 'source_url': '{source_url}'")
        except Exception as e:
            errors.append(f"Could not parse 'source_url': '{source_url}' ({e})")

    # Rule 4: Check scraped_at presence
    scraped_at = record.get("scraped_at")
    if not scraped_at:
        errors.append("Missing required field: 'scraped_at'")

    # Rule 5: Numeric price validation (if present)
    price = record.get("price")
    if price is not None:
        if not isinstance(price, (float, int)) or price < 0:
            errors.append(f"Invalid price value: '{price}'. Price must be a non-negative number.")

    # Rule 6: Rating range validation (if present)
    rating = record.get("rating")
    if rating is not None:
        if not isinstance(rating, (float, int)) or not (1.0 <= rating <= 5.0):
            errors.append(f"Invalid rating value: '{rating}'. Rating must be a number between 1.0 and 5.0.")

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_dataset(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Validate a list of standardized records.

    :param records: List of standardized records.
    :return: Tuple of (valid_records list, rejected_records list, validation_stats dict).
    """
    valid_records: List[Dict[str, Any]] = []
    rejected_records: List[Dict[str, Any]] = []
    failure_reasons: Dict[str, int] = {}

    for index, record in enumerate(records):
        is_valid, errors = validate_record(record)
        if is_valid:
            valid_records.append(record)
        else:
            record_copy = dict(record)
            record_copy["_validation_errors"] = errors
            rejected_records.append(record_copy)

            title_preview = record.get("name_or_title", f"Record index {index}")
            logger.warning(f"Record validation failed for '{title_preview}': {', '.join(errors)}")

            for err in errors:
                err_category = err.split(":")[0] if ":" in err else err
                failure_reasons[err_category] = failure_reasons.get(err_category, 0) + 1

    stats = {
        "total_evaluated": len(records),
        "valid": len(valid_records),
        "rejected": len(rejected_records),
        "failure_reasons": failure_reasons,
    }

    logger.info(
        f"Validation complete: {len(valid_records)} valid, {len(rejected_records)} rejected out of {len(records)} records."
    )
    return valid_records, rejected_records, stats
