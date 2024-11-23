import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Set, Optional
import logging
import random
from fake_useragent import UserAgent
from datetime import datetime
from playwright.async_api import async_playwright
from urllib.parse import urlparse, urljoin
import json


class EnhancedEcommerceCrawler:
    def __init__(
            self,
            domains: List[str],
            max_depth: int = 3,
            concurrent_requests: int = 5,
            custom_headers: Dict[str, str] = None,
            rotate_user_agents: bool = True,
            use_playwright: bool = True,
            respect_robots: bool = True,
            delay_range: tuple = (2, 5)
    ):
        self.domains = [self._normalize_domain(domain) for domain in domains]
        self.max_depth = max_depth
        self.concurrent_requests = concurrent_requests
        self.custom_headers = custom_headers or {}
        self.rotate_user_agents = rotate_user_agents
        self.use_playwright = use_playwright
        self.respect_robots = respect_robots
        self.delay_range = delay_range

        # session storage for cookies and tokens
        self.session_storage = {}

        # robots.txt parsers
        self.robots_parsers = {}

        # URL patterns for different retailers
        self.retailer_patterns = self._initialize_retailer_patterns()

        self.ua = UserAgent()

        # headers with browser-like behavior
        self.default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'sec-ch-ua': '"Google Chrome";v="119", "Chromium";v="119", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }

        self.stats = {
            'requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'end_time': None
        }

        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)

    def _initialize_retailer_patterns(self) -> Dict[str, Dict]:
        return {
            'amazon': {
                'product_patterns': [
                    r'/dp/[A-Z0-9]{10}',
                    r'/gp/product/[A-Z0-9]{10}'
                ],
                'pagination_patterns': [
                    r'page=\d+',
                    r'pg=\d+'
                ],
                'js_required': True
            },
            'walmart': {
                'product_patterns': [
                    r'/ip/',
                    r'/products?/'
                ],
                'pagination_patterns': [
                    r'page=\d+'
                ],
                'js_required': True
            },
            'default': {
                'product_patterns': [
                    r'/product/',
                    r'/item/',
                    r'/p/',
                    r'/products?/',
                    r'/shop/',
                    r'\d{4,8}'
                ],
                'pagination_patterns': [
                    r'page=\d+',
                    r'p=\d+'
                ],
                'js_required': False
            }
        }

    async def _handle_javascript_site(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=self.ua.random
            )

            page = await context.new_page()

            # common browser fingerprints
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
            """)

            try:
                # Set random delay before navigation
                await asyncio.sleep(random.uniform(*self.delay_range))

                # Navigate and wait for network idle
                await page.goto(url, wait_until='networkidle')

                # Scroll to simulate human behavior
                await self._simulate_scrolling(page)

                content = await page.content()

                # Store session tokens or cookies
                self.session_storage[urlparse(url).netloc] = {
                    'cookies': await context.cookies(),
                    'localStorage': await page.evaluate('() => JSON.stringify(localStorage)')
                }

                return content

            except Exception as e:
                self.logger.error(f"Playwright error for {url}: {e}")
                return ""
            finally:
                await browser.close()

    async def _simulate_scrolling(self, page):
        try:
            # Get page height
            height = await page.evaluate('document.body.scrollHeight')

            # Scroll in chunks with random delays
            for i in range(0, height, random.randint(200, 500)):
                await page.evaluate(f'window.scrollTo(0, {i})')
                await asyncio.sleep(random.uniform(0.1, 0.3))

            # Scroll back up randomly
            if random.random() < 0.3:
                await page.evaluate('window.scrollTo(0, 0)')

        except Exception as e:
            self.logger.error(f"Error during scrolling simulation: {e}")

    def _detect_site_type(self, url: str) -> Dict:
        domain = urlparse(url).netloc

        for retailer, patterns in self.retailer_patterns.items():
            if retailer in domain:
                return patterns

        return self.retailer_patterns['default']

    async def _fetch_with_fallback(self, url: str, session) -> str:
        site_patterns = self._detect_site_type(url)

        # Playwright for JS-required sites
        if site_patterns['js_required']:
            content = await self._handle_javascript_site(url)
            if content:
                return content

        # Fallback to regular HTTP request
        try:
            content = await self._fetch_page(session, url, urlparse(url).netloc)
            return content
        except Exception as e:
            self.logger.error(f"Both fetch methods failed for {url}: {e}")
            return ""

    def _is_valid_product_url(self, url: str) -> bool:
        site_patterns = self._detect_site_type(url)

        # Check against site-specific patterns
        for pattern in site_patterns['product_patterns']:
            if re.search(pattern, url):
                return True

        return False


    async def _fetch_page(
            self,
            session: aiohttp.ClientSession,
            url: str,
            domain: str
    ) -> str:
        self.stats['requests'] += 1

        try:
            headers = self._get_headers(domain)
            async with session.get(
                    url,
                    headers=headers,
                    timeout=10,
                    allow_redirects=True
            ) as response:
                self.stats['successful_requests'] += 1
                return await response.text()
        except Exception as e:
            self.stats['failed_requests'] += 1
            self.logger.error(f"Error fetching {url}: {e}")
            return ""

    async def _extract_links(self, base_url: str, html_content: str) -> Set[str]:
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()

        for a_tag in soup.find_all('a', href=True):
            link = urljoin(base_url, a_tag['href'])
            parsed_link = urlparse(link)

            if parsed_link.netloc == urlparse(base_url).netloc:
                links.add(link)

        return links

    def _get_headers(self, domain: str) -> Dict[str, str]:
        headers = self.default_headers.copy()

        if self.rotate_user_agents:
            headers['User-Agent'] = self.ua.random

        headers['Referer'] = f'https://{domain}'

        headers.update(self.custom_headers)

        headers['X-Request-Timestamp'] = str(datetime.now().timestamp())

        return headers

    async def crawl_domain(self, domain: str) -> List[str]:
        base_url = f"https://{domain}"
        product_urls = set()
        visited_urls = set()

        connector = aiohttp.TCPConnector(
            limit_per_host=self.concurrent_requests,
            force_close=True
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            async def crawl_page(url: str, depth: int):
                if depth > self.max_depth or url in visited_urls:
                    return

                visited_urls.add(url)

                # rate limiting
                await asyncio.sleep(random.uniform(*self.delay_range))

                try:
                    content = await self._fetch_with_fallback(url, session)

                    if self._is_valid_product_url(url):
                        product_urls.add(url)
                        self.logger.info(f"Found product URL: {url}")

                    # Extract and validate links
                    links = await self._extract_links(url, content)
                    valid_links = self._filter_valid_links(links, domain)

                    tasks = []
                    for link in valid_links:
                        if link not in visited_urls:
                            tasks.append(crawl_page(link, depth + 1))

                    if tasks:
                        await asyncio.gather(*tasks)

                except Exception as e:
                    self.logger.error(f"Error crawling {url}: {e}")

            await crawl_page(base_url, 0)

        return list(product_urls)

    def _normalize_domain(self, domain: str) -> str:
        domain = domain.replace('https://', '').replace('http://', '')
        return domain.rstrip('/')

    def _filter_valid_links(self, links: Set[str], domain: str) -> Set[str]:
        valid_links = set()
        site_patterns = self._detect_site_type(domain)

        for link in links:
            parsed_link = urlparse(link)

            # Skip invalid or non-matching domains
            if parsed_link.netloc != domain:
                continue

            # Skip common trap patterns
            if any(trap in link.lower() for trap in [
                'login', 'signin', 'cart', 'checkout', 'account',
                'wishlist', 'unsubscribe', 'email-preference'
            ]):
                continue

            # Check for pagination patterns
            is_pagination = any(
                re.search(pattern, link)
                for pattern in site_patterns['pagination_patterns']
            )

            if is_pagination or self._is_valid_product_url(link):
                valid_links.add(link)

        return valid_links

    async def discover_product_urls(self) -> Dict[str, List[str]]:
        self.stats['start_time'] = datetime.now()
        results = {}

        async def crawl_with_timeout(domain):
            try:
                product_urls = await asyncio.wait_for(
                    self.crawl_domain(domain),
                    timeout=300  # 5-minute timeout per domain
                )
                results[domain] = product_urls
            except asyncio.TimeoutError:
                self.logger.warning(f"Crawling {domain} timed out")
                results[domain] = []

        await asyncio.gather(
            *[crawl_with_timeout(domain) for domain in self.domains]
        )

        self.stats['end_time'] = datetime.now()
        return results

    def run(self) -> Dict[str, List[str]]:
        return asyncio.run(self.discover_product_urls())

    def print_stats(self):
        if self.stats['start_time'] and self.stats['end_time']:
            duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
            success_rate = (self.stats['successful_requests'] / self.stats['requests'] * 100
                            if self.stats['requests'] > 0 else 0)

            print("\nCrawling Statistics:")
            print(f"Total Requests: {self.stats['requests']}")
            print(f"Successful Requests: {self.stats['successful_requests']}")
            print(f"Failed Requests: {self.stats['failed_requests']}")
            print(f"Success Rate: {success_rate:.2f}%")
            print(f"Total Duration: {duration:.2f} seconds")


def main():
    domains = [
        "target.com",
    ]

    crawler = EnhancedEcommerceCrawler(
        domains=domains,
        max_depth=3,
        concurrent_requests=5,
        use_playwright=True,
        respect_robots=True,
        delay_range=(2, 5)
    )

    results = crawler.run()

    # Save results
    with open('product_urls.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Print statistics
    crawler.print_stats()


if __name__ == "__main__":
    main()