# Web Scraping Guide

## Overview

Raptorflow Lead Engine now includes comprehensive web scraping capabilities to automatically discover and collect leads from multiple sources. The scraping system respects robots.txt, implements rate limiting, and includes automatic retry logic.

## Features

### 🎯 Job Board Scraping
Automatically scrape job postings from multiple job boards:
- **Indeed.com** - Global job board
- **Naukri.com** - Indian job board
- **LinkedIn Jobs** - Professional network (limited, may be blocked)
- **Generic Career Pages** - Any company career page

### 🏢 Company Website Scraping
Extract comprehensive information from company websites:
- Contact emails and phone numbers
- Career page URLs
- Job postings and hiring signals
- Social media links (LinkedIn, Twitter, Facebook, etc.)
- Technologies used
- Company size hints
- Deep scan mode for thorough analysis

### 🔍 Lead Discovery
Discover new potential leads via search engines:
- DuckDuckGo search integration
- Keyword-based discovery
- Optional automatic company scraping
- Batch processing

### 📄 Career Page Scraping
Target specific career/jobs pages:
- Extract all job postings
- Automatic company association
- Contact information extraction

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Install Tesseract (for OCR, optional)

**Ubuntu/Debian:**
```bash
sudo apt install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download installer from: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Install Playwright (optional, for advanced scraping)

```bash
playwright install
```

## Usage

### API Endpoints

#### 1. Scrape Job Boards

**Endpoint:** `POST /api/scrape/job-boards`

**Request:**
```json
{
  "query": "marketing manager",
  "location": "Mumbai",
  "sources": ["indeed", "naukri"],
  "num_pages": 3
}
```

**Response:**
```json
{
  "status": "completed",
  "message": "Scraped 45 jobs, created 12 leads",
  "results": {
    "query": "marketing manager",
    "total_jobs": 45,
    "total_leads_created": 12,
    "sources": {
      "indeed": {"jobs_found": 25, "status": "success"},
      "naukri": {"jobs_found": 20, "status": "success"}
    }
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/scrape/job-boards \
  -H "Content-Type: application/json" \
  -d '{
    "query": "growth hacker",
    "location": "Bangalore",
    "sources": ["indeed", "naukri"],
    "num_pages": 2
  }'
```

#### 2. Scrape Company Website

**Endpoint:** `POST /api/scrape/company-website`

**Request:**
```json
{
  "url": "https://example.com",
  "company_name": "Example Corp",
  "deep_scan": true
}
```

**Response:**
```json
{
  "status": "completed",
  "message": "Scraped https://example.com, created 3 leads",
  "results": {
    "company_data": {
      "name": "Example Corp",
      "url": "https://example.com",
      "emails": ["contact@example.com", "jobs@example.com"],
      "phones": ["+91-9876543210"],
      "career_page_url": "https://example.com/careers",
      "has_jobs": true,
      "job_signals": [
        "Hiring: Marketing Manager",
        "Looking for Growth Hacker"
      ],
      "technologies": ["react", "python", "aws"],
      "company_size_hints": ["team of 15", "growing team"]
    },
    "leads_created": 3
  }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/api/scrape/company-website \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "deep_scan": true
  }'
```

#### 3. Discover Leads

**Endpoint:** `POST /api/scrape/discover-leads`

**Request:**
```json
{
  "search_query": "D2C ecommerce India hiring marketing",
  "num_results": 30,
  "scrape_companies": true
}
```

**Response:**
```json
{
  "status": "completed",
  "message": "Found 30 URLs, created 8 leads",
  "results": {
    "urls_found": 30,
    "companies_scraped": 30,
    "leads_created": 8,
    "discovered_urls": [
      "https://example1.com",
      "https://example2.com"
    ]
  }
}
```

#### 4. Scrape Career Page

**Endpoint:** `POST /api/scrape/career-page`

**Request:**
```json
{
  "url": "https://example.com/careers",
  "company_name": "Example Corp"
}
```

**Response:**
```json
{
  "status": "completed",
  "message": "Found 5 jobs, created 2 leads",
  "results": {
    "jobs_found": 5,
    "leads_created": 2
  }
}
```

#### 5. List Scraping Sources

**Endpoint:** `GET /api/scrape/sources`

Returns information about available scraping sources and their capabilities.

### Frontend UI

Access the web scraper through the main UI:

1. Start the backend: `cd backend && ./run.sh`
2. Start the frontend: `npm run dev`
3. Navigate to http://localhost:3000
4. Click on the **🕷️ Web Scraper** tab

#### Job Boards Tab
- Enter job search query (e.g., "marketing manager")
- Optionally add location
- Select job boards to scrape
- Set number of pages per source
- Click "Start Scraping"

#### Company Website Tab
- Enter company website URL
- Optionally provide company name
- Enable "Deep Scan" for thorough analysis
- Click "Scrape Company Website"

#### Lead Discovery Tab
- Enter search query with keywords
- Set number of results
- Enable "Also scrape each discovered company" for automatic processing
- Click "Discover Leads"

#### Career Page Tab
- Enter specific career page URL
- Provide company name
- Click "Scrape Career Page"

## Architecture

### Components

```
backend/scrapers/
├── __init__.py
├── base_scraper.py           # Base class with common functionality
├── job_scrapers.py            # Job board scrapers
├── company_scraper.py         # Company website scraper
└── scraping_service.py        # Orchestration service
```

### Base Scraper Features

The `BaseScraper` class provides:
- **Rate Limiting**: Configurable delay between requests (default 2 seconds)
- **Robots.txt Respect**: Automatically checks and respects robots.txt
- **User Agent Rotation**: Randomizes user agents to avoid detection
- **Retry Logic**: Automatic retries with exponential backoff (up to 3 attempts)
- **Contact Extraction**: Regex-based email and phone extraction
- **Social Link Detection**: Finds LinkedIn, Twitter, Facebook, etc.

### Job Scrapers

#### IndeedScraper
- Scrapes Indeed.com job listings
- Extracts: title, company, location, description, URL
- Rate limit: 2 seconds

#### NaukriScraper
- Scrapes Naukri.com (Indian job board)
- Extracts: title, company, location, experience, salary, description
- Rate limit: 2 seconds

#### LinkedInJobsScraper
- Scrapes public LinkedIn job listings
- ⚠️ **Warning**: LinkedIn actively blocks scrapers, use cautiously
- Rate limit: 3 seconds (slower to avoid detection)

#### GenericJobScraper
- Works with any career/jobs page
- Pattern-based job detection
- Flexible extraction

### Company Scraper

Features:
- Homepage analysis
- Career page detection and crawling
- Contact page detection and crawling
- Hiring signal detection (keywords like "we're hiring", "join our team")
- Technology stack detection
- Company size estimation
- Social media link extraction

### Scraping Service

The orchestration layer that:
- Coordinates multiple scrapers
- Processes results and creates leads
- Handles deduplication
- Integrates with classification pipeline
- Manages database operations

## Configuration

### Rate Limiting

Default rate limits (seconds between requests):
- Indeed: 2 seconds
- Naukri: 2 seconds
- LinkedIn: 3 seconds
- Company websites: 2 seconds
- Search engines: 2 seconds

To customize, modify the scraper initialization in `scraping_service.py`:

```python
self.indeed_scraper = IndeedScraper(rate_limit=3.0)  # 3 seconds
```

### Robots.txt Respect

By default, all scrapers respect robots.txt. To disable (not recommended):

```python
scraper = BaseScraper(respect_robots=False)
```

### Retry Configuration

Retries use exponential backoff with these defaults:
- Max attempts: 3
- Min wait: 2 seconds
- Max wait: 10 seconds
- Multiplier: 1

To customize, modify the `@retry` decorator in `base_scraper.py`.

## Data Flow

1. **Scraping** → Raw job postings/company data collected
2. **Deduplication** → Check for existing signals/companies
3. **Signal Creation** → Store raw signal in database
4. **Classification** → Run through Gemma 3 1B model
5. **Lead Creation** → Create lead record if ICP match
6. **Enrichment** → Background task for high-scoring leads (Gemma 3 4B)
7. **Contact Creation** → Store emails/phones as contact records

## Best Practices

### 1. Start Small
Begin with 1-2 pages per source to test:
```json
{
  "query": "marketing manager",
  "sources": ["indeed"],
  "num_pages": 1
}
```

### 2. Use Specific Queries
More specific queries yield better results:
- ✅ Good: "D2C ecommerce marketing manager India"
- ❌ Too broad: "marketing"

### 3. Respect Rate Limits
Don't scrape too aggressively:
- Stick to default rate limits
- Use LinkedIn sparingly (high detection risk)
- Space out large scraping jobs

### 4. Deep Scan Strategically
Deep scans are slower but more thorough:
- Use for high-value targets
- Skip for bulk discovery
- Combine with lead scoring

### 5. Monitor Results
Check the leads created:
```bash
curl http://localhost:8000/api/leads/ | jq '.[] | {company: .company_name, score: .total_score}'
```

### 6. Set Up ICP First
Create ICP profiles before scraping for better classification:
1. Go to ICP Whiteboard tab
2. Define your ideal customer profile
3. Add relevant keywords
4. Then start scraping

## Limitations & Legal Considerations

### Technical Limitations

1. **LinkedIn**: Actively blocks scrapers, may require authentication
2. **Rate Limits**: Scraping is slower due to respectful rate limiting
3. **Dynamic Content**: Some sites use JavaScript rendering (may need Playwright)
4. **CAPTCHAs**: Sites with CAPTCHA protection won't work
5. **IP Blocking**: Excessive scraping may result in temporary IP blocks

### Legal & Ethical

⚠️ **Important**: Web scraping legality varies by jurisdiction and website terms of service.

**Before scraping:**
1. ✅ Check the website's Terms of Service
2. ✅ Respect robots.txt (enabled by default)
3. ✅ Use reasonable rate limits
4. ✅ Don't scrape personal data without consent
5. ✅ Comply with GDPR/data protection laws
6. ✅ Don't circumvent authentication or paywalls

**Recommended use cases:**
- ✅ Public job postings
- ✅ Public company information
- ✅ Contact information intended for business inquiries
- ✅ Research and analysis

**Avoid:**
- ❌ Scraping private/authenticated content
- ❌ Aggressive scraping that impacts site performance
- ❌ Circumventing anti-scraping measures
- ❌ Scraping personal data for marketing without consent

### GDPR Compliance

If operating in EU or handling EU data:
- Implement data retention policies
- Provide opt-out mechanisms
- Document data processing activities
- Ensure lawful basis for processing

## Troubleshooting

### Common Issues

#### 1. "Blocked by robots.txt"
**Cause**: Website robots.txt disallows scraping
**Solution**: Respect the restriction or contact website owner

#### 2. "Connection timeout"
**Cause**: Website is slow or blocking requests
**Solution**:
- Increase timeout in `base_scraper.py`
- Check if IP is blocked
- Try again later

#### 3. "No jobs found"
**Cause**: Query too specific or scraper pattern mismatch
**Solution**:
- Try broader query
- Check if website structure changed
- Use generic career page scraper

#### 4. "Rate limit exceeded"
**Cause**: Too many requests too quickly
**Solution**:
- Increase rate_limit parameter
- Reduce num_pages
- Space out scraping jobs

#### 5. LinkedIn returns no results
**Cause**: LinkedIn blocking scraper
**Solution**:
- LinkedIn scraping is unreliable
- Use Indeed or Naukri instead
- Consider LinkedIn API (requires authentication)

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Scrapers

Test individual scrapers:

```python
from backend.scrapers.job_scrapers import IndeedScraper

scraper = IndeedScraper()
jobs = scraper.scrape_jobs("marketing manager", location="Mumbai", num_pages=1)
print(f"Found {len(jobs)} jobs")
for job in jobs:
    print(f"- {job['title']} at {job['company']}")
```

## Performance

### Speed

Typical scraping times:
- Job board (1 page): ~10-15 seconds
- Company website (basic): ~5-10 seconds
- Company website (deep scan): ~20-40 seconds
- Lead discovery (20 results): ~30-60 seconds
- Lead discovery with scraping: ~5-10 minutes

### Optimization Tips

1. **Parallel Scraping**: Modify `scraping_service.py` to use `ThreadPoolExecutor` for concurrent requests
2. **Caching**: Implement Redis caching for frequently accessed pages
3. **Selective Deep Scans**: Only deep scan high-scoring leads
4. **Batch Processing**: Queue scraping jobs for off-peak processing

## Advanced Usage

### Scheduled Scraping

Use APScheduler to run periodic scraping:

```python
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

def daily_job_scrape():
    results = scraping_service.scrape_job_boards(
        query="marketing manager",
        sources=["indeed", "naukri"],
        num_pages=5
    )
    print(f"Daily scrape: {results['total_leads_created']} leads created")

# Run every day at 9 AM
scheduler.add_job(daily_job_scrape, 'cron', hour=9)
scheduler.start()
```

### Custom Scrapers

Create custom scrapers by extending `BaseScraper`:

```python
from backend.scrapers.base_scraper import BaseScraper

class CustomJobBoardScraper(BaseScraper):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_url = "https://customjobboard.com"

    def scrape_jobs(self, query: str, num_pages: int = 3):
        jobs = []
        for page in range(num_pages):
            url = f"{self.base_url}/search?q={query}&page={page}"
            response = self.fetch(url)
            if response:
                soup = self.parse_html(response.text)
                # Custom extraction logic here
                jobs.extend(self._extract_jobs(soup))
        return jobs
```

### Webhook Integration

Add webhooks to notify when leads are created:

```python
import requests

def notify_new_lead(lead_data):
    webhook_url = "https://your-webhook-url.com"
    requests.post(webhook_url, json=lead_data)

# In scraping_service.py after creating lead:
if lead:
    notify_new_lead({
        "company": lead.company.name,
        "score": lead.total_score,
        "bucket": lead.score_bucket
    })
```

## API Reference

See full API documentation at: http://localhost:8000/docs

## Support

For issues or questions:
1. Check this guide
2. Review the code documentation
3. Open an issue on GitHub
4. Check logs in `backend/` directory

## Future Enhancements

Planned features:
- [ ] Proxy support for large-scale scraping
- [ ] CAPTCHA solving integration
- [ ] More job board integrations (Monster, Glassdoor, etc.)
- [ ] Email finder tools integration (Hunter.io, etc.)
- [ ] CRM integrations (Salesforce, HubSpot)
- [ ] Advanced deduplication with fuzzy matching
- [ ] Scraping job queue with Celery + Redis
- [ ] Rate limit auto-adjustment based on response
- [ ] Machine learning for better signal detection

## Changelog

### v0.2.0 (Current)
- ✅ Job board scraping (Indeed, Naukri, LinkedIn)
- ✅ Company website scraping
- ✅ Lead discovery via search
- ✅ Career page scraping
- ✅ Rate limiting and retry logic
- ✅ Data deduplication
- ✅ Frontend UI
- ✅ Full API integration

### v0.1.0 (Previous)
- Basic classification pipeline
- OCR ingestion
- ICP management
- Lead scoring
