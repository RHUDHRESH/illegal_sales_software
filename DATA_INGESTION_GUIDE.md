# Data Ingestion and Lead Sourcing Guide

This guide covers all the data ingestion and lead sourcing features available in the Raptorflow Lead Engine.

## Table of Contents

1. [CSV Job Importer](#csv-job-importer)
2. [Job Board API Integration](#job-board-api-integration)
3. [Web Scraping](#web-scraping)
4. [Depth-Limited Website Crawler](#depth-limited-website-crawler)
5. [Email and Phone Extraction](#email-and-phone-extraction)
6. [Social Media Scraping](#social-media-scraping)
7. [PDF Business Card Parsing](#pdf-business-card-parsing)
8. [RSS/Atom Feed Monitoring](#rssatom-feed-monitoring)
9. [LinkedIn Post URL Ingestion](#linkedin-post-url-ingestion)
10. [Bulk JSON Import](#bulk-json-import)
11. [Scheduled Tasks](#scheduled-tasks)

---

## CSV Job Importer

Upload CSV files with job-specific columns to automatically create and classify leads.

**Endpoint:** `POST /api/ingest/jobs/csv`

**Expected CSV Columns:**
- `company_name` (required)
- `title` (optional) - Job title
- `description` (required) - Job description
- `location` (optional) - Job location
- `posted_at` (optional) - When the job was posted
- `company_website` (optional) - Company website URL

**Example CSV:**
```csv
company_name,title,description,location,posted_at
Acme Corp,Marketing Manager,We need a marketing manager with 5 years experience...,Mumbai,2025-01-15
TechStart Inc,Growth Hacker,Looking for a growth hacker to scale our D2C brand...,Bangalore,2025-01-14
```

**Example Request:**
```bash
curl -X POST "http://localhost:8000/api/ingest/jobs/csv" \
  -F "file=@jobs.csv"
```

**Response:**
```json
{
  "total_processed": 2,
  "total_created": 2,
  "results": [
    {
      "company": "Acme Corp",
      "title": "Marketing Manager",
      "score": 75,
      "bucket": "warm",
      "lead_id": 123,
      "status": "created"
    }
  ]
}
```

---

## Job Board API Integration

Automatically fetch marketing roles from job board APIs (Naukri, LinkedIn).

**Setup:**

Set environment variables for API credentials:

```bash
# Naukri API
export NAUKRI_API_KEY="your_api_key"
export NAUKRI_API_SECRET="your_api_secret"

# LinkedIn Jobs API
export LINKEDIN_CLIENT_ID="your_client_id"
export LINKEDIN_CLIENT_SECRET="your_client_secret"
export LINKEDIN_ACCESS_TOKEN="your_access_token"
```

**Endpoint:** `POST /api/advanced/job-boards/api-search`

**Request Body:**
```json
{
  "boards": ["naukri", "linkedin"],
  "keywords": ["marketing manager", "growth hacker"],
  "location": "India",
  "max_results_per_board": 20,
  "auto_classify": true
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/advanced/job-boards/api-search" \
  -H "Content-Type: application/json" \
  -d '{
    "boards": ["naukri"],
    "keywords": ["marketing manager"],
    "location": "Mumbai",
    "max_results_per_board": 10
  }'
```

**Note:** API access requires proper credentials from each job board platform.

---

## Web Scraping

Scrape job boards and company websites using the existing scraping infrastructure.

**Endpoint:** `POST /api/scrape/job-boards`

See [SCRAPING_GUIDE.md](SCRAPING_GUIDE.md) for full details on web scraping features.

---

## Depth-Limited Website Crawler

Crawl a website with depth-limiting (up to 5 pages) to extract text from multiple pages including `/about`, `/careers`, `/jobs`, and `/blog`.

**Endpoint:** `POST /api/advanced/crawl/website`

**Request Body:**
```json
{
  "url": "https://example.com",
  "max_pages": 5,
  "max_depth": 2,
  "auto_classify": true
}
```

**Parameters:**
- `url` (required) - Starting URL to crawl
- `max_pages` (default: 5) - Maximum number of pages to crawl
- `max_depth` (default: 2) - Maximum depth from start URL
- `auto_classify` (default: true) - Automatically classify crawled content

**Example:**
```bash
curl -X POST "http://localhost:8000/api/advanced/crawl/website" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://acmecorp.com",
    "max_pages": 5,
    "auto_classify": true
  }'
```

**Response:**
```json
{
  "url": "https://acmecorp.com",
  "domain": "acmecorp.com",
  "pages_crawled": 5,
  "pages": [
    {
      "url": "https://acmecorp.com",
      "title": "Acme Corp - Home",
      "text": "...",
      "emails": ["contact@acmecorp.com"],
      "phones": ["+919876543210"]
    }
  ],
  "summary": "...",
  "emails_found": ["contact@acmecorp.com"],
  "phones_found": ["+919876543210"],
  "classification": {
    "lead_id": 123,
    "total_score": 65,
    "score_bucket": "warm"
  }
}
```

**Features:**
- Prioritizes important pages (/about, /careers, /jobs, /blog)
- Respects robots.txt
- Rate limiting (2 seconds between requests)
- Automatic email and phone extraction
- Text summarization for classification

---

## Email and Phone Extraction

All ingestion methods automatically extract and normalize contact information.

**Phone Normalization:**

Phone numbers are automatically normalized to E.164 format using the `phonenumbers` library:
- Input: `9876543210` or `+91-987-654-3210`
- Output: `+919876543210`

**Deduplication:**

Contact information is deduplicated:
- Phone numbers are normalized before comparison
- Emails are case-insensitive
- Duplicates are removed automatically

**Supported Formats:**
- Indian phone numbers: `+91XXXXXXXXXX`, `91XXXXXXXXXX`, `XXXXXXXXXX`
- International numbers with country code
- Email addresses in standard format

---

## Social Media Scraping

Search social media platforms for hiring posts and marketing pain signals.

**Endpoint:** `POST /api/advanced/social-media/search`

**Request Body:**
```json
{
  "keywords": ["hiring marketing", "marketing manager"],
  "platform": "nitter",
  "location": "India",
  "max_results": 10,
  "auto_classify": true,
  "filter_hiring": true
}
```

**Supported Platforms:**

### 1. LinkedIn Public Posts

**Platform:** `linkedin`

**Note:** LinkedIn actively blocks scrapers. This feature is unreliable and should be used sparingly. For production use, use LinkedIn's official API.

```bash
curl -X POST "http://localhost:8000/api/advanced/social-media/search" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["hiring marketing"],
    "platform": "linkedin",
    "max_results": 5
  }'
```

### 2. Twitter via Nitter

**Platform:** `nitter`

Uses Nitter (privacy-focused Twitter frontend) to access public tweets without authentication.

```bash
curl -X POST "http://localhost:8000/api/advanced/social-media/search" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["hiring marketing", "looking for marketer"],
    "platform": "nitter",
    "max_results": 10,
    "filter_hiring": true
  }'
```

**Response:**
```json
{
  "platform": "nitter",
  "keywords": ["hiring marketing"],
  "total_found": 10,
  "classified": 7,
  "results": [
    {
      "text": "We're hiring a marketing manager! Apply now...",
      "author": "@TechStartup",
      "url": "https://twitter.com/TechStartup/status/...",
      "timestamp": "2h ago",
      "source": "nitter",
      "status": "classified",
      "classification": {
        "lead_id": 124,
        "total_score": 70,
        "score_bucket": "warm"
      }
    }
  ]
}
```

**Important Notes:**
- Social media scraping should respect ToS
- Use official APIs for production
- Rate limit to avoid being blocked
- Nitter instances may be unavailable

---

## PDF Business Card Parsing

Upload multi-page PDFs (including scanned business cards) with OCR support.

**Endpoint:** `POST /api/ingest/ocr`

**Parameters:**
- `file` (required) - PDF or image file
- `use_ocr_for_pdf` (default: false) - Use OCR for scanned PDFs

**Standard PDF Extraction:**
```bash
curl -X POST "http://localhost:8000/api/ingest/ocr" \
  -F "file=@business_card.pdf"
```

**Scanned PDF (OCR Mode):**
```bash
curl -X POST "http://localhost:8000/api/ingest/ocr?use_ocr_for_pdf=true" \
  -F "file=@scanned_cards.pdf"
```

**Features:**
- Multi-page PDF support
- Fast text extraction (pypdf) for digital PDFs
- OCR mode (pdfplumber + Tesseract) for scanned PDFs
- Automatic contact extraction from each page
- Business card information detection

**Response:**
```json
{
  "extracted_text": "John Doe\nMarketing Manager\nAcme Corp\njohn@acme.com\n+919876543210",
  "detected_emails": ["john@acme.com"],
  "detected_phones": ["+919876543210"],
  "detected_names": ["John Doe", "Acme Corp"],
  "detected_company": "Acme Corp"
}
```

---

## RSS/Atom Feed Monitoring

Subscribe to RSS/Atom feeds to monitor job postings and company updates.

**Endpoint:** `POST /api/ingest/rss/fetch`

**Request Body:**
```json
{
  "feed_url": "https://company.com/jobs/feed.xml",
  "auto_classify": true,
  "max_items": 20
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ingest/rss/fetch" \
  -H "Content-Type: application/json" \
  -d '{
    "feed_url": "https://jobs.example.com/feed.xml",
    "auto_classify": true,
    "max_items": 10
  }'
```

**Response:**
```json
{
  "feed_title": "Example Corp Jobs",
  "feed_link": "https://jobs.example.com",
  "total_items": 15,
  "processed": 10,
  "auto_classified": true,
  "results": [
    {
      "title": "Marketing Manager - Mumbai",
      "link": "https://jobs.example.com/marketing-manager",
      "score": 75,
      "bucket": "warm",
      "lead_id": 125,
      "status": "classified"
    }
  ]
}
```

**Features:**
- Supports both RSS and Atom formats
- HTML tag cleaning from descriptions
- Automatic classification
- Duplicate detection
- Scheduled monitoring (see Scheduled Tasks)

---

## LinkedIn Post URL Ingestion

Manually paste a LinkedIn job post URL to extract and classify.

**Endpoint:** `POST /api/ingest/linkedin-post`

**Request Body:**
```json
{
  "post_url": "https://www.linkedin.com/jobs/view/12345",
  "company_name": "Acme Corp"
}
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ingest/linkedin-post" \
  -H "Content-Type: application/json" \
  -d '{
    "post_url": "https://www.linkedin.com/jobs/view/12345",
    "company_name": "Acme Corp"
  }'
```

**Features:**
- Works with publicly visible LinkedIn job posts
- Automatic company name extraction from page
- HTML parsing with multiple selectors
- Immediate classification

**Limitations:**
- Only works for public posts (no login required)
- LinkedIn frequently changes their HTML structure
- May not work for posts behind authentication
- Dynamic content may not be captured

---

## Bulk JSON Import

Import multiple signals at once via JSON for third-party tool integration.

**Endpoint:** `POST /api/ingest/json`

**Request Body:**
```json
[
  {
    "company_name": "Acme Corp",
    "signal_text": "Hiring marketing manager with 5 years experience...",
    "company_website": "https://acme.com",
    "source_type": "api",
    "metadata": {
      "source": "zapier",
      "campaign_id": "123"
    }
  },
  {
    "company_name": "TechStart Inc",
    "signal_text": "Looking for growth hacker to scale D2C brand...",
    "company_website": "https://techstart.io",
    "source_type": "webhook"
  }
]
```

**Example:**
```bash
curl -X POST "http://localhost:8000/api/ingest/json" \
  -H "Content-Type: application/json" \
  -d @signals.json
```

**Response:**
```json
{
  "total_processed": 2,
  "total_created": 2,
  "results": [
    {
      "company": "Acme Corp",
      "score": 80,
      "bucket": "red_hot",
      "lead_id": 126,
      "status": "created"
    }
  ]
}
```

**Use Cases:**
- Zapier integration
- Webhook receivers
- CRM imports
- Batch processing
- API integrations

---

## Scheduled Tasks

Automatically run data ingestion tasks on a schedule.

### Configuration

Scheduled tasks are configured in `backend/scheduled_tasks.py`:

**Default Schedule:**
- Job board API poll: Daily at 9:00 AM
- RSS feed monitor: Every 6 hours

### List Scheduled Jobs

**Endpoint:** `GET /api/advanced/scheduler/jobs`

```bash
curl "http://localhost:8000/api/advanced/scheduler/jobs"
```

**Response:**
```json
{
  "total_jobs": 2,
  "jobs": [
    {
      "id": "job_board_poll",
      "name": "Daily Job Board Poll",
      "next_run_time": "2025-01-16T09:00:00",
      "trigger": "cron[hour='9', minute='0']"
    },
    {
      "id": "rss_feed_monitor",
      "name": "RSS Feed Monitor",
      "next_run_time": "2025-01-15T18:00:00",
      "trigger": "interval[0:06:00:00]"
    }
  ]
}
```

### Manually Trigger a Job

**Endpoint:** `POST /api/advanced/scheduler/trigger/{job_id}`

```bash
curl -X POST "http://localhost:8000/api/advanced/scheduler/trigger/job_board_poll"
```

**Available Job IDs:**
- `job_board_poll` - Fetch jobs from Naukri and LinkedIn APIs
- `rss_feed_monitor` - Check configured RSS feeds

### Environment Variables

Configure job board API credentials for scheduled tasks:

```bash
# Naukri
export NAUKRI_API_KEY="your_key"
export NAUKRI_API_SECRET="your_secret"

# LinkedIn
export LINKEDIN_ACCESS_TOKEN="your_token"
```

---

## Best Practices

### Rate Limiting

- Wait 2-3 seconds between requests to the same domain
- Respect robots.txt
- Use scheduled tasks for periodic scraping
- Avoid hammering social media platforms

### API Credentials

- Store credentials in environment variables (`.env` file)
- Never commit API keys to version control
- Rotate credentials regularly
- Use separate credentials for development and production

### Data Quality

- Review classified leads regularly
- Adjust ICP profiles based on results
- Remove duplicates manually if needed
- Update contact information when outdated

### ToS Compliance

- Use official APIs whenever available
- Only scrape publicly visible content
- Follow robots.txt directives
- Rate limit all scraping activities
- For LinkedIn/Twitter, prefer official APIs over scraping

### Performance

- Use bulk import for large datasets
- Schedule heavy operations during off-peak hours
- Monitor database size (consider PostgreSQL for production)
- Clean up old/irrelevant leads periodically

---

## Troubleshooting

### "PDF support not available"

Install pypdf:
```bash
pip install pypdf
```

### "feedparser not available"

Install feedparser:
```bash
pip install feedparser
```

### "phonenumbers not available"

Install phonenumbers:
```bash
pip install phonenumbers
```

### LinkedIn scraping not working

LinkedIn actively blocks scrapers. Solutions:
1. Use the official LinkedIn API
2. Use the manual LinkedIn post URL ingestion instead
3. Copy-paste job post text manually

### RSS feed parsing errors

Check if the feed URL is correct and accessible:
```bash
curl "https://feed-url.com/feed.xml"
```

### Scheduler not running

Check logs for errors:
```bash
# Check backend logs
tail -f backend.log
```

Verify scheduler is started in main.py lifespan function.

---

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/ingest/jobs/csv` | POST | Upload CSV of jobs |
| `/api/ingest/json` | POST | Bulk JSON import |
| `/api/ingest/linkedin-post` | POST | Ingest LinkedIn post URL |
| `/api/ingest/rss/fetch` | POST | Fetch RSS feed |
| `/api/ingest/ocr` | POST | OCR text extraction |
| `/api/advanced/crawl/website` | POST | Depth-limited crawler |
| `/api/advanced/social-media/search` | POST | Social media search |
| `/api/advanced/job-boards/api-search` | POST | Job board API search |
| `/api/advanced/scheduler/jobs` | GET | List scheduled jobs |
| `/api/advanced/scheduler/trigger/{job_id}` | POST | Trigger job manually |

---

## Next Steps

1. Set up API credentials for job boards
2. Configure RSS feeds to monitor
3. Adjust ICP profiles for better targeting
4. Review and classify generated leads
5. Export leads to your CRM

For more information, see:
- [README.md](README.md) - System overview
- [SCRAPING_GUIDE.md](SCRAPING_GUIDE.md) - Web scraping details
- [QUICKSTART.md](QUICKSTART.md) - Setup instructions
