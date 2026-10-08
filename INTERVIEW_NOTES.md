# Technical Interview Preparation Notes

This document provides clear, concise, and technical answers to help explain every aspect of this project during an interview. All explanations strictly align with the codebase implementation.

---

## 1. Concepts & Architectural Decisions

### 1. What is Web Scraping?
Web scraping is the automated extraction of data from websites. It involves programmatically sending HTTP requests to web servers, retrieving HTML documents, parsing the HTML tree structure, and extracting structured data into formats like CSV or JSON.

### 2. Why Requests Was Used
- **Simplicity & Performance**: `requests` is a lightweight, synchronous HTTP library ideal for static HTML pages.
- **Low Overhead**: Unlike headless browsers (Selenium/Playwright), `requests` has minimal memory usage and executes requests fast.
- **Session Support**: Allows persistent HTTP connections (`requests.Session`), reducing TCP handshake overhead across pagination requests.

### 3. Why BeautifulSoup4 Was Used
- **Robust HTML Parsing**: `BeautifulSoup` gracefully handles messy or non-standard HTML.
- **Intuitive API**: Enables navigating and searching the DOM tree using CSS selectors (`soup.select`), tag finding (`soup.find_all`), and attribute inspection (`tag.get("href")`).

### 4. How Automatic Pagination Works
- **Dynamic Link Discovery**: The scrapers inspect each page for the "Next" pagination element (`<li class="next"><a href="...">`).
- **URL Resolution**: Using `urllib.parse.urljoin(current_url, next_href)`, relative links are dynamically resolved to absolute URLs.
- **Termination**: The pagination loop continues until `soup.find("li", class_="next")` returns `None`, guaranteeing full traversal without hardcoding page numbers.

### 5. HTML Structure Differences Between Sources
- **Books to Scrape**:
  - Main catalog pages list products in `<article class="product_pod">`.
  - Book title is in `h3 > a['title']`.
  - Rating is embedded as a CSS class name (`<p class="star-rating Three">`).
  - Category and full descriptions are retrieved by navigating to each book's product detail page.
- **Quotes to Scrape**:
  - Quotes are listed in `<div class="quote">`.
  - Quote text is in `<span class="text">`, author in `<small class="author">`, and tags in `<a class="tag">`.
  - Author bio/details are obtained by navigating to `/author/<name>` links, using an in-memory cache to prevent duplicate requests for the same author.

### 6. Standardized Data Model & Transformation
Raw scraped records from both sources are transformed into a single schema:
- `source` (str)
- `source_url` (str)
- `name_or_title` (str) — Book Title OR Quote Text
- `category` (str / None) — Book Category (None for Quotes)
- `price` (float / None) — Book Numeric Price (None for Quotes)
- `rating` (float / None) — Book Rating 1.0–5.0 (None for Quotes)
- `author` (str / None) — Quote Author (None for Books)
- `tags` (str / None) — Quote Tags (None for Books)
- `description` (str / None) — Book Description OR Author Bio
- `scraped_at` (str) — ISO timestamp

### 7. Data Cleaning Process
Implemented in `processing/cleaning.py`:
- **Whitespace**: Strips leading/trailing spaces, converts `\xa0` to standard space, collapses multiple spaces.
- **Price**: Uses regex `r"(-?\d+(?:\.\d+)?)"` to extract float values (e.g. `"£51.77"` -> `51.77`). Negative values are rejected.
- **Rating**: Maps words (`"One"`..`"Five"`) and numeric strings to a standardized `1.0` to `5.0` float scale.
- **Tags**: Joins tag lists into clean, comma-separated strings (`"change, thinking"`).

### 8. Validation Strategy
Implemented in `processing/validation.py`:
- Verifies required fields (`source`, `source_url`, `name_or_title`, `scraped_at`).
- Checks that `source` belongs to recognized sources.
- Validates URL syntax (`http://` or `https://`).
- Ensures numeric `price >= 0.0` and `rating` between `1.0` and `5.0`.
- Invalid records are separated into `rejected_records` with logged failure reasons, preventing pipeline crashes.

### 9. Duplicate Detection Strategy
Implemented in `processing/deduplication.py`:
- **Normalization**: Fields are lowercased, stripped, and internal spaces collapsed before key creation.
- **Composite Key Scheme**:
  - Books: `books|<normalized_title>`
  - Quotes: `quotes|<normalized_author>|<normalized_quote_text>`
- **Behavior**: Maintains a set of seen keys. Duplicate records are filtered out, and statistics (`detected`, `removed`, `final_unique_count`) are tracked.

### 10. Error Handling & Resiliency
- **Page-Level Failures**: Handled via `HttpFetcher` retries with exponential backoff. If a page fails after retries, it is logged and skipped without crashing the loop.
- **Missing Elements**: Element lookups use optional checks (`if tag: tag.text`). Missing values default to `None`.
- **Pipeline Isolation**: `main.py` runs each scraper inside `try/except` blocks. If one source fails, data from the other source is still cleaned, validated, and exported.

### 11. Logging Strategy
- Standard Python `logging` module outputs simultaneously to `logs/scraper.log` and the terminal console.
- Logged events: scraper start, page requests, HTTP errors, parsing issues, validation rejections, duplicate removals, and final summary statistics.

### 12. Why Scraping and Processing Are Separated
Separation of concerns makes the codebase maintainable, testable, and reusable:
- Scrapers focus solely on HTTP requests and DOM parsing.
- Processing modules focus on business logic (cleaning, validation, deduplication) and can be unit-tested with mock data without sending web requests.

### 13. CSV Output Generation
`output/final_dataset.csv` is exported via `pandas.DataFrame.to_csv()` with UTF-8 encoding and standardized column ordering.

### 14. Summary Report Generation
`output/summary_report.json` captures execution metrics including raw counts, valid vs. rejected counts, duplicate counts, execution time, and source-level status.

### 15. Unit Testing Implementation
Built using `unittest` and run with `pytest`. Tests use mocked dictionaries and test strings to verify cleaning functions, validation rules, and composite key deduplication independently of live network calls.

### 16. Why Selenium / Playwright / Scrapy Were Not Used
- **No JavaScript Rendering Needed**: Both target websites serve static server-rendered HTML.
- **Minimal Dependencies**: `requests` + `BeautifulSoup` provides a clean, easy-to-explain implementation without browser driver overhead or complex framework boilerplate.

### 17. Limitations of the Current Implementation
- **Synchronous Execution**: Sequential HTTP requests limit speed when fetching detail pages.
- **In-Memory Dataset**: Storage in memory is suitable for thousands of records but would require batch processing or database storage for millions.

### 18. What Would Be Changed for Production
- **Async Scraping**: Use `aiohttp` or `httpx` for concurrent asynchronous requests.
- **Database Storage**: Replace CSV output with a PostgreSQL or MongoDB database pipeline.
- **Distributed Queues**: Use Celery/Redis for distributed task scheduling and proxy rotation.

---

## 2. Likely Interview Questions & Sample Answers

**Q1: How do you handle pagination if page numbers are not in the URL?**
> *Answer*: We don't rely on URL pattern matching or page numbers. Instead, we parse the HTML DOM tree on each page to find the `<li class="next"><a href="...">` tag. We extract the `href` attribute, resolve it using `urllib.parse.urljoin`, and continue fetching until no "Next" link exists in the DOM.

**Q2: What happens if an element (like price or rating) is missing on a page?**
> *Answer*: The scraper guards element extraction using conditional checks (e.g. `price_tag.text if price_tag else None`). If missing, it safely records `None` without raising an `AttributeError` or crashing the pipeline. During cleaning and validation, missing mandatory fields are flagged and handled cleanly.

**Q3: How do you avoid getting blocked while scraping?**
> *Answer*: We set a realistic `User-Agent` header, implement configurable request delays (`--delay`), use retries with exponential backoff, and avoid aggressive parallel scraping.

**Q4: How do you handle duplicate quotes or books with different capitalization?**
> *Answer*: In `processing/deduplication.py`, we normalize key fields before generating composite keys by converting text to lowercase, stripping whitespace, and collapsing internal spaces. For instance, `" A Light in the Attic "` and `"a light in the attic"` map to the exact same composite key (`books|a light in the attic`) and are deduplicated deterministically.
