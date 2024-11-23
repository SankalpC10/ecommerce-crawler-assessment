# Enhanced Ecommerce Crawler

## Overview
The Enhanced Ecommerce Crawler is a Python-based asynchronous web crawler designed for efficiently discovering and extracting product URLs from e-commerce websites. The crawler supports advanced features like JavaScript rendering, user-agent rotation, and compliance with robots.txt. It also incorporates retailer-specific patterns for improved crawling precision.

## 🌟 Features
- Asynchronous Crawling: Uses asyncio and aiohttp for high-performance, concurrent crawling.
- JavaScript Rendering: Optionally uses Playwright to handle JavaScript-heavy websites.
- Custom Headers & User-Agent Rotation: Simulates browser-like behavior with customizable headers and rotating user-agents.
- Retailer-Specific Patterns: Tailored crawling rules for popular retailers (e.g., Amazon, Walmart).
- Robots.txt Compliance: Optionally respects robots.txt rules.
- Human-like Behavior: Simulates scrolling and adds random delays between requests.
- Error Handling: Logs errors and retries failed requests for robust crawling.
- Session Management: Stores cookies and localStorage data for maintaining session continuity.
- Crawling Statistics: Tracks performance metrics like success rate, total requests, and duration.


## Installation
```bash
git clone https://github.com/SankalpC10/ecommerce-crawler-assessment.git
cd ecommerce-crawler-assessment
pip install -r requirements.txt
playwright install #For JS rendering
```

## Usage
Configure Domains: Specify the target domains in the domains list.

Run the Crawler:

```bash
python ecommerce_crawler.py
```
- Crawled product URLs are saved in product_urls.json.
- Crawling statistics are printed to the console.

## Configuration Options

Parameter | Description |	Default
--- | --- | ---
domains	List of e-commerce | domains to crawl. |	Required
max_depth |	Maximum depth for recursive crawling. |	3
concurrent_requests |	Number of concurrent requests per domain. |	5
custom_headers |	Additional HTTP headers for requests. |	None
rotate_user_agents |	Whether to use randomized user-agents. |	True
use_playwright |	Enable JavaScript rendering for handling dynamic content. |	True
respect_robots |	Whether to honor robots.txt rules. |	True
delay_range |	Range of random delays (in seconds) between requests to simulate human-like behavior. |	(2, 5)

