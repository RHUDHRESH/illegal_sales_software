"""
Company Enrichment - Gather comprehensive company intelligence
"""
import logging
import re
import requests
from typing import Dict, Any, Optional, List
from bs4 import BeautifulSoup
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class CompanyEnrichment:
    """
    Enrich company data with intelligence from multiple sources
    """

    def __init__(self):
        self.cache = {}

    def enrich_company(
        self,
        company_name: str,
        website: Optional[str] = None,
        deep: bool = False
    ) -> Dict[str, Any]:
        """
        Enrich company with comprehensive data

        Args:
            company_name: Company name
            website: Company website URL
            deep: If True, performs deep enrichment (slower)

        Returns:
            Enriched company data dictionary
        """
        enrichment = {
            "company_name": company_name,
            "website": website,
            "enriched_at": datetime.now().isoformat(),
            "data_sources": [],

            # Basic info
            "description": None,
            "tagline": None,
            "founded_year": None,
            "headquarters": None,
            "industry": None,
            "company_type": None,  # Startup, SMB, Enterprise

            # Size & Scale
            "employee_count": None,
            "employee_range": None,
            "estimated_revenue": None,
            "revenue_range": None,

            # Funding & Financial
            "funding_total": None,
            "funding_stage": None,  # Seed, Series A, B, C, etc.
            "last_funding_date": None,
            "last_funding_amount": None,
            "investors": [],
            "valuation": None,

            # Tech Stack
            "technologies": [],
            "tech_categories": [],

            # Social & Web Presence
            "social_profiles": {},
            "blog_url": None,
            "careers_url": None,

            # Growth Signals
            "hiring_velocity": None,  # Job postings rate
            "growth_stage": None,  # Early, Growth, Mature
            "expansion_signals": [],

            # Intent Signals
            "recent_news": [],
            "trigger_events": [],
            "buying_signals": [],

            # Contact Info
            "phone": None,
            "email": None,
            "address": None,

            # Metadata
            "data_quality_score": 0,  # 0-100
            "completeness": 0,  # Percentage of fields filled
        }

        # Enrich from website
        if website:
            web_data = self._enrich_from_website(website)
            enrichment.update(web_data)
            enrichment["data_sources"].append("website")

        # Enrich from Crunchbase (public data)
        crunchbase_data = self._enrich_from_crunchbase(company_name)
        if crunchbase_data:
            self._merge_data(enrichment, crunchbase_data)
            enrichment["data_sources"].append("crunchbase")

        # Tech stack detection
        if website:
            tech_stack = self._detect_tech_stack(website)
            enrichment["technologies"] = tech_stack["technologies"]
            enrichment["tech_categories"] = tech_stack["categories"]
            enrichment["data_sources"].append("tech_detection")

        # Social profile detection
        if website:
            social = self._find_social_profiles(website)
            enrichment["social_profiles"] = social
            if social:
                enrichment["data_sources"].append("social")

        # Deep enrichment
        if deep:
            # News and trigger events
            news = self._fetch_recent_news(company_name)
            enrichment["recent_news"] = news[:5]  # Top 5
            if news:
                enrichment["data_sources"].append("news")

            # Hiring velocity
            hiring = self._analyze_hiring_velocity(company_name, website)
            enrichment.update(hiring)
            if hiring.get("hiring_velocity"):
                enrichment["data_sources"].append("jobs")

        # Calculate data quality and completeness
        enrichment["completeness"] = self._calculate_completeness(enrichment)
        enrichment["data_quality_score"] = self._calculate_quality_score(enrichment)

        return enrichment

    def _enrich_from_website(self, url: str) -> Dict[str, Any]:
        """Extract information from company website"""
        data = {}

        try:
            response = requests.get(url, timeout=15, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Meta description
            meta_desc = soup.find('meta', attrs={'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                data["description"] = meta_desc['content']

            # Open Graph data
            og_desc = soup.find('meta', property='og:description')
            if og_desc and og_desc.get('content') and not data.get("description"):
                data["description"] = og_desc['content']

            # Try to find tagline
            h1 = soup.find('h1')
            if h1:
                data["tagline"] = h1.get_text().strip()[:200]

            # Look for address
            address_patterns = [
                r'\d+\s+[\w\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)',
                r'[A-Z][a-z]+,\s*[A-Z]{2}\s*\d{5}',
            ]
            text = soup.get_text()
            for pattern in address_patterns:
                match = re.search(pattern, text)
                if match:
                    data["address"] = match.group(0)
                    break

            # Look for phone
            phone_patterns = [
                r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
                r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',
            ]
            for pattern in phone_patterns:
                match = re.search(pattern, text)
                if match:
                    data["phone"] = match.group(0)
                    break

            # Look for careers URL
            careers_link = soup.find('a', href=re.compile(r'career|job|hiring|join', re.I))
            if careers_link:
                data["careers_url"] = careers_link.get('href')

            # Look for blog URL
            blog_link = soup.find('a', href=re.compile(r'blog', re.I))
            if blog_link:
                data["blog_url"] = blog_link.get('href')

            # Try to determine company type from content
            text_lower = text.lower()
            if any(word in text_lower for word in ['startup', 'founded in 202', 'founded in 201']):
                data["company_type"] = "startup"
                # Try to extract founded year
                year_match = re.search(r'founded in (\d{4})', text_lower)
                if year_match:
                    data["founded_year"] = int(year_match.group(1))

            # Try to determine industry from keywords
            industry_keywords = {
                'saas': ['software as a service', 'saas', 'cloud platform'],
                'ecommerce': ['ecommerce', 'e-commerce', 'online store', 'shop'],
                'd2c': ['direct to consumer', 'd2c', 'dtc'],
                'fintech': ['fintech', 'financial technology', 'payments'],
                'healthtech': ['healthtech', 'healthcare', 'medical'],
                'edtech': ['edtech', 'education technology', 'learning platform'],
            }

            for industry, keywords in industry_keywords.items():
                if any(kw in text_lower for kw in keywords):
                    data["industry"] = industry
                    break

        except Exception as e:
            logger.error(f"Error enriching from website {url}: {e}")

        return data

    def _enrich_from_crunchbase(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch public data from Crunchbase

        Note: This is a simplified version. Real implementation would use Crunchbase API
        or scrape public Crunchbase pages (respecting robots.txt)
        """
        data = {}

        try:
            # This would require Crunchbase API key for full access
            # For now, we can try to scrape public profile
            search_url = f"https://www.crunchbase.com/organization/{company_name.lower().replace(' ', '-')}"

            # This is just a placeholder - real implementation needs proper API
            logger.info(f"Crunchbase enrichment requires API access for {company_name}")

            # In production, you would:
            # 1. Use Crunchbase API with authentication
            # 2. Extract funding rounds, investors, employee count, etc.
            # 3. Get recent news and acquisition data

        except Exception as e:
            logger.error(f"Error enriching from Crunchbase: {e}")

        return data if data else None

    def _detect_tech_stack(self, url: str) -> Dict[str, Any]:
        """
        Detect technologies used by company website

        Similar to BuiltWith or Wappalyzer
        """
        tech_data = {
            "technologies": [],
            "categories": []
        }

        try:
            response = requests.get(url, timeout=15)
            html = response.text
            headers = response.headers

            # Detect frameworks and libraries
            detections = {
                # Frontend frameworks
                "React": r'react|_reactRootContainer|__REACT',
                "Vue": r'vue\.js|__vue__|v-app',
                "Angular": r'ng-app|ng-controller|angular\.js',
                "Next.js": r'__NEXT_DATA__|_next/',
                "Nuxt": r'__NUXT__',

                # Backend indicators
                "WordPress": r'wp-content|wp-includes',
                "Shopify": r'cdn\.shopify\.com|shopify',
                "Wix": r'wix\.com',
                "Squarespace": r'squarespace',

                # Analytics
                "Google Analytics": r'google-analytics\.com|gtag|ga\(',
                "Facebook Pixel": r'facebook\.net/en_US/fbevents',
                "Mixpanel": r'mixpanel',
                "Segment": r'segment\.com|analytics\.js',

                # Marketing tools
                "HubSpot": r'hs-scripts\.com|hubspot',
                "Intercom": r'intercom\.io|widget\.intercom',
                "Drift": r'drift\.com',

                # CDNs
                "Cloudflare": r'cloudflare',
                "Fastly": r'fastly',

                # Payment processors
                "Stripe": r'stripe\.com',
                "PayPal": r'paypal',
            }

            for tech, pattern in detections.items():
                if re.search(pattern, html, re.I):
                    tech_data["technologies"].append(tech)

            # Check headers
            if 'X-Powered-By' in headers:
                tech_data["technologies"].append(headers['X-Powered-By'])

            if 'Server' in headers:
                server = headers['Server']
                if 'nginx' in server.lower():
                    tech_data["technologies"].append("Nginx")
                elif 'apache' in server.lower():
                    tech_data["technologies"].append("Apache")

            # Categorize technologies
            categories_map = {
                "frontend": ["React", "Vue", "Angular", "Next.js"],
                "ecommerce": ["Shopify", "WooCommerce"],
                "cms": ["WordPress", "Wix", "Squarespace"],
                "analytics": ["Google Analytics", "Mixpanel", "Segment"],
                "marketing": ["HubSpot", "Intercom", "Drift"],
                "payments": ["Stripe", "PayPal"],
            }

            for category, techs in categories_map.items():
                if any(t in tech_data["technologies"] for t in techs):
                    tech_data["categories"].append(category)

            # Remove duplicates
            tech_data["technologies"] = list(set(tech_data["technologies"]))
            tech_data["categories"] = list(set(tech_data["categories"]))

        except Exception as e:
            logger.error(f"Error detecting tech stack for {url}: {e}")

        return tech_data

    def _find_social_profiles(self, url: str) -> Dict[str, str]:
        """Find social media profiles"""
        profiles = {}

        try:
            response = requests.get(url, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find social links
            social_patterns = {
                'linkedin': r'linkedin\.com/company/([^/\s"\']+)',
                'twitter': r'(?:twitter|x)\.com/([^/\s"\']+)',
                'facebook': r'facebook\.com/([^/\s"\']+)',
                'instagram': r'instagram\.com/([^/\s"\']+)',
                'youtube': r'youtube\.com/(?:c/|channel/|user/)?([^/\s"\']+)',
                'github': r'github\.com/([^/\s"\']+)',
            }

            page_html = response.text

            for platform, pattern in social_patterns.items():
                match = re.search(pattern, page_html, re.I)
                if match:
                    profiles[platform] = match.group(0)

        except Exception as e:
            logger.error(f"Error finding social profiles: {e}")

        return profiles

    def _fetch_recent_news(self, company_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch recent news about company

        This would use News API or similar service
        """
        news = []

        try:
            # Placeholder for news API integration
            # Real implementation would use:
            # - News API (newsapi.org)
            # - Google News scraping
            # - Company blog RSS feed
            # - PR Newswire / Business Wire

            logger.info(f"News fetching for {company_name} requires News API")

        except Exception as e:
            logger.error(f"Error fetching news: {e}")

        return news

    def _analyze_hiring_velocity(self, company_name: str, website: Optional[str]) -> Dict[str, Any]:
        """
        Analyze hiring velocity (growth indicator)

        Checks:
        - Number of open positions
        - Growth rate of job postings
        - Hiring for key roles (exec, leadership)
        """
        data = {
            "hiring_velocity": None,
            "open_positions": 0,
            "key_hires": [],
            "expansion_signals": []
        }

        try:
            # This would scrape career page or job boards
            # Check for multiple open positions
            # Track over time to calculate velocity

            logger.info("Hiring velocity analysis requires job board scraping")

        except Exception as e:
            logger.error(f"Error analyzing hiring velocity: {e}")

        return data

    def _merge_data(self, target: Dict, source: Dict):
        """Merge source data into target, only adding non-None values"""
        for key, value in source.items():
            if value is not None and (target.get(key) is None or target[key] == ""):
                target[key] = value

    def _calculate_completeness(self, data: Dict) -> int:
        """Calculate what percentage of fields are populated"""
        total_fields = 0
        filled_fields = 0

        skip_fields = {"enriched_at", "data_sources", "completeness", "data_quality_score"}

        for key, value in data.items():
            if key in skip_fields:
                continue

            total_fields += 1

            if value is not None:
                if isinstance(value, (list, dict)):
                    if len(value) > 0:
                        filled_fields += 1
                elif value != "":
                    filled_fields += 1

        if total_fields == 0:
            return 0

        return int((filled_fields / total_fields) * 100)

    def _calculate_quality_score(self, data: Dict) -> int:
        """
        Calculate overall data quality score (0-100)

        Based on:
        - Number of data sources
        - Completeness
        - Presence of key fields
        """
        score = 0

        # Base score from completeness
        score += data.get("completeness", 0) * 0.4

        # Bonus for number of data sources
        sources = len(data.get("data_sources", []))
        score += min(sources * 10, 20)

        # Bonus for key fields
        key_fields = [
            "website", "description", "employee_count", "industry",
            "technologies", "social_profiles"
        ]

        for field in key_fields:
            value = data.get(field)
            if value:
                if isinstance(value, (list, dict)):
                    if len(value) > 0:
                        score += 5
                else:
                    score += 5

        return min(int(score), 100)

    def detect_trigger_events(self, company_name: str, enrichment_data: Dict) -> List[Dict[str, Any]]:
        """
        Detect trigger events that indicate buying intent

        Trigger events:
        - Recent funding
        - Rapid hiring
        - New product launch
        - Executive hire
        - Office expansion
        - Technology migration
        """
        triggers = []

        # Recent funding
        if enrichment_data.get("last_funding_date"):
            try:
                funding_date = datetime.fromisoformat(enrichment_data["last_funding_date"])
                days_ago = (datetime.now() - funding_date).days

                if days_ago < 90:  # Within 3 months
                    triggers.append({
                        "type": "funding",
                        "severity": "high",
                        "description": f"Raised {enrichment_data.get('last_funding_amount', 'funding')} {days_ago} days ago",
                        "action": "Reach out about growth initiatives"
                    })
            except:
                pass

        # Rapid hiring (>5 open positions)
        if enrichment_data.get("open_positions", 0) > 5:
            triggers.append({
                "type": "hiring_spree",
                "severity": "medium",
                "description": f"{enrichment_data['open_positions']} open positions",
                "action": "They're scaling - need better systems"
            })

        # Tech stack changes could indicate migration
        if len(enrichment_data.get("technologies", [])) > 8:
            triggers.append({
                "type": "tech_stack",
                "severity": "low",
                "description": "Complex tech stack",
                "action": "May need marketing automation"
            })

        return triggers


# Global instance
company_enrichment = CompanyEnrichment()
