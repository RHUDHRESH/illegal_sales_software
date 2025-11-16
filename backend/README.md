# Raptorflow Lead Engine - Backend

**Overkill lead discovery + enrichment powered by local Ollama.**

> Hunts people with marketing pain, extracts rich context, scores aggressively.

---

## What's in here?

- **FastAPI** backend for lead classification
- **SQLite** database for companies, contacts, signals, and leads
- **Gemma 3 1B/4B** integration via Ollama for intelligent classification
- **OCR** support (images/PDFs) via Tesseract
- **ICP Whiteboard** API to define ideal customer profiles

---

## Quick Start

### Prerequisites

1. **Python 3.9+**
2. **Ollama** (download from https://ollama.ai)
   - Start it: `ollama serve`
   - (Don't close this terminal; it runs in background after first start)

### Setup

```bash
cd backend

# Windows
run.bat

# Mac/Linux
chmod +x run.sh
./run.sh
```

This will:
- Create a Python virtual environment
- Install dependencies
- Check Ollama + pull Gemma 3 1B and 4B models
- Start the FastAPI server

### Models

First run will pull models from Ollama (takes ~5-10 min on first download):
- **gemma3:1b** (~800MB) – Fast classifier for routing
- **gemma3:4b** (~3.3GB) – Rich context generation for hot leads

After first pull, they're cached locally. Lightning fast on subsequent runs.

---

## API Endpoints

### ICP Management

```
POST   /api/icp/                    Create ICP profile
GET    /api/icp/                    List all ICPs
GET    /api/icp/{id}                Get specific ICP
PUT    /api/icp/{id}                Update ICP
DELETE /api/icp/{id}                Delete ICP

POST   /api/icp/templates/solo-founder     Pre-built: Solo founder
POST   /api/icp/templates/small-d2c        Pre-built: Small D2C
```

### Leads

```
GET    /api/leads/                                  List leads (with filtering)
GET    /api/leads/{id}                             Get specific lead
PATCH  /api/leads/{id}/status                      Update status
PATCH  /api/leads/{id}/notes                       Update notes
DELETE /api/leads/{id}                             Delete lead
GET    /api/leads/score-distribution/bucket-counts Lead counts by score
```

### Classification

```
POST   /api/classify/signal                        Classify a single signal (1B)
POST   /api/classify/signal/batch                  Batch classify signals
```

### Ingest

```
POST   /api/ingest/ocr                             OCR an image/PDF
POST   /api/ingest/ocr-and-classify                OCR + immediate classification
POST   /api/ingest/csv                             Bulk ingest from CSV
```

---

## How It Works

### Phase 1 – Fast Classification (Gemma 3 1B)

When you feed in a signal (job posting, website text, manual input, OCR'd card):

1. **1B model runs instantly** (~2-5 seconds):
   - ICP match? (Yes/No)
   - Size bucket?
   - Role type (first marketer, agency replacement, etc)?
   - Marketing pain score (0-40)
   - Tags (first_marketer_hell, chaos_culture, etc)
   - SPIN fields (situation, problem, implication, need_payoff)
   - MEDDIC-lite (economic buyer, key pain, chaos flags)

2. **Compute total score** (0-100):
   - ICP fit (0-50) + Pain (0-40) + Data quality (0-10)

3. **Bucket the lead**:
   - **Red Hot** (80-100) → Immediate attention
   - **Warm** (60-79) → This week
   - **Nurture** (40-59) → Keep watching
   - **Parked** (<40) → Not a fit

### Phase 2 – Deep Context (Gemma 3 4B, optional)

If a lead scores > 70, a background task fires up the 4B model to generate:

- **Snapshot**: Who are they in 40 words?
- **Why pain?**: 3 bullets on their marketing struggle
- **Uncomfortable truth**: What happens if they don't fix it
- **Reframe**: Flip their thinking in 1 sentence
- **Best angle**: 3 ways to approach them
- **Challenger insight**: The one thing to lead with

All stored in the lead record for later reference.

---

## Usage Examples

### 1. Create an ICP Profile (Whiteboard)

```bash
curl -X POST http://localhost:8000/api/icp/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Solo Founder - D2C",
    "description": "Solo founder running D2C brand, hiring first marketer",
    "size_buckets": ["1"],
    "industries": ["ecommerce", "d2c"],
    "locations": ["india"],
    "hiring_keywords": ["marketing manager", "growth hacker"],
    "pain_keywords": ["lead generation", "scaling ads"]
  }'
```

### 2. Classify a Manual Signal

```bash
curl -X POST http://localhost:8000/api/classify/signal \
  -H "Content-Type: application/json" \
  -d '{
    "signal_text": "Looking to hire a growth marketer. We run an eCommerce brand with $50K MRR and no marketing system. Help!",
    "source_type": "manual",
    "company_name": "MyD2C Brand",
    "company_website": "https://mydc.com"
  }'
```

Returns:

```json
{
  "icp_match": true,
  "total_score": 82.5,
  "score_bucket": "red_hot",
  "classification": {
    "score_fit": 45,
    "score_pain": 35,
    "score_data_quality": 2.5,
    "role_type": "first_marketer",
    "pain_tags": ["lead_gen", "scaling_ads", "no_system"],
    ...
  },
  "company_id": 1,
  "lead_id": 1
}
```

### 3. Drop a Business Card Image

```bash
curl -X POST http://localhost:8000/api/ingest/ocr-and-classify \
  -F "file=@business_card.jpg" \
  -F "company_name=My Startup"
```

OCR extracts text → 1B classifies → Creates lead → If hot, queues 4B dossier.

### 4. List Leads (Sorted by Score)

```bash
curl http://localhost:8000/api/leads?score_min=60&score_bucket=red_hot
```

Returns hottest leads first, with all context + scores.

---

## Database Schema

Key tables:

- **icp_profiles** – Your targeting definitions
- **companies** – Deduplicated company records
- **contacts** – Individual people
- **signals** – Raw data (job posts, site snippets, OCR text)
- **leads** – Scored + classified signals ready for outreach
- **activities** – Call logs, notes, tasks per lead

---

## Configuration

Edit `backend/.env`:

```
OLLAMA_BASE_URL=http://localhost:11434      # Ollama server
OLLAMA_MODEL_1B=gemma3:1b                   # Fast model
OLLAMA_MODEL_4B=gemma3:4b                   # Rich model
CLASSIFIER_SCORE_THRESHOLD=70               # When to call 4B
DATABASE_URL=sqlite:///./raptorflow_leads.db
```

---

## What Next?

1. **Create 2-3 ICP profiles** (solo founder, small D2C, etc)
2. **Feed it real signals** (job posts, website text, cards)
3. **Watch the scores** (red hot = immediate attention)
4. **Integrate into Raptorflow CRM** (frontend coming next)

---

## Troubleshooting

### "Ollama not running"

Make sure Ollama is running:

```bash
ollama serve
```

(It will stay in the terminal. Open another terminal for the backend.)

### "Model not found"

If `gemma3:1b` or `gemma3:4b` don't exist:

```bash
ollama pull gemma3:1b
ollama pull gemma3:4b
```

### "Database locked"

SQLite can have concurrency issues. For production, migrate to PostgreSQL.

### Slow response times?

- First request to a model is slow (loading into RAM)
- Subsequent requests are much faster
- Check available RAM (4B needs ~4GB, 1B ~500MB)

---

## Next Steps

1. Frontend (React) – Lead list, ICP builder, OCR uploader
2. Job board collectors – Automatically pull job postings
3. Website crawler – Extract signals from company sites
4. Export to CRM – Sync classified leads into Raptorflow dashboard
5. Alerts – Real-time push when hot lead appears

---

Questions? Issues? File a GitHub issue or check the docs.

**Let's hunt some marketing pain.** 🔥
