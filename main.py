"""
Multi-Source Web Scraping & Data Consolidation Pipeline Entry Point.

Runs Books to Scrape and Quotes to Scrape scrapers, cleans, validates,
deduplicates, and consolidates records into final_dataset.csv and summary_report.json.
"""

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, List

import pandas as pd

from processing.cleaning import clean_record
from processing.deduplication import deduplicate_records
from processing.validation import validate_dataset
from scrapers.books_scraper import BooksScraper
from scrapers.quotes_scraper import QuotesScraper
from scrapers.utils import HttpFetcher

# Standardized CSV column ordering
CSV_COLUMNS = [
    "source",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "source_url",
    "scraped_at",
]


def setup_logging(log_file: Path) -> None:
    """
    Configure Python logging to output to both console and logs/scraper.log file.

    :param log_file: Path to log file.
    """
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Clear existing handlers if any
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File Handler
    file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


def save_csv(records: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Save standardized records to a CSV file.

    :param records: List of record dictionaries.
    :param output_path: Destination Path for CSV file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(records)

    # Ensure all required columns exist even if empty
    for col in CSV_COLUMNS:
        if col not in df.columns:
            df[col] = None

    # Reorder columns
    df = df[CSV_COLUMNS]
    df.to_csv(output_path, index=False, encoding="utf-8")
    logging.getLogger(__name__).info(f"Successfully saved {len(records)} records to CSV: {output_path}")


def save_json(data: Dict[str, Any], output_path: Path) -> None:
    """
    Save summary report dictionary to JSON file.

    :param data: Summary dictionary.
    :param output_path: Destination Path for JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    logging.getLogger(__name__).info(f"Successfully saved summary report to JSON: {output_path}")


def run_pipeline(max_pages: int = None, delay: float = 0.1) -> Dict[str, Any]:
    """
    Execute the full scraping and data processing pipeline.

    :param max_pages: Optional page limit per scraper for quick testing (None for full scrape).
    :param delay: HTTP request delay in seconds.
    :return: Summary metrics dictionary.
    """
    start_time = time.time()
    logger = logging.getLogger(__name__)

    base_dir = Path(__file__).parent.resolve()
    output_dir = base_dir / "output"
    csv_file = output_dir / "final_dataset.csv"
    summary_file = output_dir / "summary_report.json"

    logger.info("==================================================")
    logger.info("Starting Multi-Source Web Scraping & Consolidation")
    logger.info("==================================================")

    fetcher = HttpFetcher(delay_between_requests=delay)

    # 1. Scrape Books
    books_records: List[Dict[str, Any]] = []
    books_error = None
    try:
        books_scraper = BooksScraper(fetcher=fetcher)
        books_records = books_scraper.scrape(max_pages=max_pages)
    except Exception as e:
        books_error = str(e)
        logger.error(f"Books scraper encountered a critical error: {e}", exc_info=True)

    # 2. Scrape Quotes
    quotes_records: List[Dict[str, Any]] = []
    quotes_error = None
    try:
        quotes_scraper = QuotesScraper(fetcher=fetcher)
        quotes_records = quotes_scraper.scrape(max_pages=max_pages)
    except Exception as e:
        quotes_error = str(e)
        logger.error(f"Quotes scraper encountered a critical error: {e}", exc_info=True)

    total_scraped = len(books_records) + len(quotes_records)
    logger.info(f"Scraping completed. Raw total records collected: {total_scraped}")

    # 3. Clean records
    raw_combined = books_records + quotes_records
    cleaned_records = [clean_record(rec) for rec in raw_combined]
    logger.info(f"Cleaning completed. Records cleaned: {len(cleaned_records)}")

    # 4. Validate records
    valid_records, rejected_records, val_stats = validate_dataset(cleaned_records)

    # 5. Deduplicate records
    unique_records, dedupe_stats = deduplicate_records(valid_records)

    # 6. Save outputs
    save_csv(unique_records, csv_file)

    execution_time = round(time.time() - start_time, 2)

    # 7. Generate summary statistics
    summary_report = {
        "pipeline_status": "SUCCESS" if (not books_error and not quotes_error) else "PARTIAL_FAILURE",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "books": {
            "records_scraped": len(books_records),
            "status": "FAILED" if books_error else "SUCCESS",
            "error": books_error,
        },
        "quotes": {
            "records_scraped": len(quotes_records),
            "status": "FAILED" if quotes_error else "SUCCESS",
            "error": quotes_error,
        },
        "total_records_scraped": total_scraped,
        "records_after_cleaning": len(cleaned_records),
        "validation": {
            "valid": val_stats["valid"],
            "rejected": val_stats["rejected"],
            "failure_reasons": val_stats["failure_reasons"],
        },
        "duplicates": {
            "detected": dedupe_stats["detected"],
            "removed": dedupe_stats["removed"],
        },
        "final_record_count": len(unique_records),
        "execution_time_seconds": execution_time,
    }

    save_json(summary_report, summary_file)

    logger.info("==================================================")
    logger.info("Pipeline Execution Finished Successfully")
    logger.info(f"Total Scraped: {total_scraped} | Final Dataset Count: {len(unique_records)}")
    logger.info(f"Summary Report saved to: {summary_file}")
    logger.info("==================================================")

    return summary_report


def main():
    parser = argparse.ArgumentParser(
        description="Multi-Source Web Scraping & Data Consolidation Pipeline"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Maximum pages to scrape per website (default: None for full pagination)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between HTTP requests in seconds (default: 0.1)",
    )
    args = parser.parse_args()

    base_dir = Path(__file__).parent.resolve()
    log_file = base_dir / "logs" / "scraper.log"
    setup_logging(log_file)

    run_pipeline(max_pages=args.max_pages, delay=args.delay)


if __name__ == "__main__":
    main()
