"""Social media scraping for LinkedIn and Twitter hiring posts.

This module provides scrapers for public social media posts that mention hiring
or marketing pain. Designed to respect ToS and only access publicly visible content.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SocialMediaScraper:
    """Base class for social media scrapers."""

    def __init__(
        self,
        timeout: float = 30.0,
        user_agent: str = None
    ):
        self.timeout = timeout
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


class LinkedInPublicScraper(SocialMediaScraper):
    """
    Scraper for publicly visible LinkedIn job posts.

    IMPORTANT: This only works for publicly visible job posts that don't require login.
    LinkedIn actively blocks scrapers, so this should be used sparingly and with respect.
    For production use, consider LinkedIn's official API with proper authentication.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://www.linkedin.com"

    async def search_public_jobs(
        self,
        keywords: List[str],
        location: str = "India",
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for publicly visible job posts on LinkedIn.

        Args:
            keywords: Search keywords (e.g., ["marketing", "hiring"])
            location: Job location
            max_results: Maximum number of results

        Returns:
            List of job post data

        Note: LinkedIn frequently changes their structure and actively blocks scrapers.
        This is intended for educational purposes and light use only.
        """
        logger.warning(
            "LinkedIn public scraping is unreliable and violates LinkedIn ToS for automated access. "
            "Use LinkedIn's official API or manual copy-paste instead."
        )

        jobs = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for keyword in keywords[:3]:  # Limit to avoid rate limiting
                try:
                    # LinkedIn job search URL (public jobs)
                    search_url = f"{self.base_url}/jobs/search/"
                    params = {
                        "keywords": keyword,
                        "location": location,
                        "trk": "public_jobs_jobs-search-bar_search-submit",
                    }

                    headers = {
                        "User-Agent": self.user_agent,
                        "Accept-Language": "en-US,en;q=0.9",
                    }

                    response = await client.get(search_url, params=params, headers=headers, follow_redirects=True)

                    if response.status_code != 200:
                        logger.warning(f"LinkedIn returned status {response.status_code}")
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Try to find job cards (structure may vary)
                    job_cards = soup.find_all('div', class_=re.compile(r'job.*card|base-card'))

                    for card in job_cards[:max_results]:
                        try:
                            # Extract job details (structure varies)
                            title_elem = card.find('h3') or card.find('a', class_=re.compile(r'job.*title'))
                            company_elem = card.find('h4') or card.find('a', class_=re.compile(r'company'))
                            location_elem = card.find('span', class_=re.compile(r'location'))

                            title = title_elem.get_text(strip=True) if title_elem else "Unknown"
                            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
                            location_text = location_elem.get_text(strip=True) if location_elem else ""

                            # Try to get job URL
                            link = card.find('a', href=True)
                            job_url = link['href'] if link else None
                            if job_url and not job_url.startswith('http'):
                                job_url = f"{self.base_url}{job_url}"

                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': location_text,
                                'url': job_url,
                                'source': 'linkedin_public',
                                'text': f"{title} at {company} - {location_text}",
                            })

                        except Exception as e:
                            logger.error(f"Error parsing LinkedIn job card: {e}")

                except Exception as e:
                    logger.error(f"Error searching LinkedIn for '{keyword}': {e}")

        logger.info(f"Found {len(jobs)} public LinkedIn jobs")
        return jobs


class TwitterPublicScraper(SocialMediaScraper):
    """
    Scraper for publicly visible Twitter/X posts mentioning hiring.

    IMPORTANT: Twitter/X has strict API policies. For production use,
    use Twitter API v2 with proper authentication.

    This scraper is for educational purposes only and should be used sparingly.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://twitter.com"

    async def search_hiring_tweets(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for public tweets mentioning hiring or marketing pain.

        Args:
            keywords: Search keywords (e.g., ["hiring marketing", "marketing pain"])
            max_results: Maximum number of results

        Returns:
            List of tweet data

        Note: Twitter/X requires authentication for API access. This method
        will not work reliably without official API access.
        """
        logger.warning(
            "Twitter/X scraping without API is unreliable and violates ToS. "
            "Use Twitter API v2 with proper authentication instead."
        )

        tweets = []

        # Twitter/X now requires authentication for most access
        # This is a placeholder - actual implementation would need Twitter API

        logger.info("Twitter scraping requires official API access. Returning empty results.")

        return tweets


class NitterScraper(SocialMediaScraper):
    """
    Scraper using Nitter (privacy-focused Twitter frontend) as an alternative.

    Nitter instances provide public access to Twitter without authentication.
    However, Nitter instances are often rate-limited or unavailable.
    """

    def __init__(self, nitter_instance: str = "nitter.net", **kwargs):
        super().__init__(**kwargs)
        self.base_url = f"https://{nitter_instance}"

    async def search_hiring_tweets(
        self,
        keywords: List[str],
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search for tweets using Nitter instance.

        Args:
            keywords: Search keywords
            max_results: Maximum number of results

        Returns:
            List of tweet data
        """
        tweets = []

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for keyword in keywords[:3]:
                try:
                    # Nitter search URL
                    search_url = f"{self.base_url}/search"
                    params = {
                        "f": "tweets",
                        "q": keyword,
                    }

                    headers = {
                        "User-Agent": self.user_agent,
                    }

                    response = await client.get(search_url, params=params, headers=headers)

                    if response.status_code != 200:
                        logger.warning(f"Nitter returned status {response.status_code}")
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Find tweet containers
                    tweet_divs = soup.find_all('div', class_='timeline-item')

                    for tweet_div in tweet_divs[:max_results]:
                        try:
                            # Extract tweet text
                            text_elem = tweet_div.find('div', class_='tweet-content')
                            text = text_elem.get_text(strip=True) if text_elem else ""

                            # Extract author
                            author_elem = tweet_div.find('a', class_='fullname')
                            author = author_elem.get_text(strip=True) if author_elem else "Unknown"

                            # Extract tweet URL
                            link_elem = tweet_div.find('a', class_='tweet-link')
                            tweet_url = link_elem['href'] if link_elem else None
                            if tweet_url and not tweet_url.startswith('http'):
                                tweet_url = f"https://twitter.com{tweet_url}"

                            # Extract timestamp
                            time_elem = tweet_div.find('span', class_='tweet-date')
                            timestamp = time_elem.get_text(strip=True) if time_elem else ""

                            tweets.append({
                                'text': text,
                                'author': author,
                                'url': tweet_url,
                                'timestamp': timestamp,
                                'source': 'nitter',
                            })

                        except Exception as e:
                            logger.error(f"Error parsing Nitter tweet: {e}")

                except Exception as e:
                    logger.error(f"Error searching Nitter for '{keyword}': {e}")

        logger.info(f"Found {len(tweets)} tweets via Nitter")
        return tweets


# ============================================================================
# Helper Functions
# ============================================================================

def filter_hiring_posts(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter posts to only include those likely related to hiring or marketing pain.

    Args:
        posts: List of social media post dictionaries

    Returns:
        Filtered list of posts
    """
    hiring_keywords = [
        r'\bhiring\b', r'\brecruiting\b', r'\bjob\s+opening\b', r'\bwe\'re\s+looking\s+for\b',
        r'\bjoin\s+our\s+team\b', r'\bmarketing\s+manager\b', r'\bmarketing\s+lead\b',
        r'\bgrowth\s+hacker\b', r'\bdigital\s+marketing\b', r'\bopen\s+position\b',
    ]

    filtered = []

    for post in posts:
        text = post.get('text', '').lower()

        # Check if post matches hiring keywords
        for keyword_pattern in hiring_keywords:
            if re.search(keyword_pattern, text, re.IGNORECASE):
                filtered.append(post)
                break

    return filtered


def social_post_to_signal_text(post: Dict[str, Any]) -> str:
    """
    Convert a social media post to signal text for classification.

    Args:
        post: Social media post dictionary

    Returns:
        Signal text string
    """
    parts = []

    if post.get('source'):
        parts.append(f"Source: {post['source']}")

    if post.get('company'):
        parts.append(f"Company: {post['company']}")

    if post.get('author'):
        parts.append(f"Author: {post['author']}")

    if post.get('title'):
        parts.append(f"Title: {post['title']}")

    if post.get('timestamp'):
        parts.append(f"Posted: {post['timestamp']}")

    if post.get('text'):
        parts.append(f"\n{post['text']}")

    if post.get('url'):
        parts.append(f"\nURL: {post['url']}")

    return '\n'.join(parts)
