import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
from typing import List, Dict, Set
import json
import logging
from concurrent.futures import ThreadPoolExecutor


class EcommerceCrawler:
    def __init__(self, domains: List[str], max_depth: int = 3, concurrent_requests: int = 10):
        self.domains = [self._normalize_domain(domain) for domain in domains]
        self.max_depth = max_depth
        self.concurrent_requests = concurrent_requests
        self.product_url_patterns = [
            r'/product/',
            r'/item/',
            r'/p/',
            r'/products?/',
            r'/shop/',
            r'\d{4,8}'  # Potential product ID pattern
        ]

        # Configure logging
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s: %(message)s')
        self.logger = logging.getLogger(__name__)

    def _normalize_domain(self, domain: str) -> str:
        domain = domain.replace('https://', '').replace('http://', '')
        return domain.rstrip('/')

    def _is_potential_product_url(self, url: str) -> bool:
        url = url.lower()
        return any(re.search(pattern, url) for pattern in self.product_url_patterns)

    async def _fetch_page(self, session: aiohttp.ClientSession, url: str) -> str:
        try:
            async with session.get(url, timeout=10) as response:
                print(response.status, response.text)
                return await response.text()
        except Exception as e:
            self.logger.error(f"Error fetching {url}: {e}")
            return ""

    async def _extract_links(self, base_url: str, html_content: str) -> Set[str]:
        soup = BeautifulSoup(html_content, 'html.parser')
        links = set()

        for a_tag in soup.find_all('a', href=True):
            link = urljoin(base_url, a_tag['href'])
            parsed_link = urlparse(link)

            # Filter links from same domain
            if parsed_link.netloc == urlparse(base_url).netloc:
                links.add(link)

        return links

    async def crawl_domain(self, domain: str) -> List[str]:
        base_url = f"https://{domain}"
        product_urls = set()
        visited_urls = set()

        async with aiohttp.ClientSession() as session:
            async def crawl_page(url: str, depth: int):
                if depth > self.max_depth or url in visited_urls:
                    return

                visited_urls.add(url)

                try:
                    html_content = await self._fetch_page(session, url)

                    if self._is_potential_product_url(url):
                        product_urls.add(url)

                    links = await self._extract_links(url, html_content)

                    tasks = [
                        crawl_page(link, depth + 1)
                        for link in links
                        if self._is_potential_product_url(link)
                    ]
                    await asyncio.gather(*tasks)

                except Exception as e:
                    self.logger.error(f"Error crawling {url}: {e}")

            # Start crawling from base URL
            await crawl_page(base_url, 0)

        return list(product_urls)

    async def discover_product_urls(self) -> Dict[str, List[str]]:
        results = {}

        async def crawl_with_timeout(domain):
            try:
                product_urls = await asyncio.wait_for(
                    self.crawl_domain(domain),
                    timeout=300  # Change timeout as needed
                )
                results[domain] = product_urls
            except asyncio.TimeoutError:
                self.logger.warning(f"Crawling {domain} timed out")

        await asyncio.gather(
            *[crawl_with_timeout(domain) for domain in self.domains]
        )

        return results

    def run(self) -> Dict[str, List[str]]:
        return asyncio.run(self.discover_product_urls())


def main():
    # domains = ["amazon.in","amazon.com","albertsons.com", "ebay.com", "target.com"]
    domains = ["argos.co.uk"]
    crawler = EcommerceCrawler(domains)
    results = crawler.run()
 
    # Save results to JSON
    with open('product_urls.json', 'w') as f:
        json.dump(results, f, indent=2)

    # Print summary
    for domain, urls in results.items():
        print(f"{domain}: {len(urls)} product URLs discovered")


if __name__ == "__main__":
    main()