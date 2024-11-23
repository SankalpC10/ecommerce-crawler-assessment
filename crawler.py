import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Set
import json
import logging
import random
from fake_useragent import UserAgent
from datetime import datetime


class EcommerceCrawler:
    def __init__(
            self,
            domains: List[str],
            max_depth: int = 3,
            concurrent_requests: int = 10,
            custom_headers: Dict[str, str] = None,
            rotate_user_agents: bool = True
    ):
        self.domains = [self._normalize_domain(domain) for domain in domains]
        self.max_depth = max_depth
        self.concurrent_requests = concurrent_requests
        self.custom_headers = custom_headers or {}
        self.rotate_user_agents = rotate_user_agents

        self.ua = UserAgent() # User-Agent rotator

        self.default_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

        self.product_url_patterns = [
            r'/product/',
            r'/item/',
            r'/p/',
            r'/products?/',
            r'/shop/',
            r'\d{4,8}'
        ]

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

        self.stats = {
            'requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'start_time': None,
            'end_time': None
        }

    def _get_headers(self, domain: str) -> Dict[str, str]:
        headers = self.default_headers.copy()

        if self.rotate_user_agents:
            headers['User-Agent'] = self.ua.random

        headers['Referer'] = f'https://{domain}'

        headers.update(self.custom_headers)

        headers['X-Request-Timestamp'] = str(datetime.now().timestamp())

        return headers

    def _normalize_domain(self, domain: str) -> str:
        domain = domain.replace('https://', '').replace('http://', '')
        return domain.rstrip('/')

    def _is_potential_product_url(self, url: str) -> bool:
        url = url.lower()
        return any(re.search(pattern, url) for pattern in self.product_url_patterns)

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

    async def crawl_domain(self, domain: str) -> List[str]:
        base_url = f"https://{domain}"
        product_urls = set()
        visited_urls = set()

        # Configure client session with TCP connector settings
        connector = aiohttp.TCPConnector(
            limit_per_host=self.concurrent_requests,
            force_close=True
        )

        async with aiohttp.ClientSession(connector=connector) as session:
            async def crawl_page(url: str, depth: int):
                if depth > self.max_depth or url in visited_urls:
                    return

                visited_urls.add(url)

                try:
                    html_content = await self._fetch_page(session, url, domain)

                    if self._is_potential_product_url(url):
                        product_urls.add(url)
                        self.logger.info(f"Found product URL: {url}")

                    links = await self._extract_links(url, html_content)

                    tasks = []
                    for link in links:
                        if self._is_potential_product_url(link) and link not in visited_urls:
                            tasks.append(crawl_page(link, depth + 1))

                    if tasks:
                        await asyncio.gather(*tasks)

                except Exception as e:
                    self.logger.error(f"Error crawling {url}: {e}")

            await crawl_page(base_url, 0)

        return list(product_urls)

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
        "amazon.in",
        "amazon.com",
        "albertsons.com",
        "argos.co.uk",
        "lowes.com",
        "ebay.com",
        "hm.com",
        "etsy.com",
        "samsclub.com",
        "target.com"
    ]


    # Custom headers
    # custom_headers = {
    #     'X-Custom-Header': 'Useragent',
    #     'Authorization': 'x-cc-auth-token'  # If needed
    # }

    crawler = EcommerceCrawler(
        domains=domains,
        max_depth=3,
        concurrent_requests=10,
        # custom_headers=custom_headers,
        rotate_user_agents=True
    )

    results = crawler.run()

    with open('product_urls.json', 'w') as f:
        json.dump(results, f, indent=2)

    crawler.print_stats()

    # Print summary
    for domain, urls in results.items():
        print(f"\n{domain}: {len(urls)} product URLs discovered")


if __name__ == "__main__":
    main()