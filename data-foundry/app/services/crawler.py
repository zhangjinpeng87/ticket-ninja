from dataclasses import dataclass
from typing import List, Optional, Set, Tuple
from collections import deque
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


@dataclass
class CrawledPage:
    url: str
    html: str
    title: str
    depth: int


class WebCrawler:
    """Simple breadth-first crawler tailored for technical documentation sites."""

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "TicketNinjaDataFoundry/0.1 (+https://github.com/)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    async def crawl(
        self,
        root_url: str,
        max_depth: int,
        max_pages: int,
        allowed_domains: Optional[List[str]] = None,
        include_subdomains: bool = True,
        skip_assets: bool = True,
    ) -> Tuple[List[CrawledPage], List[str]]:
        visited: Set[str] = set()
        errors: List[str] = []
        pages: List[CrawledPage] = []

        parsed_root = urlparse(root_url)
        base_domain = parsed_root.netloc

        normalized_allowed = set(allowed_domains or [base_domain])

        queue = deque([(root_url, 0)])

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True, headers=self.headers) as client:
            while queue and len(pages) < max_pages:
                url, depth = queue.popleft()
                if url in visited or depth > max_depth:
                    continue
                visited.add(url)

                if not self._is_allowed(url, normalized_allowed, include_subdomains):
                    continue

                try:
                    response = await client.get(url)
                except Exception as exc:
                    errors.append(f"Failed to fetch {url}: {exc}")
                    continue

                if response.status_code >= 400:
                    errors.append(f"{url} returned {response.status_code}")
                    continue

                content_type = response.headers.get("content-type", "")
                if skip_assets and "html" not in content_type and "xml" not in content_type:
                    continue

                html = response.text
                soup = BeautifulSoup(html, "lxml")
                title = (soup.title.string.strip() if soup.title and soup.title.string else url)

                pages.append(CrawledPage(url=url, html=html, title=title, depth=depth))

                if depth < max_depth:
                    for link in self._extract_links(soup, url):
                        if link not in visited and self._is_allowed(link, normalized_allowed, include_subdomains):
                            queue.append((link, depth + 1))

                if len(pages) >= max_pages:
                    break

        return pages, errors

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        links = []
        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href")
            if not href:
                continue
            if href.startswith("#") or href.startswith("mailto:") or href.startswith("javascript:"):
                continue
            absolute = urljoin(base_url, href)
            links.append(absolute.split("#")[0])
        return links

    def _is_allowed(self, url: str, allowed_domains: Set[str], include_subdomains: bool) -> bool:
        parsed = urlparse(url)
        hostname = parsed.netloc
        if not hostname:
            return False
        hostname = hostname.lower()

        if include_subdomains:
            return any(hostname == domain or hostname.endswith(f".{domain}") for domain in allowed_domains)
        return hostname in allowed_domains

