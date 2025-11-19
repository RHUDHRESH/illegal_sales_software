# Advanced Scoring Heuristics and Lead Quality Detection

This guide documents the comprehensive scoring heuristics system that enhances lead classification with intelligent quality detection, pattern recognition, and automated lead management.

## Table of Contents

1. [Overview](#overview)
2. [Ghost Job Detection](#ghost-job-detection)
3. [First Marketer Detection](#first-marketer-detection)
4. [Founder vs HR Tone Classification](#founder-vs-hr-tone-classification)
5. [Silver-Bullet Seeker Detection](#silver-bullet-seeker-detection)
6. [Spam Detection](#spam-detection)
7. [Industry-Specific Scoring](#industry-specific-scoring)
8. [Funding Event Signals](#funding-event-signals)
9. [Customizable Scoring Weights](#customizable-scoring-weights)
10. [Manual Score Overrides](#manual-score-overrides)
11. [Auto-Park Functionality](#auto-park-functionality)
12. [Score Explanation](#score-explanation)
13. [API Reference](#api-reference)
14. [Configuration](#configuration)

---

## Overview

The scoring heuristics system provides **intelligent quality detection** beyond basic AI classification. It applies pattern recognition, linguistic analysis, and temporal signals to:

- **Filter out low-quality signals** (ghost jobs, spam)
- **Boost high-value opportunities** (first marketer roles, founder-written posts, recent funding)
- **Provide transparency** with detailed score explanations
- **Enable manual control** with score overrides
- **Automate lead management** with auto-park functionality

### Architecture

```
Signal Input
    ↓
AI Classification (1B model) → Base Scores (fit, pain, quality)
    ↓
Scoring Heuristics Module
    ├─ Ghost Job Detection (-20 to 0 points)
    ├─ First Marketer Detection (0 to +15 points)
    ├─ Tone Classification (-5 to +10 points)
    ├─ Silver-Bullet Detection (-20 to 0 points)
    ├─ Spam Detection (-40 to 0 points)
    └─ Industry-Specific (+0 to +12 points)
    ↓
Funding Event Check (+0 to +10 points)
    ↓
Apply Custom Weights → Final Score (0-100)
    ↓
Score Bucket (red_hot, warm, nurture, parked)
```

---

## Ghost Job Detection

### Purpose

Identify and penalize **ghost jobs** - fake or stale job postings that waste sales team's time.

### Detection Criteria

| Indicator | Penalty | Reason |
|-----------|---------|--------|
| Post age >30 days | -1 to -20 points | Older posts likely filled or stale |
| No company name | -10 points | Suspicious anonymity |
| Very short description (<100 chars) | -5 points | Low effort post |
| Excessively long (>5000 chars) | -3 points | Boilerplate template |
| Template placeholders | -15 points | "[Company Name]", "TBD", etc. |

### Example

**Signal**:
```
Job Title: Marketing Manager
Company: [Insert Company Name]
Posted: 45 days ago
Description: We are looking for a marketing manager. TBD.
```

**Detection**:
```json
{
  "category": "ghost_job",
  "adjustment": -30,
  "reason": "Post is 45 days old (stale); No company name provided; Contains template placeholders",
  "confidence": 0.9
}
```

**Impact**: Signal dropped from 65 points to 35 points → Moved from "warm" to "parked"

### Configuration

```bash
# Ghost job detection is always enabled when scoring heuristics are on
ENABLE_SCORING_HEURISTICS=true
```

---

## First Marketer Detection

### Purpose

Identify and **boost** signals for "first marketer" roles - highly valuable opportunities where the hire will own all marketing.

### Detection Patterns

Regex patterns matched (case-insensitive):

- `first marketing hire`
- `first marketer`
- `own all of marketing`
- `founding marketer`
- `0 to 1 marketing`
- `build marketing from scratch`
- `establish marketing function`

### Scoring

- **+5 points** per matching pattern
- **Max +15 points** (3+ matches)
- Confidence increases with more matches

### Example

**Signal**:
```
Looking for our FIRST MARKETING HIRE to own all of marketing
and build our growth function from scratch. You'll establish
the entire marketing function at our early-stage SaaS startup.
```

**Detection**:
```json
{
  "category": "first_marketer",
  "adjustment": 15,
  "reason": "First marketer role detected (3 indicators)",
  "confidence": 0.9
}
```

**Impact**: Signal boosted from 55 points to 70 points → Moved from "nurture" to "warm" → Triggers 4B dossier generation

---

## Founder vs HR Tone Classification

### Purpose

Distinguish between **founder-written** posts (personal, passionate) and **HR-generated** posts (generic, formal) to prioritize authentic opportunities.

### Founder Tone Indicators

Patterns suggesting founder-written:

- `we're building`
- `our mission`
- `join us`
- `I'm looking` (first person)
- `help us grow`
- `passionate about`

**Bonus**: +10 points max (founder ratio >60%)

### HR Tone Indicators

Patterns suggesting HR/generic:

- `the successful candidate`
- `responsibilities include`
- `competitive salary`
- `equal opportunity employer`
- `please submit`

**Penalty**: -5 points max (founder ratio <40%)

### Example

**Founder-written signal**:
```
We're building the future of email marketing for D2C brands.
Our mission is to help small businesses compete with giants.
I'm looking for someone passionate about growth who can
help us reach our first 1000 customers. Join us on this journey!
```

**Detection**:
```json
{
  "category": "tone_classification",
  "adjustment": 8,
  "reason": "Founder-written tone detected (5 founder indicators, 1 HR indicators)",
  "confidence": 0.83
}
```

**HR-generated signal**:
```
The successful candidate will have responsibilities including
managing social media accounts and creating content. Qualifications
include 3+ years of experience. Competitive salary and benefits
package. Equal opportunity employer. Please submit your resume.
```

**Detection**:
```json
{
  "category": "tone_classification",
  "adjustment": -4,
  "reason": "HR/generic tone detected (5 HR indicators, 0 founder indicators)",
  "confidence": 0.90
}
```

---

## Silver-Bullet Seeker Detection

### Purpose

Flag and **penalize** unrealistic expectations ("10x growth overnight") that indicate difficult clients.

### Detection Patterns

- `10x growth`
- `hockey stick growth`
- `overnight success`
- `viral growth`
- `guaranteed success`
- `triple revenue in a month`

### Scoring

- **-8 points** per red flag
- **Max -20 points**
- Warns sales team about unrealistic expectations

### Example

**Signal**:
```
Looking for growth hacker to achieve 10x growth and hockey stick
trajectory. We need viral growth and guaranteed success within 3 months.
```

**Detection**:
```json
{
  "category": "silver_bullet_seeker",
  "adjustment": -20,
  "reason": "Unrealistic expectations detected (3 red flags)",
  "confidence": 0.8
}
```

**Impact**: Major penalty warns team this client may have unrealistic expectations

---

## Spam Detection

### Purpose

Identify and **heavily penalize** spammy, low-quality signals.

### Detection Patterns

- `earn money fast`
- `work from home` (context-dependent)
- `no experience needed`
- `MLM` / `multi-level marketing`
- `get rich quick`
- `limited time offer`

### Scoring

- **-15 points** per spam indicator
- **Max -40 points**
- Effectively kills spam signals

### Example

**Signal**:
```
Earn money fast working from home! No experience needed.
MLM opportunity. Get rich quick with our proven system.
Limited time offer!
```

**Detection**:
```json
{
  "category": "spam_detection",
  "adjustment": -40,
  "reason": "Spammy language detected (4 spam indicators)",
  "confidence": 0.9
}
```

**Impact**: Signal dropped from 50 points to 10 points → Effectively filtered out

---

## Industry-Specific Scoring

### Purpose

Apply **industry-specific pain keyword matching** to boost signals with domain-relevant pain.

### Supported Industries

| Industry | Pain Keywords |
|----------|---------------|
| **D2C** | retention, churn, CAC, LTV, abandoned cart, repeat purchase, customer loyalty |
| **SaaS** | pipeline, MQL, SQL, conversion, trial-to-paid, activation, onboarding, PLG |
| **B2B** | lead generation, enterprise sales, ABM, demand gen, sales cycle, deal velocity |
| **Ecommerce** | cart abandonment, conversion rate, AOV, ROAS, product pages, SEO |
| **Marketplace** | supply-demand, liquidity, GMV, take rate, network effects |

### Industry Detection

Auto-detected from signal text:

- "d2c", "direct to consumer" → D2C
- "saas", "b2b software" → SaaS
- "marketplace", "platform" → Marketplace

Or manually specified in API request:

```json
{
  "signal_text": "...",
  "industry": "saas"
}
```

### Scoring

- **+3 points** per matching pain keyword
- **Max +12 points**

### Example

**Signal (SaaS)**:
```
Struggling with pipeline generation and poor trial-to-paid
conversion. Need help with PLG motion and activation flows.
```

**Detection**:
```json
{
  "category": "industry_specific",
  "adjustment": 9,
  "reason": "SAAS industry pain detected (3 keywords)",
  "confidence": 0.6
}
```

**Impact**: +9 points for domain-specific pain

---

## Funding Event Signals

### Purpose

Boost leads for companies that recently raised funding (hiring spree indicator).

### How It Works

1. **Track funding events** via API or manual entry
2. **Check timeframe**: Signal posted within `funding_boost_days` of funding announcement
3. **Apply bonus**: +10 points (configurable)

### Configuration

```bash
# Boost window (default: 60 days)
FUNDING_BOOST_DAYS=60

# Bonus points (default: 10)
FUNDING_BOOST_SCORE=10.0
```

### API Usage

**Add Funding Event**:
```bash
POST /api/classify/funding-events
Content-Type: application/json

{
  "company_name": "Acme Corp",
  "event_type": "series_a",
  "amount_usd": 5000000,
  "announced_date": "2025-11-01T00:00:00",
  "source": "crunchbase",
  "notes": "Led by Sequoia"
}
```

**List Recent Events**:
```bash
GET /api/classify/funding-events?days=90
```

### Example

**Scenario**:
- Acme Corp raises Series A on Nov 1, 2025
- Marketing manager job posted on Nov 15, 2025 (14 days later)
- Funding boost applied: +10 points

**Impact**: Signal boosted from 68 to 78 points → "warm" to "red_hot"

---

## Customizable Scoring Weights

### Purpose

Allow users to **adjust the relative importance** of ICP fit, marketing pain, and data quality.

### Configuration

```bash
# Default weights (all 1.0 = equal importance)
SCORING_WEIGHT_ICP_FIT=1.0
SCORING_WEIGHT_MARKETING_PAIN=1.0
SCORING_WEIGHT_DATA_QUALITY=1.0

# Example: Prioritize pain over fit
SCORING_WEIGHT_ICP_FIT=0.8
SCORING_WEIGHT_MARKETING_PAIN=1.5
SCORING_WEIGHT_DATA_QUALITY=1.0
```

### Calculation

```
base_total = (fit_score × fit_weight) +
             (pain_score × pain_weight) +
             (quality_score × quality_weight)

final_score = base_total + heuristic_adjustments + funding_bonus
```

### Example

**Base Scores**:
- ICP Fit: 40/50
- Marketing Pain: 30/40
- Data Quality: 8/10

**Default Weights (1.0, 1.0, 1.0)**:
```
base_total = (40 × 1.0) + (30 × 1.0) + (8 × 1.0) = 78
```

**Prioritize Pain (0.8, 1.5, 1.0)**:
```
base_total = (40 × 0.8) + (30 × 1.5) + (8 × 1.0) = 32 + 45 + 8 = 85
```

**Impact**: Signal moved from "warm" (78) to "red_hot" (85)

---

## Manual Score Overrides

### Purpose

Allow users to **manually adjust scores** when automated scoring misses context.

### Features

- Override any lead's score
- Store override history
- Record reason for override
- Track who made the override

### API Usage

**Override Score**:
```bash
POST /api/classify/leads/{lead_id}/override-score
Content-Type: application/json

{
  "override_score": 85,
  "reason": "CEO reached out directly on LinkedIn",
  "user": "john@sales.com"
}
```

**Response**:
```json
{
  "lead_id": 123,
  "original_score": 65,
  "override_score": 85,
  "new_bucket": "red_hot",
  "reason": "CEO reached out directly on LinkedIn"
}
```

**View Override History**:
```bash
GET /api/classify/leads/{lead_id}/score-history
```

**Response**:
```json
{
  "lead_id": 123,
  "current_score": 85,
  "manual_override": 85,
  "override_count": 2,
  "history": [
    {
      "id": 5,
      "user": "john@sales.com",
      "original_score": 65,
      "override_score": 85,
      "reason": "CEO reached out directly on LinkedIn",
      "timestamp": "2025-11-19T14:30:00"
    },
    {
      "id": 3,
      "user": "admin",
      "original_score": 60,
      "override_score": 65,
      "reason": "Competitor insight",
      "timestamp": "2025-11-18T10:00:00"
    }
  ]
}
```

### Use Cases

- **Inbound interest**: CEO/founder reached out directly
- **Competitive intelligence**: Competitor just lost this client
- **Relationship**: Existing connection/warm intro
- **Strategic**: High-value target regardless of score
- **Correction**: Model clearly wrong (e.g., missed key context)

---

## Auto-Park Functionality

### Purpose

Automatically park **stale leads** that haven't been contacted to keep pipeline clean.

### How It Works

1. **Daily scheduled task** runs at 2:00 AM
2. **Identifies leads**: Status = "new", created > `auto_park_days` ago
3. **Parks leads**: Status → "parked", adds timestamped note
4. **Tracks**: Records `auto_parked_at` timestamp

### Configuration

```bash
# Enable auto-park (default: true)
ENABLE_AUTO_PARK=true

# Days before auto-parking (default: 30)
AUTO_PARK_DAYS=30
```

### Manual Trigger

**Dry Run** (see what would be parked):
```bash
POST /api/classify/leads/auto-park?dry_run=true
```

**Response**:
```json
{
  "dry_run": true,
  "leads_to_park": 15,
  "leads": [
    {
      "id": 45,
      "company_id": 12,
      "total_score": 55,
      "created_at": "2025-10-01T10:00:00",
      "days_old": 49
    },
    ...
  ]
}
```

**Actually Park**:
```bash
POST /api/classify/leads/auto-park
```

**Response**:
```json
{
  "parked_count": 15,
  "cutoff_date": "2025-10-20T00:00:00",
  "auto_park_days": 30
}
```

### Scheduled Task

Auto-park runs **daily at 2:00 AM** (configured in `scheduled_tasks.py`).

Check scheduled tasks:
```python
from scheduled_tasks import get_scheduled_jobs
jobs = get_scheduled_jobs()
# Output: [{"id": "auto_park_leads", "name": "Auto-Park Old Leads", ...}]
```

---

## Score Explanation

### Purpose

Provide **transparent, detailed breakdown** of how final score was calculated.

### Response Format

Every classification result includes `score_explanation`:

```json
{
  "base_scores": {
    "icp_fit": 40,
    "marketing_pain": 30,
    "data_quality": 8
  },
  "scoring_weights": {
    "icp_fit": 1.0,
    "marketing_pain": 1.0,
    "data_quality": 1.0
  },
  "weighted_base_scores": {
    "icp_fit": 40,
    "marketing_pain": 30,
    "data_quality": 8
  },
  "base_total": 78,
  "adjustments": [
    {
      "category": "first_marketer",
      "adjustment": 15,
      "reason": "First marketer role detected (3 indicators)",
      "confidence": 0.9
    },
    {
      "category": "tone_classification",
      "adjustment": 8,
      "reason": "Founder-written tone detected",
      "confidence": 0.75
    },
    {
      "category": "ghost_job",
      "adjustment": -5,
      "reason": "Post is 35 days old (stale)",
      "confidence": 0.6
    }
  ],
  "adjustment_total": 18,
  "final_score": 96,
  "score_bucket": "red_hot"
}
```

### UI Display

Recommended UI breakdown:

```
Lead Score: 96 / 100 (Red Hot 🔥)

Base Scores:
  ✓ ICP Fit:         40/50  ████████░░
  ✓ Marketing Pain:  30/40  ████████░
  ✓ Data Quality:     8/10  ████████░

Adjustments:
  ✓ First Marketer:  +15  (3 indicators found)
  ✓ Founder Tone:     +8  (Personal, mission-driven)
  ⚠ Ghost Job:        -5  (Post is 35 days old)

Final Score: 96 → Red Hot
```

---

## API Reference

### Classification Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/classify/signal` | POST | Classify single signal (with heuristics) |
| `/api/classify/signal/batch` | POST | Classify multiple signals |
| `/api/classify/metrics` | GET | Get AI/cache/heuristics metrics |

### Funding Events

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/classify/funding-events` | POST | Add funding event |
| `/api/classify/funding-events` | GET | List recent funding events |

### Score Overrides

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/classify/leads/{id}/override-score` | POST | Override lead score |
| `/api/classify/leads/{id}/score-history` | GET | View override history |

### Auto-Park

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/classify/leads/auto-park` | POST | Auto-park old leads |

---

## Configuration

### Complete `.env` Example

```bash
# Scoring Heuristics
ENABLE_SCORING_HEURISTICS=true
SCORING_WEIGHT_ICP_FIT=1.0
SCORING_WEIGHT_MARKETING_PAIN=1.0
SCORING_WEIGHT_DATA_QUALITY=1.0

# Auto-park
ENABLE_AUTO_PARK=true
AUTO_PARK_DAYS=30

# Funding Events
FUNDING_BOOST_DAYS=60
FUNDING_BOOST_SCORE=10.0
```

### Feature Matrix

| Feature | Default | Configurable | Dependencies |
|---------|---------|--------------|--------------|
| Ghost Job Detection | Enabled | Via `ENABLE_SCORING_HEURISTICS` | None |
| First Marketer Detection | Enabled | Via `ENABLE_SCORING_HEURISTICS` | None |
| Tone Classification | Enabled | Via `ENABLE_SCORING_HEURISTICS` | None |
| Silver-Bullet Detection | Enabled | Via `ENABLE_SCORING_HEURISTICS` | None |
| Spam Detection | Enabled | Via `ENABLE_SCORING_HEURISTICS` | None |
| Industry-Specific | Enabled | Via `ENABLE_SCORING_HEURISTICS` | None |
| Funding Boost | Enabled | Via funding events API | Database |
| Custom Weights | Configurable | Via `SCORING_WEIGHT_*` vars | None |
| Manual Overrides | Always available | N/A | Database |
| Auto-Park | Enabled | Via `ENABLE_AUTO_PARK` | Scheduler |

---

## Performance Impact

### Heuristics Overhead

**Latency Impact**: +10-20ms per signal (regex matching, score calculation)

**Benefit**: Improved lead quality, reduced false positives, better transparency

### Caching

Heuristic results are **not cached** (too context-dependent), but AI classification is cached, so heuristics overhead is minimal.

---

## Examples

### Complete Flow Example

**Input Signal**:
```json
{
  "signal_text": "Looking for our first marketing hire to own all of marketing at our Series A SaaS startup. We're building the future of project management for remote teams. Join us on this mission! Posted 5 days ago.",
  "company_name": "Acme Corp",
  "post_date": "2025-11-14T00:00:00",
  "industry": "saas"
}
```

**AI Classification** (1B model):
```json
{
  "score_fit": 45,
  "score_pain": 35,
  "score_data_quality": 9,
  "icp_match": true,
  "role_type": "first_marketer"
}
```

**Heuristics Applied**:
1. Ghost Job: 0 (recent post, has company name)
2. First Marketer: +15 (3 indicators)
3. Tone: +8 (founder-written)
4. Silver-Bullet: 0 (no red flags)
5. Spam: 0 (no spam)
6. Industry: +9 (SaaS pain keywords)

**Funding Check**:
- Acme Corp raised Series A on Nov 1 (13 days ago)
- Funding boost: +10

**Final Calculation**:
```
base_total = 45 + 35 + 9 = 89
heuristic_total = 0 + 15 + 8 + 0 + 0 + 9 = 32
funding_bonus = 10
final_score = 89 + 32 + 10 = 131 → clamped to 100
```

**Result**: **100 / 100 (Red Hot 🔥)**

**Action**: Immediately queue 4B dossier, prioritize for sales team.

---

## Troubleshooting

### Issue: Scores seem too high/low

**Solution**: Adjust scoring weights:
```bash
# Reduce overall scores
SCORING_WEIGHT_ICP_FIT=0.8
SCORING_WEIGHT_MARKETING_PAIN=0.8
SCORING_WEIGHT_DATA_QUALITY=0.8
```

### Issue: Too many leads auto-parked

**Solution**: Increase auto-park threshold:
```bash
AUTO_PARK_DAYS=45  # Was 30
```

### Issue: Heuristics not being applied

**Check**:
1. `ENABLE_SCORING_HEURISTICS=true` in `.env`
2. Scoring heuristics initialized in `/health` endpoint
3. Check logs for heuristics messages

### Issue: Funding boost not working

**Check**:
1. Funding event created with correct `company_id`
2. `announced_date` within `FUNDING_BOOST_DAYS` window
3. Signal includes `company_name` that matches

---

## Summary

The scoring heuristics system provides:

✅ **10+ intelligent quality detectors**
✅ **Transparent score explanations**
✅ **Customizable scoring weights**
✅ **Manual override capability**
✅ **Automated lead management**
✅ **Funding event signals**
✅ **Industry-specific adjustments**

**Result**: Higher quality leads, less sales team waste, better pipeline management.
