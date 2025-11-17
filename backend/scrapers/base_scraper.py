"""
Base scraper with rate limiting, retries, and error handling
"""
import time
import random
import logging
import urllib.robotparser
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urljoin
import re

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for all scrapers with common functionality"""

    def __init__(self, rate_limit: float = 2.0, respect_robots: bool = True):
        """
        Initialize base scraper

        Args:
            rate_limit: Minimum seconds between requests (default 2.0)
            respect_robots: Whether to check robots.txt (default True)
        """
        self.rate_limit = rate_limit
        self.respect_robots = respect_robots
        self.last_request_time = {}  # Track per-domain
        self.ua = UserAgent()
        self.robots_parsers = {}  # Cache robots.txt parsers
        self.session = requests.Session()

    def get_user_agent(self) -> str:
        """Get a random user agent"""
        try:
            return self.ua.random
        except:
            # Fallback user agents
            fallbacks = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ]
            return random.choice(fallbacks)

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self.respect_robots:
            return True

        try:
            domain = self._get_domain(url)

            # Get or create robots parser for this domain
            if domain not in self.robots_parsers:
                rp = urllib.robotparser.RobotFileParser()
                robots_url = urljoin(domain, '/robots.txt')
                rp.set_url(robots_url)
                try:
                    rp.read()
                    self.robots_parsers[domain] = rp
                except:
                    # If can't read robots.txt, allow by default
                    logger.warning(f"Could not read robots.txt for {domain}")
                    self.robots_parsers[domain] = None

            rp = self.robots_parsers[domain]
            if rp is None:
                return True

            return rp.can_fetch(self.get_user_agent(), url)
        except Exception as e:
            logger.warning(f"Error checking robots.txt: {e}")
            return True

    def _wait_for_rate_limit(self, url: str):
        """Wait if needed to respect rate limiting"""
        domain = self._get_domain(url)

        if domain in self.last_request_time:
            elapsed = time.time() - self.last_request_time[domain]
            if elapsed < self.rate_limit:
                sleep_time = self.rate_limit - elapsed + random.uniform(0, 0.5)
                time.sleep(sleep_time)

        self.last_request_time[domain] = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.RequestException, ConnectionError))
    )
    def fetch(self, url: str, headers: Optional[Dict] = None, **kwargs) -> Optional[requests.Response]:
        """
        Fetch URL with rate limiting and retries

        Args:
            url: URL to fetch
            headers: Optional headers dict
            **kwargs: Additional arguments for requests.get()

        Returns:
            Response object or None if failed
        """
        # Check robots.txt
        if not self._can_fetch(url):
            logger.warning(f"Blocked by robots.txt: {url}")
            return None

        # Rate limiting
        self._wait_for_rate_limit(url)

        # Prepare headers
        if headers is None:
            headers = {}
        if 'User-Agent' not in headers:
            headers['User-Agent'] = self.get_user_agent()

        # Fetch
        try:
            response = self.session.get(url, headers=headers, timeout=30, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            raise

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML content"""
        return BeautifulSoup(html, 'lxml')

    def extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        # Filter out common garbage emails
        filtered = []
        garbage_patterns = [
            r'example\.com$',
            r'test\.com$',
            r'sample\.com$',
            r'placeholder',
            r'noreply',
            r'no-reply'
        ]
        for email in emails:
            if not any(re.search(pattern, email, re.IGNORECASE) for pattern in garbage_patterns):
                filtered.append(email.lower())
        return list(set(filtered))

    def extract_phones(self, text: str) -> List[str]:
        """Extract phone numbers from text"""
        # Indian phone patterns
        patterns = [
            r'\+91[-\s]?\d{10}',  # +91 format
            r'\d{10}',  # 10 digit
            r'\(\d{3}\)[-\s]?\d{3}[-\s]?\d{4}',  # (123) 456-7890
            r'\d{3}[-\s]?\d{3}[-\s]?\d{4}',  # 123-456-7890
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))

    def extract_social_links(self, soup: BeautifulSoup, base_url: str) -> Dict[str, str]:
        """Extract social media links from page"""
        social = {}
        social_patterns = {
            'linkedin': r'linkedin\.com',
            'twitter': r'twitter\.com|x\.com',
            'facebook': r'facebook\.com',
            'instagram': r'instagram\.com',
            'youtube': r'youtube\.com'
        }

        for link in soup.find_all('a', href=True):
            href = link['href']
            for platform, pattern in social_patterns.items():
                if re.search(pattern, href, re.IGNORECASE):
                    social[platform] = href
                    break

        return social

    def clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s\.,!?;:()\-\'\"@]', '', text)
        return text.strip()

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def extract_company_info(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract basic company information from page"""
        info = {
            'url': url,
            'title': None,
            'description': None,
            'emails': [],
            'phones': [],
            'social_links': {}
        }

        # Title
        title_tag = soup.find('title')
        if title_tag:
            info['title'] = self.clean_text(title_tag.get_text())

        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            info['description'] = self.clean_text(meta_desc['content'])

        # Extract contact info from full page text
        page_text = soup.get_text()
        info['emails'] = self.extract_emails(page_text)
        info['phones'] = self.extract_phones(page_text)

        # Social links
        info['social_links'] = self.extract_social_links(soup, url)

        return info
