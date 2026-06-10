# Week 07 - Web Scraping and Dataset Collection

## Conceptual Focus
Collect a text corpus from the web to power later indexing and search.

## Core Track (graded)
- HTTP requests with requests.
- Extract plain text with BeautifulSoup.
- Save articles as JSON: {title, url, text, fetched_at}.
- Scrape a list of URLs politely with delays.

## Exploration Track (optional)
- Structured parsing, crawling, retry logic.
- Logging, Wikipedia API, robots.txt ethics.

## Mini Project (5 marks)
Wikipedia Dataset Collector:
- collect_wiki.py reads urls.txt and saves JSON files to corpus/.
- Handle errors and log progress.
