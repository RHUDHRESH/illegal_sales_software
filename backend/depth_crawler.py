"""Depth-limited website crawler for extracting text from multiple pages.

This crawler implements depth-limited crawling (default 5 pages) to extract
text from /about, /careers, /jobs, /blog pages for a given domain.
"""

import logging
import re
from typing import List, Dict, Any, Set, Optional
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


class DepthLimitedCrawler:
    """
    Depth-limited crawler that extracts text from multiple pages of a website.
    """

    def __init__(
        self,
        max_pages: int = 5,
        max_depth: int = 2,
        rate_limit_seconds: float = 2.0,
        timeout: float = 30.0,
        user_agent: str = None
    ):
        """
        Initialize the crawler.

        Args:
            max_pages: Maximum number of pages to crawl (default: 5)
            max_depth: Maximum depth to crawl from start URL (default: 2)
            rate_limit_seconds: Seconds to wait between requests (default: 2.0)
            timeout: Request timeout in seconds (default: 30.0)
            user_agent: Custom user agent string
        """
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.rate_limit_seconds = rate_limit_seconds
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (compatible; LeadBot/1.0)"

        # Target page patterns (prioritize these)
        self.priority_patterns = [
            r'/(about|careers?|jobs?|blog|team|company|hiring|openings)',
            r'/(contact|reach|connect)',
        ]

        # Patterns to avoid
        self.exclude_patterns = [
            r'\.(pdf|jpg|jpeg|png|gif|svg|css|js|zip|exe|dmg)$',
            r'/(login|signin|signup|register|logout|admin|dashboard|account)',
            r'/(privacy|terms|legal|cookie)',
            r'/#',  # Anchor links
        ]

    def crawl(self, start_url: str) -> Dict[str, Any]:
        """
        Crawl a website starting from the given URL.

        Args:
            start_url: Starting URL to crawl

        Returns:
            Dictionary with crawled data:
            {
                'start_url': str,
                'pages_crawled': int,
                'pages': [
                    {
                        'url': str,
                        'title': str,
                        'text': str,
                        'emails': List[str],
                        'phones': List[str],
                    }
                ],
                'all_text': str,  # Combined text from all pages
                'all_emails': List[str],
                'all_phones': List[str],
            }
        """
        domain = self._get_domain(start_url)
        visited: Set[str] = set()
        to_visit: List[tuple] = [(start_url, 0)]  # (url, depth)
        crawled_pages = []

        logger.info(f"Starting crawl of {domain} (max {self.max_pages} pages, max depth {self.max_depth})")

        while to_visit and len(crawled_pages) < self.max_pages:
            url, depth = to_visit.pop(0)

            # Skip if already visited or max depth exceeded
            if url in visited or depth > self.max_depth:
                continue

            # Skip excluded patterns
            if self._should_exclude(url):
                continue

            # Mark as visited
            visited.add(url)

            # Fetch and parse page
            try:
                page_data = self._fetch_and_parse_page(url)
                if page_data:
                    crawled_pages.append(page_data)
                    logger.info(f"Crawled [{len(crawled_pages)}/{self.max_pages}]: {url}")

                    # Extract links for further crawling (if not at max depth)
                    if depth < self.max_depth and len(crawled_pages) < self.max_pages:
                        new_links = self._extract_links(page_data['soup'], url, domain)

                        # Prioritize links matching priority patterns
                        priority_links = []
                        other_links = []

                        for link in new_links:
                            if link not in visited:
                                if self._is_priority_link(link):
                                    priority_links.append((link, depth + 1))
                                else:
                                    other_links.append((link, depth + 1))

                        # Add priority links first
                        to_visit = priority_links + to_visit + other_links

                    # Rate limiting
                    time.sleep(self.rate_limit_seconds)

            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")

        # Aggregate results
        all_text_parts = []
        all_emails = set()
        all_phones = set()

        for page in crawled_pages:
            all_text_parts.append(f"=== {page['title']} ({page['url']}) ===\n{page['text']}")
            all_emails.update(page['emails'])
            all_phones.update(page['phones'])

        result = {
            'start_url': start_url,
            'domain': domain,
            'pages_crawled': len(crawled_pages),
            'pages': [
                {
                    'url': p['url'],
                    'title': p['title'],
                    'text': p['text'],
                    'emails': p['emails'],
                    'phones': p['phones'],
                }
                for p in crawled_pages
            ],
            'all_text': '\n\n'.join(all_text_parts),
            'all_emails': list(all_emails),
            'all_phones': list(all_phones),
        }

        logger.info(f"Crawl complete. Visited {len(crawled_pages)} pages, found {len(all_emails)} emails, {len(all_phones)} phones")

        return result

    def _fetch_and_parse_page(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and parse a single page.
        """
        try:
            headers = {
                'User-Agent': self.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }

            response = httpx.get(url, headers=headers, timeout=self.timeout, follow_redirects=True)

            if response.status_code != 200:
                logger.warning(f"Non-200 status for {url}: {response.status_code}")
                return None

            soup = BeautifulSoup(response.text, 'html.parser')

            # Remove script and style elements
            for script in soup(['script', 'style', 'nav', 'footer', 'header']):
                script.decompose()

            # Extract title
            title = soup.find('title')
            title_text = title.get_text(strip=True) if title else url

            # Extract main text
            # Try to find main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main'))

            if main_content:
                text = main_content.get_text(separator=' ', strip=True)
            else:
                text = soup.get_text(separator=' ', strip=True)

            # Clean up text
            text = re.sub(r'\s+', ' ', text).strip()

            # Extract emails and phones
            emails = self._extract_emails(text)
            phones = self._extract_phones(text)

            return {
                'url': url,
                'title': title_text,
                'text': text,
                'emails': emails,
                'phones': phones,
                'soup': soup,  # Keep soup for link extraction
            }

        except Exception as e:
            logger.error(f"Error fetching page {url}: {e}")
            return None

    def _extract_links(self, soup: BeautifulSoup, current_url: str, domain: str) -> List[str]:
        """
        Extract all links from a page, filtering to same domain.
        """
        links = []

        for anchor in soup.find_all('a', href=True):
            href = anchor['href']

            # Convert relative URLs to absolute
            absolute_url = urljoin(current_url, href)

            # Only include links from the same domain
            if self._get_domain(absolute_url) == domain:
                # Remove fragments
                absolute_url = absolute_url.split('#')[0]

                links.append(absolute_url)

        return list(set(links))  # Deduplicate

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()

    def _should_exclude(self, url: str) -> bool:
        """Check if URL matches exclusion patterns."""
        for pattern in self.exclude_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _is_priority_link(self, url: str) -> bool:
        """Check if URL matches priority patterns."""
        for pattern in self.priority_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False

    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))

    def _extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text."""
        phone_patterns = [
            r'\+91[-.\s]?\d{10}',
            r'91[-.\s]?\d{10}',
            r'\b\d{10}\b',
            r'[6-9]\d{9}',
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))


def summarize_crawled_text(crawled_data: Dict[str, Any], max_length: int = 5000) -> str:
    """
    Summarize crawled text for classification.

    Args:
        crawled_data: Result from DepthLimitedCrawler.crawl()
        max_length: Maximum length of summary text

    Returns:
        Summarized text
    """
    summary_parts = []

    # Add domain info
    summary_parts.append(f"Website: {crawled_data['domain']}")
    summary_parts.append(f"Pages analyzed: {crawled_data['pages_crawled']}")

    # Add key page summaries
    for page in crawled_data['pages']:
        # Take first 500 chars from each page
        page_summary = page['text'][:500]
        summary_parts.append(f"\n--- {page['title']} ---\n{page_summary}")

    # Add contact info if found
    if crawled_data['all_emails']:
        summary_parts.append(f"\nEmails found: {', '.join(crawled_data['all_emails'][:5])}")

    if crawled_data['all_phones']:
        summary_parts.append(f"\nPhones found: {', '.join(crawled_data['all_phones'][:5])}")

    summary = '\n'.join(summary_parts)

    # Truncate if too long
    if len(summary) > max_length:
        summary = summary[:max_length] + "..."

    return summary
