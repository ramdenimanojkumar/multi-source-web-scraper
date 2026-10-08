# Multi-Source Web Scraping & Data Consolidation Pipeline

A robust, production-grade Python web scraping and data consolidation pipeline built to extract, clean, validate, deduplicate, and consolidate structured records from multiple practice e-commerce and quotes websites.

---

## 1. Project Overview
This project extracts unstructured data from two distinct web sources ([Books to Scrape](https://books.toscrape.com/) and [Quotes to Scrape](https://quotes.toscrape.com/)), transforms raw HTML elements into a unified, standardized schema, enforces quality and validation rules, detects duplicates deterministically, and generates structured CSV and JSON outputs.

## 2. Objective
- Demonstrate clean, maintainable, modular Python design without over-engineering.
- Implement **automatic pagination** without hardcoded page counts.
- Create a unified standardized data model combining e-commerce book metadata and quotes data.
- Ensure 100% testable, reproducible, and explainable code.

## 3. Technologies Used
- **Python 3.x** (Standard Library & Core Packages)
- **Requests**: HTTP client for fetching HTML pages with session management and retries.
- **BeautifulSoup4**: Parsing and extracting DOM elements.
- **Pandas**: Structured CSV dataset generation.
- **Pytest / Unittest**: Unit testing framework.

## 4. Python Version Requirements
- Python `3.9+` (Tested on Python `3.14`)

---

## 5. Required Project Structure
```
scraping_assignment/
│
├── scrapers/
│   ├── __init__.py
│   ├── utils.py               # HttpFetcher with retry logic & rate limiting
│   ├── books_scraper.py       # Books to Scrape scraper
│   └── quotes_scraper.py      # Quotes to Scrape scraper
│
├── processing/
│   ├── __init__.py
│   ├── cleaning.py            # Whitespace, price, rating & record cleaning
│   ├── validation.py          # Quality rules & record validation
│   └── deduplication.py       # Deterministic composite key deduplication
│
├── output/
│   ├── final_dataset.csv      # Consolidated CSV output
│   └── summary_report.json    # JSON summary metrics report
│
├── logs/
│   └── scraper.log            # Execution log file
│
├── tests/
│   ├── __init__.py
│   ├── test_cleaning.py       # Unit tests for cleaning logic
│   ├── test_validation.py     # Unit tests for validation rules
│   └── test_deduplication.py  # Unit tests for duplicate detection
│
├── main.py                    # Pipeline entry point & coordinator
├── requirements.txt           # Project dependencies
├── README.md                  # Detailed documentation
├── AI_USAGE.md                # Transparency & AI usage report
└── INTERVIEW_NOTES.md         # Technical interview preparation guide
```

---

## 6. Setup Instructions & Environment Setup

### Step 1: Clone or Navigate to Project Directory
```bash
cd scraping_assignment
```

### Step 2: Create a Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  python -m venv venv
  venv\Scripts\activate.bat
  ```
- **Linux / macOS**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 7. How to Run the Pipeline

### Run Full Pipeline
To run the complete pipeline across all pages of both websites:
```bash
python main.py
```

### Run with Custom Options (CLI Parameters)
- **Fast Test Run (Limit max pages per site)**:
  ```bash
  python main.py --max-pages 2
  ```
- **Custom Request Delay**:
  ```bash
  python main.py --delay 0.2
  ```

---

## 8. How Pagination Works
The scraper uses **automatic dynamic pagination**. It does **NOT** use fixed page ranges like `for page in range(1, 5)`.

1. The scraper starts at the initial URL (e.g. `https://books.toscrape.com/index.html`).
2. After extracting items on the page, it searches the HTML DOM for the "Next" link:
   - Books: `soup.find("li", class_="next").find("a")["href"]`
   - Quotes: `soup.find("li", class_="next").find("a")["href"]`
3. Relative URLs are resolved using `urllib.parse.urljoin(current_url, next_href)`.
4. The loop continues fetching subsequent pages until `find("li", class_="next")` returns `None`.

---

## 9. Scraper Implementations

### Books Scraper (`scrapers/books_scraper.py`)
- Target: `https://books.toscrape.com/`
- Extracts product title, price (`£51.77`), availability, star rating (`Three`), and product link from catalog pages.
- Navigates to individual product detail pages to extract category (from breadcrumbs) and full product description.

### Quotes Scraper (`scrapers/quotes_scraper.py`)
- Target: `https://quotes.toscrape.com/`
- Extracts quote text, author name, and tag list.
- Navigates to author detail pages to extract birth date, location, and bio snippet.
- Implements an **author cache** (`author_cache`) to prevent redundant requests when multiple quotes share the same author.

---

## 10. Standardized Data Model
All scraped data is mapped into a common unified schema:

| Standardized Field | Books Mapping | Quotes Mapping |
| :--- | :--- | :--- |
| `source` | `"Books to Scrape"` | `"Quotes to Scrape"` |
| `source_url` | Catalog page URL | Quotes page URL |
| `name_or_title` | Book Title | Quote Text |
| `category` | Category (e.g., "Poetry") | `None` |
| `price` | Numeric Float (e.g., `51.77`) | `None` |
| `rating` | Numeric Float (`1.0` to `5.0`) | `None` |
| `author` | `None` | Author Name |
| `tags` | `None` | Comma-separated tags string |
| `description` | Product Description | Author Bio / Birth Info |
| `scraped_at` | ISO 8601 UTC Timestamp | ISO 8601 UTC Timestamp |

---

## 11. Data Cleaning (`processing/cleaning.py`)
- **Whitespace Normalization**: Removes leading/trailing spaces, replaces non-breaking space `\xa0`, and collapses multiple consecutive spaces into a single space.
- **Price Conversion**: Extracts numeric values via regex `r"(-?\d+(?:\.\d+)?)"` and converts strings like `"£51.77"` to `51.77`. Rejects negative numbers.
- **Rating Standardization**: Maps word ratings (`"One"`..`"Five"`) and numeric strings to a standard float scale `1.0`–`5.0`.
- **Tags Formatting**: Converts tag arrays into clean, comma-separated strings (`"change, thinking"`).

---

## 12. Validation Rules (`processing/validation.py`)
Each record is validated against strict quality constraints:
- `source`, `source_url`, `name_or_title`, and `scraped_at` are required and non-empty.
- `source` must be recognized (`"Books to Scrape"` or `"Quotes to Scrape"`).
- `source_url` must be a valid HTTP/HTTPS URL.
- `price` (if present) must be a float `>= 0.0`.
- `rating` (if present) must be a float between `1.0` and `5.0`.

Invalid records are logged and isolated into `rejected_records` without stopping the pipeline execution.

---

## 13. Duplicate Detection Strategy (`processing/deduplication.py`)
To prevent relying on simple raw string matches:
1. Key fields (`name_or_title`, `author`, `source`) are stripped, lowercased, and internal spaces collapsed.
2. A deterministic composite key is generated:
   - Books: `books|<normalized_title>`
   - Quotes: `quotes|<normalized_author>|<normalized_quote>`
3. Deduplication tracks metrics: `detected`, `removed`, and `final_unique_count`.

---

## 14. Error Handling & Resiliency
- **Transient Network Failures**: `HttpFetcher` uses retries (default 3) with exponential backoff.
- **Page Failures**: If a page fails after max retries, it is logged and skipped without crashing the pagination loop.
- **Missing Elements**: Uses safe element inspection (`if tag: tag.text`). Missing elements default to `None`.
- **Source Failure Isolation**: If one scraper fails entirely, the pipeline logs the error and continues processing data collected from the other source.

---

## 15. Logging (`logs/scraper.log`)
Configured using Python's standard `logging` library. Logs output to both `logs/scraper.log` and the terminal console, recording scraper progress, HTTP attempts, validation failures, deduplication stats, and final timing metrics.

---

## 16. Output Files
1. `output/final_dataset.csv`: Cleaned, validated, deduplicated records.
2. `output/summary_report.json`: Execution metrics summary.

---

## 17. How to Run Tests
Run the unit test suite using `pytest`:
```bash
python -m pytest tests/
```
Or using Python's built-in `unittest`:
```bash
python -m unittest discover tests
```

---

## 18. Assumptions
- Practice websites ([books.toscrape.com](https://books.toscrape.com/) and [quotes.toscrape.com](https://quotes.toscrape.com/)) remain publicly accessible without requiring authentication or CAPTCHAs.
- Book titles and Quote text remain stable primary identifiers for duplicate detection.

## 19. Limitations
- Sequential HTTP requests take ~30-60 seconds for 1,000 detail pages.
- Memory usage scales with the dataset size (suitable for thousands of records; larger scales require database stream writing).

## 20. AI Usage Summary
AI (Gemini 3.6 Flash) was used for initial code generation, HTML selector drafting, and test vector generation. All generated code was manually reviewed, debugged, tested, and modified (see `AI_USAGE.md`).

## 21. Ethical & Legal Considerations
- Scraping is limited exclusively to public practice sandbox websites designed specifically for web scraping practice.
- Respectful request rates (`--delay`) are enforced.
- No CAPTCHAs, paywalls, robots.txt restrictions, or authentication controls were bypassed.
