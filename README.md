# Ecommerce Crawler

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
python main.py
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


## How It Works
1.**Initialization:**

- Configures retailer-specific patterns for product and pagination detection.
- Sets up default HTTP headers and user-agent rotation.
2. **Crawling:**

- Fetches pages asynchronously.
- Detects valid product URLs based on domain-specific patterns.
- Handles JavaScript-heavy websites using Playwright when necessary.

3. **Link Extraction:**

- Extracts and normalizes links using BeautifulSoup.
- Filters links based on retailer-specific patterns and domain rules.

4. **Output:**

- Saves discovered product URLs to a JSON file.
- Logs crawling statistics.

## Example Output
**JSON File (product_urls.json):**

```json
{
    "amazon.com": [
        "https://amazon.com/product1",
        "https://amazon.com/product2"
    ],
    "lowes.com":[
    ...
    ],
    ...
}
```

**Console Output:**

```yaml
Crawling Statistics:
Total Requests: 200
Successful Requests: 180
Failed Requests: 20
Success Rate: 90.00%
Total Duration: 300.00 seconds
```

## Dependencies
- aiohttp: Asynchronous HTTP client for efficient web crawling.
- playwright: Handles JavaScript rendering for dynamic web pages.
- BeautifulSoup: Parses HTML and extracts links.
- fake_useragent: Generates randomized user-agents.
- aiohttp_retry: Adds retry logic to failed requests.
- brotli and gzip: Decompression libraries for handling encoded responses.

```bash
pip install aiohttp playwright beautifulsoup4 fake-useragent aiohttp-retry brotli
```

## Limitations
- Heavy JavaScript Sites: Crawling JavaScript-heavy websites is slower due to rendering overhead.
- Timeouts: Large websites with high depth may cause timeouts.
- Captcha Handling: No support for bypassing captchas.
  
## Future Improvements
- Add support for more retailers with custom patterns. (Zip based/ Region Locked Sites)
- Integrate proxy rotation for IP-based rate limiting. (Squid Proxy Server)
- Implement captcha-solving capabilities.


