# AI Usage Declaration & Disclosure Document

## 1. AI Tools Used
- **Google Antigravity / Gemini 3.6 Flash (High)**: Used as the primary AI coding assistant for project scaffolding, HTML analysis, documentation drafting, test case generation, and refactoring.

## 2. Why Each Tool Was Used
- **Gemini 3.6 Flash**: Selected for fast code generation, accurate Python type hint recommendations, standard library adherence, structured Markdown documentation, and rapid unit test generation.

## 3. Representative Prompts
- *"Analyze the HTML structure of books.toscrape.com and quotes.toscrape.com and suggest robust BeautifulSoup selectors for automatic pagination and detail page parsing."*
- *"Design a clean, modular Python pipeline architecture separating scraping, cleaning, validation, deduplication, and output generation."*
- *"Implement a deterministic composite key deduplication strategy in Python that normalizes whitespace, casing, and punctuation."*
- *"Generate comprehensive Pytest unit tests for data cleaning, validation rules, and deduplication logic without relying on live web requests."*

## 4. Which Code Sections Were AI-Assisted
- **Scraper Modules (`scrapers/books_scraper.py`, `scrapers/quotes_scraper.py`)**: AI provided initial HTML parsing templates, BeautifulSoup selector strategies, and author page caching logic.
- **Processing Modules (`processing/cleaning.py`, `processing/validation.py`, `processing/deduplication.py`)**: AI generated initial regular expressions for price cleaning, rating word mapping, validation rules, and composite key normalization.
- **Pipeline Coordinator (`main.py`)**: AI assisted in framing `argparse` CLI options, output logging setup, and CSV/JSON reporting logic.
- **Unit Tests (`tests/`)**: AI drafted edge-case test vectors for price extraction, rating bounds, and duplicate detection.

## 5. What Was Reviewed Manually
- Verified that pagination uses dynamic link extraction (`urllib.parse.urljoin`) and contains **no hard-coded page limits** or fixed `range(1, N)` loops.
- Ensured no prohibited frameworks (Selenium, Playwright, Scrapy, Django) or paid APIs were added.
- Inspected rating map dictionary (`"One"` -> `1.0` ... `"Five"` -> `5.0`) and price regex parsing.
- Verified that missing HTML fields return `None` or appropriate empty values without raising uncaught exceptions.
- Checked CSV column formatting and validated `summary_report.json` schema metrics.

## 6. Changes Made After Reviewing AI-Generated Code
- **Fixed Regex for Negative Prices**: The original AI suggestion for `clean_price` extracted `10.0` from `"-10.00"`. Updated the regex to `r"(-?\d+(?:\.\d+)?)"` to explicitly recognize negative numbers as invalid prices.
- **Added Author Information Caching**: Enhanced `QuotesScraper` with an in-memory `author_cache` dictionary to prevent redundant HTTP requests when multiple quotes belong to the same author.
- **Standardized Field Mapping**: Adjusted field assignment for quotes so `quote` text maps to `name_or_title` while `price` and `rating` are explicitly set to `None`.
- **Added Graceful Fallback in `main.py`**: Added try/except blocks around each scraper phase so that if one website fails, the pipeline continues processing and saving data from the remaining source.

## 7. Incorrect or Incomplete AI Suggestions Discovered
- **Price Regex Flaw**: Initial AI code did not handle leading minus signs in price strings, returning positive numbers for negative inputs. Handled manually during unit test verification.
- **Rating Case Sensitivity**: Initial code was sensitive to lowercase `"three"`. Fixed by normalizing rating input to `.lower()` before map lookup.

## 8. Final Verification Process
1. Clean environment installation test via `pip install -r requirements.txt`.
2. Full test suite run using `python -m pytest tests/` (18 unit tests passed).
3. End-to-end execution of `python main.py` scraping live practice websites.
4. Inspection of `output/final_dataset.csv` and `output/summary_report.json`.
5. Log verification in `logs/scraper.log`.
