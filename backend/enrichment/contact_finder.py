"""
Advanced Contact Finder - Email pattern generation, verification, and discovery
"""
import re
import logging
import dns.resolver
import smtplib
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class EmailCandidate:
    """Represents a potential email address"""
    email: str
    pattern: str
    confidence: float  # 0-1
    verified: bool = False
    deliverable: Optional[bool] = None
    source: str = "generated"


class ContactFinder:
    """
    Advanced contact finder that generates and verifies email addresses
    """

    # Common email patterns
    EMAIL_PATTERNS = [
        "{first}.{last}@{domain}",      # john.doe@company.com
        "{first}{last}@{domain}",       # johndoe@company.com
        "{f}{last}@{domain}",           # jdoe@company.com
        "{first}@{domain}",             # john@company.com
        "{first}_{last}@{domain}",      # john_doe@company.com
        "{first}-{last}@{domain}",      # john-doe@company.com
        "{last}.{first}@{domain}",      # doe.john@company.com
        "{last}{first}@{domain}",       # doejohn@company.com
        "{last}@{domain}",              # doe@company.com
        "{first}{l}@{domain}",          # johnd@company.com
        "{f}.{last}@{domain}",          # j.doe@company.com
    ]

    # Common business email prefixes to try
    COMMON_PREFIXES = [
        "info", "contact", "hello", "sales", "support",
        "admin", "team", "hr", "jobs", "careers",
        "marketing", "business", "office", "inquiry"
    ]

    def __init__(self):
        self.dns_cache = {}
        self.mx_cache = {}

    def find_contacts(
        self,
        company_name: str,
        website: Optional[str] = None,
        person_name: Optional[str] = None,
        linkedin_url: Optional[str] = None
    ) -> List[EmailCandidate]:
        """
        Find contact emails for a company/person

        Args:
            company_name: Company name
            website: Company website URL
            person_name: Person's name (optional)
            linkedin_url: LinkedIn profile URL (optional)

        Returns:
            List of email candidates with confidence scores
        """
        candidates = []

        # Extract domain from website
        domain = self._extract_domain(website) if website else None

        if not domain:
            # Try to guess domain from company name
            domain = self._guess_domain(company_name)

        if not domain:
            logger.warning(f"Could not determine domain for {company_name}")
            return candidates

        # Check if domain has valid MX records
        if not self._has_mx_records(domain):
            logger.warning(f"No MX records found for {domain}")
            # Try common alternatives
            for alt in [f"www.{domain}", domain.replace("www.", "")]:
                if self._has_mx_records(alt):
                    domain = alt
                    break

        # Generate common business emails
        candidates.extend(self._generate_common_emails(domain))

        # If we have a person name, generate personalized emails
        if person_name:
            candidates.extend(self._generate_person_emails(person_name, domain))

        # Scrape website for emails
        if website:
            scraped = self._scrape_website_for_emails(website)
            candidates.extend(scraped)

        # Verify emails (SMTP check)
        verified_candidates = []
        for candidate in candidates:
            is_deliverable = self._verify_email(candidate.email)
            candidate.deliverable = is_deliverable
            if is_deliverable or candidate.source == "scraped":
                verified_candidates.append(candidate)

        # Sort by confidence
        verified_candidates.sort(key=lambda x: x.confidence, reverse=True)

        return verified_candidates

    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc or parsed.path
            domain = domain.replace("www.", "")
            # Remove trailing slash and path
            domain = domain.split("/")[0]
            return domain if domain else None
        except:
            return None

    def _guess_domain(self, company_name: str) -> Optional[str]:
        """Guess domain from company name"""
        # Clean company name
        clean = re.sub(r'[^a-z0-9\s]', '', company_name.lower())
        clean = clean.replace(" ", "")

        # Try common TLDs
        common_tlds = [".com", ".co", ".io", ".ai", ".in"]

        for tld in common_tlds:
            domain = f"{clean}{tld}"
            if self._has_mx_records(domain):
                return domain

        # Default to .com
        return f"{clean}.com"

    def _has_mx_records(self, domain: str) -> bool:
        """Check if domain has MX records"""
        if domain in self.mx_cache:
            return self.mx_cache[domain]

        try:
            dns.resolver.resolve(domain, 'MX')
            self.mx_cache[domain] = True
            return True
        except:
            self.mx_cache[domain] = False
            return False

    def _generate_common_emails(self, domain: str) -> List[EmailCandidate]:
        """Generate common business emails"""
        candidates = []

        for prefix in self.COMMON_PREFIXES:
            email = f"{prefix}@{domain}"
            candidates.append(EmailCandidate(
                email=email,
                pattern=f"{{{prefix}}}@{{domain}}",
                confidence=0.4 if prefix in ["info", "contact", "hello"] else 0.3,
                source="generated"
            ))

        return candidates

    def _generate_person_emails(self, name: str, domain: str) -> List[EmailCandidate]:
        """Generate email patterns for a person"""
        candidates = []

        # Parse name
        parts = name.lower().strip().split()
        if len(parts) < 2:
            return candidates

        first = parts[0]
        last = parts[-1]
        f = first[0]
        l = last[0]

        # Generate all patterns
        for pattern in self.EMAIL_PATTERNS:
            try:
                email = pattern.format(
                    first=first,
                    last=last,
                    f=f,
                    l=l,
                    domain=domain
                )

                # Confidence based on pattern popularity
                confidence = self._pattern_confidence(pattern)

                candidates.append(EmailCandidate(
                    email=email,
                    pattern=pattern,
                    confidence=confidence,
                    source="generated"
                ))
            except:
                continue

        return candidates

    def _pattern_confidence(self, pattern: str) -> float:
        """Get confidence score for email pattern"""
        # More common patterns have higher confidence
        confidence_map = {
            "{first}.{last}@{domain}": 0.9,
            "{first}{last}@{domain}": 0.8,
            "{f}{last}@{domain}": 0.7,
            "{first}@{domain}": 0.6,
            "{first}_{last}@{domain}": 0.5,
        }
        return confidence_map.get(pattern, 0.4)

    def _scrape_website_for_emails(self, url: str) -> List[EmailCandidate]:
        """Scrape website for email addresses"""
        candidates = []

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            # Extract emails using regex
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, response.text)

            # Also check for mailto: links
            soup = BeautifulSoup(response.text, 'html.parser')
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:'))
            for link in mailto_links:
                email = link['href'].replace('mailto:', '').split('?')[0]
                emails.append(email)

            # Filter and create candidates
            seen = set()
            for email in emails:
                email = email.lower().strip()

                # Skip common garbage
                if any(x in email for x in ['example', 'test', 'sample', 'noreply', 'no-reply']):
                    continue

                if email not in seen:
                    seen.add(email)
                    candidates.append(EmailCandidate(
                        email=email,
                        pattern="scraped",
                        confidence=0.95,  # High confidence for scraped emails
                        verified=True,
                        source="scraped"
                    ))

        except Exception as e:
            logger.error(f"Error scraping website for emails: {e}")

        return candidates

    def _verify_email(self, email: str) -> Optional[bool]:
        """
        Verify email deliverability using SMTP

        Returns:
            True if deliverable, False if not, None if uncertain
        """
        try:
            # Extract domain
            domain = email.split('@')[1]

            # Get MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange)

            # Connect to SMTP server
            server = smtplib.SMTP(timeout=10)
            server.set_debuglevel(0)
            server.connect(mx_host)
            server.helo(server.local_hostname)
            server.mail('verify@example.com')

            # Check if recipient exists
            code, message = server.rcpt(email)
            server.quit()

            # 250 = success, 550 = user not found
            if code == 250:
                return True
            elif code == 550:
                return False
            else:
                return None

        except dns.resolver.NXDOMAIN:
            return False
        except dns.resolver.NoAnswer:
            return None
        except smtplib.SMTPServerDisconnected:
            return None
        except smtplib.SMTPConnectError:
            return None
        except Exception as e:
            logger.debug(f"Email verification error for {email}: {e}")
            return None

    def find_linkedin_email(self, linkedin_url: str) -> Optional[str]:
        """
        Extract email from LinkedIn profile (if public)

        Note: This requires authentication for most profiles
        """
        # This is a placeholder - real implementation would need:
        # 1. LinkedIn API access
        # 2. Authentication
        # 3. Proper permission handling
        logger.info("LinkedIn email extraction requires API access")
        return None

    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def is_catch_all(self, domain: str) -> bool:
        """
        Check if domain uses catch-all email (accepts any email)

        This is important because catch-all domains will verify as deliverable
        even for non-existent addresses
        """
        try:
            # Generate random email
            random_email = f"nonexistent{hash(domain)}@{domain}"

            # If this verifies as deliverable, it's likely catch-all
            is_deliverable = self._verify_email(random_email)

            return is_deliverable == True

        except Exception as e:
            logger.debug(f"Catch-all check error for {domain}: {e}")
            return False

    def find_decision_makers(
        self,
        company_name: str,
        website: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Find decision makers at a company

        Args:
            company_name: Company name
            website: Company website
            roles: List of roles to find (e.g., ["CEO", "Founder", "Marketing Director"])

        Returns:
            List of decision makers with contact info
        """
        if roles is None:
            roles = [
                "CEO", "Founder", "Co-Founder", "Chief Executive Officer",
                "Marketing Director", "CMO", "Chief Marketing Officer",
                "Head of Marketing", "VP Marketing", "Growth Lead"
            ]

        # This is a placeholder for advanced functionality
        # Real implementation would:
        # 1. Scrape LinkedIn Sales Navigator
        # 2. Use Apollo.io / Hunter.io / RocketReach API
        # 3. Scrape company About/Team pages
        # 4. Use Clearbit Person API

        logger.info(f"Decision maker finding for {company_name} - requires additional APIs")

        decision_makers = []

        # Try to scrape about/team page
        if website:
            team_members = self._scrape_team_page(website)
            decision_makers.extend(team_members)

        return decision_makers

    def _scrape_team_page(self, website: str) -> List[Dict[str, Any]]:
        """Scrape company team/about page for contacts"""
        team_members = []

        try:
            # Common team page URLs
            team_urls = [
                f"{website}/team",
                f"{website}/about",
                f"{website}/about-us",
                f"{website}/leadership",
                f"{website}/our-team",
                f"{website}/company",
            ]

            for url in team_urls:
                try:
                    response = requests.get(url, timeout=10)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Look for name + title patterns
                    # This is basic - real implementation would use NER
                    text = soup.get_text()

                    # Find patterns like "John Doe - CEO" or "Jane Smith, Founder"
                    name_title_pattern = r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[-,]\s*([A-Z][a-z]+(?: [A-Z][a-z]+)*)'
                    matches = re.findall(name_title_pattern, text)

                    for name, title in matches:
                        if any(role.lower() in title.lower() for role in ["ceo", "founder", "director", "head", "vp", "chief"]):
                            team_members.append({
                                "name": name,
                                "title": title,
                                "source": "team_page"
                            })

                    break  # Found a team page, stop trying

                except Exception as e:
                    continue

        except Exception as e:
            logger.error(f"Error scraping team page: {e}")

        return team_members


# Global instance
contact_finder = ContactFinder()
