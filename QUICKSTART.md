# 🚀 Raptorflow Lead Engine - Quick Start

**The overkill sales machine.** Find people with marketing pain, understand their context, close them.

Runs 100% local on Ollama (Gemma 3 1B/4B). No data selling. India-focused. <20 person teams.

---

## 5-Minute Setup

### What You Need

1. **Python 3.9+** – Download from python.org
2. **Ollama** – Download from https://ollama.ai
3. **Git** (optional, but recommended)

### Step 1: Start Ollama

```bash
ollama serve
```

Leave this running in a terminal. (It runs in the background after first start.)

### Step 2: Start the Backend

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
- Install FastAPI, SQLAlchemy, Tesseract, etc.
- Check Ollama and pull Gemma 3 1B (~800MB) and 4B (~3.3GB) if needed
- Start the API on http://localhost:8000

**First run may take 5-10 minutes** (downloading models). Subsequent runs are instant.

### Step 3: Start the Frontend

```bash
# In a new terminal, from the root
npm install
npm run dev
```

Open http://localhost:3000

---

## What You Can Do Right Now

### 1. Create an ICP Profile (Tell it who to hunt)

Open http://localhost:3000/icp (coming soon) or use the API:

```bash
curl -X POST http://localhost:8000/api/icp/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Solo Founder Ecommerce",
    "size_buckets": ["1"],
    "industries": ["ecommerce", "d2c"],
    "locations": ["india"],
    "hiring_keywords": ["marketing manager", "growth hacker"],
    "pain_keywords": ["lead generation", "scaling ads", "no marketing team"]
  }'
```

Or use a pre-built template:

```bash
curl -X POST http://localhost:8000/api/icp/templates/solo-founder
curl -X POST http://localhost:8000/api/icp/templates/small-d2c
```

### 2. Feed It a Signal (Job post, website text, whatever)

```bash
curl -X POST http://localhost:8000/api/classify/signal \
  -H "Content-Type: application/json" \
  -d '{
    "signal_text": "Hiring: Growth Marketer. We are a D2C skincare brand doing $100K/mo, need someone to scale our ad campaigns and own email. No marketing team currently.",
    "source_type": "job_post",
    "company_name": "SkinCo Brands",
    "company_website": "https://skinco.com"
  }'
```

**Response:**

```json
{
  "icp_match": true,
  "total_score": 87.5,
  "score_bucket": "red_hot",
  "company_id": 1,
  "lead_id": 1,
  "classification": {
    "score_fit": 45,
    "score_pain": 40,
    "score_data_quality": 2.5,
    "role_type": "first_marketer",
    "pain_tags": ["lead_gen", "scaling_ads", "no_system"],
    "situation": "D2C skincare, $100K/mo, no marketing team",
    "problem": "Can't scale ads, no strategy, manual everything",
    "implication": "Will churn customers, ad costs rising, won't hit targets",
    "need_payoff": "Systematic approach to campaigns + email",
    "economic_buyer_guess": "founder",
    "key_pain": "Spending on ads but no system to measure/improve",
    "chaos_flags": ["chaos_culture", "scaling_desperation"],
    "silver_bullet_phrases": ["no marketing team", "need to scale", "own all of growth"]
  }
}
```

**What does this mean?**

- **Score 87.5** = Red Hot 🔥 (This is a real lead.)
- **ICP Match** = Yes, they fit your ideal customer.
- **Role Type** = "First marketer" (They have no one yet.)
- **Pain Tags** = Lead gen, scaling, no system.
- **Chaos Flags** = They're chaotic + desperate (perfect for Raptorflow angle).
- **Key Pain** = "Spending on ads but no system."

If the score was > 70, Raptorflow queues up a background task to use the 4B model to generate a rich dossier (snapshot, why they have pain, uncomfortable truth, reframe, best angle).

### 3. Drop a Business Card (OCR)

```bash
curl -X POST http://localhost:8000/api/ingest/ocr-and-classify \
  -F "file=@my_business_card.jpg" \
  -F "company_name=My Startup"
```

OCR extracts text → 1B classifier scores it → Creates a lead → If hot, 4B generates dossier.

### 4. View Your Leads

```bash
curl http://localhost:8000/api/leads?score_min=60&score_bucket=red_hot&limit=20
```

Returns leads sorted by score, hottest first.

### 5. Update a Lead

```bash
curl -X PATCH http://localhost:8000/api/leads/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "contacted"}'
```

Valid statuses: `new`, `contacted`, `qualified`, `pitched`, `trial`, `won`, `lost`, `parked`.

---

## API Endpoints (Quick Reference)

### ICP Whiteboard

- `POST /api/icp/` – Create profile
- `GET /api/icp/` – List all
- `PUT /api/icp/{id}` – Update
- `DELETE /api/icp/{id}` – Delete
- `POST /api/icp/templates/solo-founder` – Pre-built template

### Classification

- `POST /api/classify/signal` – Classify a signal (1B model)

### Leads

- `GET /api/leads/` – List (with filters)
- `GET /api/leads/{id}` – Get one
- `PATCH /api/leads/{id}/status` – Update status
- `PATCH /api/leads/{id}/notes` – Update notes
- `DELETE /api/leads/{id}` – Delete

### Ingest

- `POST /api/ingest/ocr` – OCR extraction only
- `POST /api/ingest/ocr-and-classify` – OCR + classify
- `POST /api/ingest/csv` – Bulk CSV ingest

---

## How the Scoring Works

Every signal gets scored 0-100:

```
Total Score = ICP Fit (0-50) + Marketing Pain (0-40) + Data Quality (0-10)
```

**ICP Fit (0-50)**
- Size match: +20
- Region = India: +10
- Industry in your target list: +20

**Marketing Pain (0-40)**
- Explicit "hiring marketer" job post: +30
- Multiple marketing roles: +10
- "No marketing team" / "need help scaling": +10

**Data Quality (0-10)**
- Email + phone + website: +5-10
- Partial data: +2-5
- Just text: +0-2

**Buckets:**
- **Red Hot** (80-100) → Call them today
- **Warm** (60-79) → This week
- **Nurture** (40-59) → Watch them
- **Parked** (<40) → Not a fit

---

## What Happens With High Scores?

If a lead scores > 70, a background task fires up the 4B model to generate:

- **Snapshot** – Who are they in 40 words?
- **Why pain?** – 3 bullets on what's broken
- **Uncomfortable truth** – What happens if they don't fix it
- **Reframe** – Flip their thinking
- **Best angle** – 3 ways to approach
- **Challenger insight** – Lead with this

Check the lead detail later and you'll see the dossier.

---

## Next: The Frontend

The React app is coming. It will have:

- **Lead List** – Sortable by score, status, ICP, source
- **ICP Whiteboard** – Visual builder (no coding needed)
- **OCR Uploader** – Drag-drop cards/images
- **Lead Detail** – Full context + dossier
- **Dashboard** – Red hot count, pipeline view
- **Activities** – Call logs, notes, tasks

---

## Troubleshooting

### "Ollama not responding"

Make sure Ollama is running:

```bash
ollama serve
```

(It might take a moment to start. Check http://localhost:11434/api/tags in browser.)

### "Models not found"

Pull them manually:

```bash
ollama pull gemma3:1b
ollama pull gemma3:4b
```

### "Database locked"

SQLite has concurrency limits. For now, make sure only one API instance is running.

### "Classification is slow"

First call to a model loads it into RAM (~30s). Subsequent calls are 2-5s.

If you have < 4GB free RAM, the 4B model might swap to disk (very slow).

### "Database file corrupted"

Delete it and restart:

```bash
rm backend/raptorflow_leads.db
```

---

## File Structure

```
Illegal_sales_machine/
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── database.py             # SQLAlchemy models
│   ├── config.py               # Settings
│   ├── ollama_wrapper.py       # 1B/4B integration
│   ├── routers/
│   │   ├── icp.py              # ICP CRUD
│   │   ├── leads.py            # Lead CRUD
│   │   ├── classify.py         # Classification (1B + 4B)
│   │   └── ingest.py           # OCR + CSV ingest
│   ├── requirements.txt
│   ├── .env
│   ├── run.sh / run.bat         # Start script
│   └── README.md
├── app/                         # Next.js app (React)
├── components/                  # React components
├── lib/                         # Utilities
├── package.json
└── QUICKSTART.md                # This file
```

---

## What's Working Right Now (Phase 0-1)

✅ FastAPI backend with SQLite
✅ Ollama 1B/4B integration
✅ ICP profiles (CRUD)
✅ Signal classification (1B fast, optional 4B dossier)
✅ OCR extraction (images)
✅ Contact info extraction (emails, phones, names)
✅ Lead scoring + bucketing
✅ SPIN/MEDDIC fields
✅ Chaos culture detection

---

## What's Coming (Phase 2-4)

🔜 React frontend (lead list, ICP builder, OCR uploader)
🔜 Job board collectors (Naukri, Foundit, etc.)
🔜 Website crawler
🔜 Real-time alerts
🔜 CRM pipeline view
🔜 Raptorflow ADAPT integration

---

## The Philosophy

This is **not** a generic lead tool.

- **Signal first** – Only processes real "hiring for marketing" signals.
- **Context heavy** – Dossier tells you *why* they need you.
- **Scoring smart** – Separates red hot from noise.
- **Local only** – Gemma 3 runs on your machine. No data sent to anyone.
- **Founder-minded** – Built with SPIN/MEDDIC/Challenger Sale heuristics baked in.

You're not selling leads. You're finding people who are already in pain and giving them context so *they* come to you.

---

## Quick Test Script

Want to test without hitting the API manually?

```bash
# Backend must be running
python backend/test_classify.py
```

(Coming soon – will create sample signals and show you scoring.)

---

## Questions?

- Check `backend/README.md` for detailed API docs
- Check `ARCHITECTURE.md` for design decisions (coming soon)
- File an issue on GitHub

---

**Let's hunt some marketing pain.** 🔥

Start with: `cd backend && run.bat` (or `./run.sh`)
