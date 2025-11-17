"""
Company website scraper for extracting contact info and career pages
"""
import logging
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urljoin, urlparse
import re

from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class CompanyScraper(BaseScraper):
    """Scraper for company websites to extract contact info and career pages"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.career_keywords = [
            'career', 'careers', 'jobs', 'job', 'openings', 'opportunities',
            'join-us', 'joinus', 'work-with-us', 'hiring', 'talent', 'apply'
        ]
        self.contact_keywords = [
            'contact', 'about', 'team', 'company', 'connect', 'reach'
        ]

    def scrape_company(self, url: str, deep_scan: bool = False) -> Dict[str, Any]:
        """
        Scrape company website for contact info and job postings

        Args:
            url: Company website URL
            deep_scan: If True, crawl multiple pages (slower)

        Returns:
            Dictionary with company information
        """
        company_data = {
            'url': url,
            'domain': self._get_domain(url),
            'name': None,
            'description': None,
            'emails': [],
            'phones': [],
            'social_links': {},
            'career_page_url': None,
            'contact_page_url': None,
            'has_jobs': False,
            'job_signals': [],
            'technologies': [],
            'company_size_hints': []
        }

        try:
            # Fetch homepage
            response = self.fetch(url)
            if not response:
                logger.warning(f"Could not fetch {url}")
                return company_data

            soup = self.parse_html(response.text)

            # Extract basic company info
            basic_info = self.extract_company_info(soup, url)
            company_data.update(basic_info)

            # Get company name
            company_data['name'] = self._extract_company_name(soup, url)

            # Find career and contact page URLs
            links = self._extract_important_links(soup, url)
            company_data['career_page_url'] = links.get('career')
            company_data['contact_page_url'] = links.get('contact')

            # Check for hiring signals on homepage
            company_data['job_signals'] = self._find_hiring_signals(soup)
            company_data['has_jobs'] = len(company_data['job_signals']) > 0

            # Extract technologies mentioned
            company_data['technologies'] = self._extract_technologies(soup)

            # Extract company size hints
            company_data['company_size_hints'] = self._extract_size_hints(soup)

            # If deep scan, visit career and contact pages
            if deep_scan:
                if company_data['career_page_url']:
                    career_data = self._scrape_career_page(company_data['career_page_url'])
                    company_data['emails'].extend(career_data.get('emails', []))
                    company_data['phones'].extend(career_data.get('phones', []))
                    company_data['job_signals'].extend(career_data.get('job_signals', []))
                    company_data['has_jobs'] = company_data['has_jobs'] or len(career_data.get('job_signals', [])) > 0

                if company_data['contact_page_url']:
                    contact_data = self._scrape_contact_page(company_data['contact_page_url'])
                    company_data['emails'].extend(contact_data.get('emails', []))
                    company_data['phones'].extend(contact_data.get('phones', []))

            # Deduplicate lists
            company_data['emails'] = list(set(company_data['emails']))
            company_data['phones'] = list(set(company_data['phones']))
            company_data['job_signals'] = list(set(company_data['job_signals']))
            company_data['technologies'] = list(set(company_data['technologies']))

            logger.info(f"Scraped company: {company_data['name']} - Found {len(company_data['emails'])} emails, {len(company_data['job_signals'])} job signals")

        except Exception as e:
            logger.error(f"Error scraping company {url}: {e}")

        return company_data

    def _extract_company_name(self, soup, url: str) -> Optional[str]:
        """Extract company name from page"""
        # Try meta tags
        og_site = soup.find('meta', property='og:site_name')
        if og_site and og_site.get('content'):
            return self.clean_text(og_site['content'])

        # Try title tag
        title = soup.find('title')
        if title:
            title_text = self.clean_text(title.get_text())
            # Remove common suffixes
            for suffix in [' - Home', ' | Home', ' - Official Site', ' | Official', ' - Welcome']:
                title_text = title_text.replace(suffix, '')
            return title_text

        # Try to extract from domain
        domain = urlparse(url).netloc
        domain = domain.replace('www.', '').split('.')[0]
        return domain.capitalize()

    def _extract_important_links(self, soup, base_url: str) -> Dict[str, str]:
        """Extract career and contact page URLs"""
        links = {
            'career': None,
            'contact': None
        }

        all_links = soup.find_all('a', href=True)

        for link in all_links:
            href = link['href'].lower()
            text = link.get_text().lower()

            # Make absolute URL
            full_url = urljoin(base_url, link['href'])

            # Check for career page
            if not links['career']:
                for keyword in self.career_keywords:
                    if keyword in href or keyword in text:
                        links['career'] = full_url
                        break

            # Check for contact page
            if not links['contact']:
                for keyword in self.contact_keywords:
                    if keyword in href or keyword in text:
                        links['contact'] = full_url
                        break

            if links['career'] and links['contact']:
                break

        return links

    def _find_hiring_signals(self, soup) -> List[str]:
        """Find hiring/job-related signals on page"""
        signals = []
        page_text = soup.get_text().lower()

        # Hiring keywords
        hiring_patterns = [
            r"we['\u2019]re hiring",
            r"we are hiring",
            r"join our team",
            r"careers",
            r"job opening",
            r"positions? available",
            r"apply now",
            r"looking for",
            r"seeking",
            r"hiring for",
            r"recruitment",
            r"grow our team",
            r"expanding team"
        ]

        for pattern in hiring_patterns:
            matches = re.finditer(pattern, page_text, re.IGNORECASE)
            for match in matches:
                # Get context around match (50 chars before and after)
                start = max(0, match.start() - 50)
                end = min(len(page_text), match.end() + 100)
                context = page_text[start:end].strip()
                if context:
                    signals.append(self.clean_text(context))

        # Look for job titles in headings
        job_title_patterns = [
            r'\b(hiring|seeking|looking for).{0,20}(manager|developer|engineer|designer|marketer|analyst|lead)',
            r'\b(manager|developer|engineer|designer|marketer|analyst|lead).{0,20}(wanted|needed|required)',
        ]

        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'strong'])
        for heading in headings:
            heading_text = heading.get_text().lower()
            for pattern in job_title_patterns:
                if re.search(pattern, heading_text, re.IGNORECASE):
                    signals.append(self.clean_text(heading.get_text()))

        return signals[:10]  # Limit to 10 most relevant signals

    def _extract_technologies(self, soup) -> List[str]:
        """Extract technologies/tools mentioned on website"""
        page_text = soup.get_text().lower()

        tech_keywords = [
            # Programming languages
            'python', 'javascript', 'java', 'ruby', 'php', 'go', 'golang', 'rust',
            'typescript', 'kotlin', 'swift', 'c++', 'c#', 'scala',
            # Frameworks
            'react', 'angular', 'vue', 'django', 'flask', 'rails', 'laravel',
            'node.js', 'express', 'spring', 'fastapi',
            # Databases
            'mongodb', 'postgresql', 'mysql', 'redis', 'elasticsearch',
            # Cloud/DevOps
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
            'terraform', 'jenkins', 'gitlab', 'github',
            # Marketing tools
            'hubspot', 'salesforce', 'marketo', 'mailchimp', 'google analytics',
            'facebook ads', 'google ads', 'shopify', 'wordpress'
        ]

        found_tech = []
        for tech in tech_keywords:
            if tech in page_text:
                found_tech.append(tech)

        return found_tech

    def _extract_size_hints(self, soup) -> List[str]:
        """Extract hints about company size"""
        page_text = soup.get_text().lower()
        hints = []

        size_patterns = [
            (r'(\d+)\+?\s*(employees?|people|team members?)', 'employees'),
            (r'team of (\d+)', 'team_size'),
            (r'(\d+)\s*person (company|team|startup)', 'team_size'),
            (r'(solo|one person|founder|solopreneur)', 'solo'),
            (r'(small team|small company|startup)', 'small'),
            (r'(growing team|scaling|expanding)', 'growing'),
        ]

        for pattern, hint_type in size_patterns:
            matches = re.finditer(pattern, page_text, re.IGNORECASE)
            for match in matches:
                hints.append(match.group(0))

        return hints[:5]

    def _scrape_career_page(self, url: str) -> Dict[str, Any]:
        """Scrape career/jobs page for detailed information"""
        data = {
            'emails': [],
            'phones': [],
            'job_signals': []
        }

        try:
            response = self.fetch(url)
            if not response:
                return data

            soup = self.parse_html(response.text)

            # Extract contact info
            page_text = soup.get_text()
            data['emails'] = self.extract_emails(page_text)
            data['phones'] = self.extract_phones(page_text)

            # Find job postings/signals
            data['job_signals'] = self._find_hiring_signals(soup)

            # Look for job titles
            job_title_elements = soup.find_all(['h2', 'h3', 'h4', 'strong', 'b'])
            for elem in job_title_elements:
                text = self.clean_text(elem.get_text())
                # Check if looks like a job title
                if 5 < len(text) < 100:  # Reasonable length
                    job_keywords = ['manager', 'developer', 'engineer', 'designer', 'analyst',
                                  'specialist', 'coordinator', 'director', 'lead', 'head']
                    if any(keyword in text.lower() for keyword in job_keywords):
                        data['job_signals'].append(text)

        except Exception as e:
            logger.error(f"Error scraping career page {url}: {e}")

        return data

    def _scrape_contact_page(self, url: str) -> Dict[str, Any]:
        """Scrape contact/about page for contact information"""
        data = {
            'emails': [],
            'phones': []
        }

        try:
            response = self.fetch(url)
            if not response:
                return data

            soup = self.parse_html(response.text)
            page_text = soup.get_text()

            data['emails'] = self.extract_emails(page_text)
            data['phones'] = self.extract_phones(page_text)

        except Exception as e:
            logger.error(f"Error scraping contact page {url}: {e}")

        return data


class LeadDiscoveryScraper(BaseScraper):
    """
    Scraper for discovering new leads via search engines
    """

    def search_for_leads(self, query: str, num_results: int = 20) -> List[Dict[str, Any]]:
        """
        Search for potential leads using Google/Bing

        Args:
            query: Search query (e.g., "D2C ecommerce India hiring marketing")
            num_results: Number of results to return

        Returns:
            List of potential lead URLs and snippets
        """
        leads = []

        # Try DuckDuckGo (easier to scrape than Google)
        try:
            leads = self._search_duckduckgo(query, num_results)
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")

        return leads

    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict[str, Any]]:
        """Search DuckDuckGo (less restrictive than Google)"""
        results = []

        try:
            from urllib.parse import quote_plus
            search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

            response = self.fetch(search_url)
            if not response:
                return results

            soup = self.parse_html(response.text)

            # DuckDuckGo HTML results
            result_divs = soup.find_all('div', class_='result')

            for div in result_divs[:num_results]:
                try:
                    result = {
                        'title': None,
                        'url': None,
                        'snippet': None,
                        'source': 'duckduckgo'
                    }

                    # Title and URL
                    title_link = div.find('a', class_='result__a')
                    if title_link:
                        result['title'] = self.clean_text(title_link.get_text())
                        result['url'] = title_link.get('href')

                    # Snippet
                    snippet_elem = div.find('a', class_='result__snippet')
                    if snippet_elem:
                        result['snippet'] = self.clean_text(snippet_elem.get_text())

                    if result['title'] and result['url']:
                        results.append(result)

                except Exception as e:
                    logger.error(f"Error parsing search result: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {e}")

        return results
