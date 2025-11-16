# 🚀 Raptorflow Lead Engine

**The overkill sales machine.**

Hunt people with marketing pain signals. Extract rich context. Score ruthlessly. Close them.

Runs 100% local on Ollama (Gemma 3 1B/4B). No data selling. India-focused. <20 person teams.

---

## What This Does

You're selling **Raptorflow** – a cohort-based marketing platform that helps small teams do better marketing than they could with a full-time marketer, for 3.5K/month instead of 50K/month.

This system finds the exact people who need you:

- **People hiring for marketers** (clearest pain signal)
- **Founders running small D2C/SaaS** (minimal team, high growth ambition)
- **Service businesses** (selling their time, trying to scale)
- **Young creators** (growth mindset, no budget for agencies)

For each lead, it:

1. **Classifies** – Is this person actually in marketing pain?
2. **Scores** – How urgent is their pain? (0-100, bucketed)
3. **Contextualizes** – Why do they need help? (Rich dossier for your research)
4. **Prepares** – Gives you the uncomfortable truth to lead with

All **local**. All **private**. No subscriptions, no limits.

---

## Quick Start

### Prerequisites

1. **Python 3.9+**
2. **Node.js 18+** (for React frontend)
3. **Ollama** (download from https://ollama.ai)

### 5-Minute Setup

1. **Start Ollama:**

```bash
ollama serve
```

Leave this running.

2. **Start the Backend:**

```bash
cd backend
# Windows
run.bat

# Mac/Linux
chmod +x run.sh
./run.sh
```

This pulls Gemma 3 1B (~800MB) and 4B (~3.3GB) on first run, then starts the API.

3. **Start the Frontend:**

```bash
# New terminal, from root
npm install
npm run dev
```

Open http://localhost:3000

That's it. You're live.

---

## How It Works

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│ React Frontend (Next.js) - http://localhost:3000         │
│ - Dashboard: Lead overview by score bucket              │
│ - Leads List: Filterable, sortable, scorable             │
│ - ICP Whiteboard: Define your ideal customer            │
│ - OCR Uploader: Drag-drop cards/images                  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       │ HTTP/JSON
                       │
┌──────────────────────▼──────────────────────────────────┐
│ FastAPI Backend - http://localhost:8000/docs             │
│ - ICP CRUD                                              │
│ - Signal Classification (1B fast routing)               │
│ - Lead Scoring & Bucketing                              │
│ - OCR Ingest (Tesseract)                                │
│ - Contact Info Extraction                               │
│ - Optional 4B Dossier Generation (background task)      │
└──────────────────────┬──────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
      SQLite      Ollama (1B)    Ollama (4B)
      Database    Fast Classify  Deep Context
```

### The Classification Pipeline

**Phase 1 – Fast Classification (Gemma 3 1B, ~2-5 seconds)**

When you feed a signal (job posting, website text, OCR'd card), 1B model:

- Checks **ICP fit** (size, industry, region)
- Scores **marketing pain** (0-40)
- Extracts **SPIN fields** (situation, problem, implication, need_payoff)
- Identifies **MEDDIC-lite** (economic buyer, key pain, chaos flags)
- Tags **chaos culture**, **silver bullet phrases**, **hiring signals**

Computes **total score** (0-100):

- ICP fit (0-50) + Marketing pain (0-40) + Data quality (0-10)

**Buckets the lead:**

- **Red Hot** (80-100) – Call them today 🔥
- **Warm** (60-79) – This week 🔆
- **Nurture** (40-59) – Keep watching 👀
- **Parked** (<40) – Not a fit 📦

**Phase 2 – Deep Context (Gemma 3 4B, ~10-20 seconds)**

If score > 70, a background task generates:

- **Snapshot** – Who they are in 40 words
- **Why pain?** – 3 bullets on their struggle
- **Uncomfortable truth** – What happens if they don't fix it
- **Reframe** – Flip their thinking in 1 sentence
- **Best angle** – 3 ways to approach them
- **Challenger insight** – Lead with this

All stored in the lead record. Reference later during outreach.

---

## Core Features

### 1. ICP Whiteboard

Define your ideal customer profile without writing code:

- **Company size** – Select: 1, 2-5, 6-10, 11-20
- **Industries** – ecommerce, d2c, saas, consulting, freelance, agency, etc.
- **Locations** – India (extensible)
- **Hiring keywords** – "marketing manager", "growth hacker", etc.
- **Pain keywords** – "lead generation", "scaling ads", etc.
- **Channel preferences** – Instagram, LinkedIn, email, etc.

Save multiple ICPs and toggle between them. Classifier uses these for scoring.

### 2. Signal Ingest

Feed the machine raw signals:

**Manual Input** – Paste job post text, website snippet, or free-form description.

```bash
curl -X POST http://localhost:8000/api/classify/signal \
  -H "Content-Type: application/json" \
  -d '{
    "signal_text": "Hiring: Growth Marketer...",
    "source_type": "job_post",
    "company_name": "MyBrand",
    "company_website": "https://mybrand.com"
  }'
```

**OCR Ingest** – Drag-drop a business card, screenshot, or image. Tesseract extracts text → 1B classifies → Lead created.

```bash
curl -X POST http://localhost:8000/api/ingest/ocr-and-classify \
  -F "file=@card.jpg" \
  -F "company_name=MyStartup"
```

**CSV Bulk** – Upload a CSV with `company_name`, `signal_text` columns. Batch processed.

### 3. Lead Management

**List View** – All leads sorted by score (hottest first).

- Filter by score range, bucket, status
- See pain tags, ICP match, score breakdown
- Click to view full context

**Lead Detail** – Deep dive on a single lead:

- Company info + website
- Extracted contact info (emails, phones, WhatsApp)
- All signals (job posts, site snippets, OCR text)
- SPIN/MEDDIC fields
- Generated dossier (if score > 70)
- Activity timeline (notes, calls, tasks)

**Status Tracking** – Move leads through pipeline:

- **new** → **contacted** → **qualified** → **pitched** → **trial** → **won** / **lost** / **parked**

### 4. Dashboard

Live overview:

- **Red Hot** count (80-100) – How many ready to call?
- **Warm** count (60-79) – Pipeline for this week?
- **Nurture** (40-59) + **Parked** (<40) – Long-tail opportunities
- Percentage distribution
- Quick stats: total leads, action required, conversion potential

---

## API Reference

### Base URL

http://localhost:8000

### ICP Management

```
POST   /api/icp/                              Create ICP profile
GET    /api/icp/                              List all ICPs
GET    /api/icp/{id}                          Get specific ICP
PUT    /api/icp/{id}                          Update ICP
DELETE /api/icp/{id}                          Delete ICP
POST   /api/icp/templates/solo-founder        Pre-built: Solo founder
POST   /api/icp/templates/small-d2c           Pre-built: Small D2C
```

### Lead Management

```
GET    /api/leads/                                    List leads (with filtering)
GET    /api/leads/{id}                               Get specific lead
PATCH  /api/leads/{id}/status                        Update status (new/contacted/won/lost/etc)
PATCH  /api/leads/{id}/notes                         Add notes
DELETE /api/leads/{id}                               Delete lead
GET    /api/leads/score-distribution/bucket-counts   Lead counts by bucket
```

### Classification

```
POST   /api/classify/signal                          Classify a single signal
POST   /api/classify/signal/batch                    Batch classify signals
```

### Ingest

```
POST   /api/ingest/ocr                               OCR text extraction only
POST   /api/ingest/ocr-and-classify                  OCR + immediate classification
POST   /api/ingest/csv                               Bulk CSV ingest
```

### Health

```
GET    /                                             API status
GET    /health                                       Full health check
```

---

## Example Workflow

### 1. Create an ICP Profile

```bash
curl -X POST http://localhost:8000/api/icp/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Solo Founder D2C",
    "description": "Solo founder or 2-person team running D2C brand",
    "size_buckets": ["1", "2-5"],
    "industries": ["ecommerce", "d2c"],
    "locations": ["india"],
    "hiring_keywords": ["marketing manager", "growth hacker", "performance marketer"],
    "pain_keywords": ["lead generation", "scaling", "no marketing team"],
    "channel_preferences": ["instagram", "facebook"]
  }'
```

### 2. Feed It a Signal

```bash
curl -X POST http://localhost:8000/api/classify/signal \
  -H "Content-Type: application/json" \
  -d '{
    "signal_text": "Hiring Growth Marketer. We are a 3-person D2C skincare brand doing $50K MRR. Looking for someone to own our Instagram and email. No marketing team currently.",
    "source_type": "job_post",
    "company_name": "SkinLab",
    "company_website": "https://skinlab.in"
  }'
```

**Response:**

```json
{
  "icp_match": true,
  "total_score": 82.5,
  "score_bucket": "red_hot",
  "company_id": 1,
  "lead_id": 1,
  "classification": {
    "score_fit": 45,
    "score_pain": 35,
    "score_data_quality": 2.5,
    "role_type": "first_marketer",
    "pain_tags": ["lead_gen", "scaling", "no_system"],
    "situation": "3-person D2C skincare, $50K MRR, no marketing team",
    "problem": "Instagram and email completely manual, no strategy",
    "implication": "Can't scale brand, customer acquisition too slow",
    "need_payoff": "Systematic content + email flow for growth",
    "economic_buyer_guess": "founder",
    "chaos_flags": ["chaos_culture", "diy", "first_hire"],
    "silver_bullet_phrases": ["no marketing team", "own our", "first marketer"]
  }
}
```

✅ **Red Hot lead!** ICP match + clear pain + first marketer = call them.

### 3. Later: View the Dossier

After 4B dossier generation completes (background task):

```bash
curl http://localhost:8000/api/leads/1
```

The `context_dossier`, `challenger_insight`, and `reframe_suggestion` fields will be populated.

### 4. Drop a Business Card

```bash
curl -X POST http://localhost:8000/api/ingest/ocr-and-classify \
  -F "file=@john_card.jpg" \
  -F "company_name=MyStartup"
```

OCR extracts text → Detects emails/phones/names → 1B classifies → Lead stored with score + bucket.

---

## Scoring Deep Dive

### Why This Scoring?

Not all leads are created equal. Raptorflow is niche:

- **Not for big enterprises** (they have big budgets for agencies)
- **Perfect for small teams** (DIY, chaos, need systems)
- **Perfect for founders** (growth mindset, lean, willing to experiment)

Scoring reflects this:

**ICP Fit (0-50)**

- Size match (1, 2-5, 6-10, 11-20): +20 points
- Region = India: +10 points
- Industry in target list: +20 points
- Total: max 50

**Marketing Pain (0-40)**

- Job post with "marketing manager" or "growth" in title/desc: +30 points
- Keywords like "no marketing team", "need help scaling": +10 points
- Multiple marketing roles posted recently: +10 points
- Total: max 40

**Data Quality (0-10)**

- Email + phone + website: +10 points
- Email + phone or email + website: +5-7 points
- Just text: +1-3 points
- Total: max 10

**Bucket Logic**

- 80-100 = **Red Hot** (urgent + good fit + high pain)
- 60-79 = **Warm** (good fit or high pain, but not both)
- 40-59 = **Nurture** (some signals, but weak)
- <40 = **Parked** (not a fit for Raptorflow)

### Example Scoring

**"Hiring: Growth Marketer. Solo founder, D2C brand, $50K MRR, India."**

- ICP fit: 45 (size 1: +20, region India: +10, industry d2c: +20, "growth" keyword: +5 bonus)
- Pain: 35 (explicit hire: +30, "no team" implied: +5)
- Data quality: 2.5 (just text, no email/phone yet)
- **Total: 82.5 → Red Hot**

**"We're looking for someone to help with our marketing. Remote, flexible hours."**

- ICP fit: 10 (vague about size/industry/region)
- Pain: 5 (mentions "help marketing" but not specific)
- Data quality: 0 (no contact info)
- **Total: 15 → Parked**

---

## Architecture Notes

### Why Gemma 3 1B + 4B?

**1B is fast** (~2-5 seconds, 800MB model):

- Perfect for routing, tagging, extracting fields
- Runs on low-spec machines
- Runs locally, no API calls

**4B is rich** (~10-20 seconds, 3.3GB model):

- Better narrative, context generation
- Dossier storytelling
- Only called for hot leads (score > 70)

Together, they're lean + smart. Not overkill on resources, maximum on insights.

### Why SQLite (for now)?

**Pros:**

- Zero setup
- Portable (single `.db` file)
- Good for prototyping

**Cons:**

- Concurrency limits
- No good for multiple simultaneous users

**Plan:** Migrate to PostgreSQL later when you need multi-user scale.

### Why No Celery/Redis Yet?

**For Phase 0-1:** Background tasks are simple. Python's `asyncio` handles dossier generation.

**For Phase 2+:** As you add job board collectors running on schedule, you'll want proper task queue. Then add Celery + Redis.

---

## Next Steps (Roadmap)

### Phase 2 – Collectors

- Job board scraper (Naukri, Foundit, LinkedIn Jobs)
- Website crawler (extract job postings from company sites)
- Hourly/daily refresh

### Phase 3 – Advanced Matching

- Funding + hiring = high urgency
- Multiple marketing roles = team building
- Re-posted roles = desperation
- Content inconsistency = no system

### Phase 4 – CRM Integration

- Export to CRM
- Outreach templates
- Multi-touch sequences
- Win/loss tracking

### Phase 5 – Raptorflow Integrate

- When lead becomes customer, pull context into ADAPT
- Auto-generate cohorts based on lead profile
- Suggest first assets

---

## Troubleshooting

### "Ollama not responding"

```bash
# Check Ollama is running
ollama serve

# In another terminal, test
curl http://localhost:11434/api/tags
```

### "Models not found"

```bash
ollama pull gemma3:1b
ollama pull gemma3:4b
```

### "Classification is slow"

First call loads model (~30s). Subsequent calls are 2-5s.

If you have <4GB free RAM, 4B model will swap to disk (very slow).

### "Database locked"

SQLite has concurrency limits. Make sure only one API is running.

### "OCR not working"

Tesseract needs to be installed:

- **Mac:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`
- **Windows:** Download from https://github.com/UB-Mannheim/tesseract/wiki

### "Backend won't start"

Check Python version:

```bash
python --version  # Should be 3.9+
```

Check port 8000 isn't in use:

```bash
# Linux/Mac
lsof -i :8000

# Windows
netstat -ano | findstr :8000
```

---

## File Structure

```
Illegal_sales_machine/
├── backend/                     # FastAPI app
│   ├── main.py                 # Entry point
│   ├── database.py             # SQLAlchemy models
│   ├── config.py               # Settings
│   ├── ollama_wrapper.py       # 1B/4B integration
│   ├── routers/
│   │   ├── icp.py              # ICP CRUD
│   │   ├── leads.py            # Lead CRUD
│   │   ├── classify.py         # 1B/4B classification
│   │   └── ingest.py           # OCR + CSV
│   ├── requirements.txt         # Python deps
│   ├── .env                    # Config
│   ├── run.sh / run.bat        # Start script
│   └── README.md               # Backend docs
├── app/                         # Next.js pages
├── components/                  # React components
│   ├── dashboard.tsx           # Lead overview
│   ├── leads-list.tsx          # Lead list + filtering
│   ├── icp-builder.tsx         # ICP CRUD UI
│   ├── ocr-uploader.tsx        # OCR + classify
│   └── ui/                     # Radix UI components
├── lib/                         # Utilities + store
├── public/                      # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.js
├── QUICKSTART.md               # Quick start guide
├── README.md                   # This file
└── .gitignore
```

---

## Philosophy

**This is not a generic lead tool.**

- **Signal first** – Only processes real "hiring for marketing" signals.
- **Context heavy** – Dossier tells you *why* they need you.
- **Scoring smart** – Separates red hot from noise.
- **Local only** – Gemma 3 runs on your machine. No data sent anywhere.
- **Founder-minded** – Built with SPIN/MEDDIC/Challenger Sale heuristics.
- **High signal-to-noise** – Better to have 5 red hot leads than 100 maybes.

You're not selling leads. You're finding people already in pain and giving them context so *they* come to you.

---

## Support

- **Documentation** – See `QUICKSTART.md` for 5-minute setup
- **API Docs** – http://localhost:8000/docs (SwaggerUI, auto-generated)
- **Backend Docs** – `backend/README.md`
- **Issues** – File on GitHub

---

## License

This is an internal tool for Raptorflow. Built for your specific use case.

---

**Let's hunt some marketing pain.** 🔥

Start with:

```bash
cd backend && run.bat  # (or ./run.sh)
```

Then:

```bash
npm run dev  # (new terminal)
```

Then:

http://localhost:3000
