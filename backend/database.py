"""Database models and initialization."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, ForeignKey, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class ICPProfile(Base):
    """ICP (Ideal Customer Profile) definition."""
    __tablename__ = "icp_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(Text, nullable=True)

    # Firmographics
    size_buckets = Column(JSON, default=[])  # e.g. ["1", "2-5", "6-10", "11-20"]
    industries = Column(JSON, default=[])
    locations = Column(JSON, default=[])  # e.g. ["india"]
    stages = Column(JSON, default=[])  # e.g. ["freelancer", "early-startup", "small-agency"]

    # Marketing pain signals
    hiring_keywords = Column(JSON, default=[])  # e.g. ["marketing manager", "growth hacker"]
    pain_keywords = Column(JSON, default=[])  # e.g. ["lead generation", "scaling ads"]
    channel_preferences = Column(JSON, default=[])  # e.g. ["instagram", "linkedin"]

    # Budget/maturity
    budget_signals = Column(JSON, default=[])  # e.g. ["diy", "1-junior-marketer"]

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Company(Base):
    """Company record."""
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    website = Column(String, nullable=True, unique=True)
    description = Column(Text, nullable=True)

    # Firmographics
    size_bucket = Column(String, nullable=True)  # "1", "2-5", "6-10", "11-20", "unknown"
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    country = Column(String, default="india")
    sector = Column(String, nullable=True)

    # Inferred
    marketing_stack_guess = Column(Text, nullable=True)
    is_marketing_pain_clear = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    contacts = relationship("Contact", back_populates="company")
    signals = relationship("Signal", back_populates="company")
    leads = relationship("Lead", back_populates="company")

class Contact(Base):
    """Individual contact."""
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    name = Column(String, nullable=True)
    role = Column(String, nullable=True)

    email = Column(String, nullable=True, index=True)
    phone_numbers = Column(JSON, default=[])  # Multiple numbers with classifications
    whatsapp_number = Column(String, nullable=True)
    social_links = Column(JSON, default=[])  # LinkedIn, Twitter, etc.

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="contacts")
    leads = relationship("Lead", back_populates="contact")

class Signal(Base):
    """Raw signal data (job post, website snippet, OCR text, etc)."""
    __tablename__ = "signals"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=True)
    source_type = Column(String, index=True)  # "job_post", "website", "ocr", "manual", "csv"
    source_url = Column(String, nullable=True)
    raw_text = Column(Text)
    metadata = Column(JSON, default={})

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="signals")

class Lead(Base):
    """Qualified lead with scores and context."""
    __tablename__ = "leads"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=True)

    # Scoring
    score_icp_fit = Column(Float, default=0)  # 0-50
    score_marketing_pain = Column(Float, default=0)  # 0-40
    score_data_quality = Column(Float, default=0)  # 0-10
    total_score = Column(Float, default=0)  # 0-100
    score_bucket = Column(String, default="parked")  # "red_hot", "warm", "nurture", "parked"

    # Classification
    icp_matches = Column(JSON, default=[])  # List of matching ICP profile IDs
    role_type = Column(String, nullable=True)  # "first_marketer", "agency_replacement", etc.
    pain_tags = Column(JSON, default=[])  # "lead_gen", "brand", "chaos_culture", etc.

    # SPIN / MEDDIC-lite fields
    situation = Column(Text, nullable=True)
    problem = Column(Text, nullable=True)
    implication = Column(Text, nullable=True)
    need_payoff = Column(Text, nullable=True)
    economic_buyer_guess = Column(String, nullable=True)
    key_pain = Column(Text, nullable=True)
    chaos_flags = Column(JSON, default=[])
    silver_bullet_phrases = Column(JSON, default=[])

    # Deep context (generated by 4B model)
    context_dossier = Column(Text, nullable=True)
    challenger_insight = Column(Text, nullable=True)
    reframe_suggestion = Column(Text, nullable=True)

    # Status
    status = Column(String, default="new")  # "new", "contacted", "qualified", "pitched", "trial", "won", "lost", "parked"
    owner = Column(String, nullable=True)  # Who's working this lead
    notes = Column(Text, nullable=True)

    # Scoring heuristics metadata
    heuristic_adjustments = Column(JSON, default=[])  # List of scoring adjustments applied
    ghost_job_score = Column(Float, default=0)  # Ghost job penalty
    first_marketer_bonus = Column(Float, default=0)  # First marketer bonus
    founder_tone_score = Column(Float, default=0)  # Founder vs HR tone
    industry_bonus = Column(Float, default=0)  # Industry-specific bonus
    spam_penalty = Column(Float, default=0)  # Spam detection penalty
    manual_score_override = Column(Float, nullable=True)  # Manual override (if set)
    override_reason = Column(Text, nullable=True)  # Why override was applied

    # Auto-park tracking
    last_contacted_at = Column(DateTime, nullable=True)
    auto_parked_at = Column(DateTime, nullable=True)  # When auto-parked

    # Signal metadata
    signal_post_date = Column(DateTime, nullable=True)  # When the signal was originally posted

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    company = relationship("Company", back_populates="leads")
    contact = relationship("Contact", back_populates="leads")
    activities = relationship("Activity", back_populates="lead")
    score_overrides = relationship("ScoreOverride", back_populates="lead")

class Activity(Base):
    """Activity log per lead (calls, messages, notes, tasks)."""
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    type = Column(String)  # "call", "email", "whatsapp", "note", "task"
    content = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="activities")

class FundingEvent(Base):
    """Track company funding events for signal boost."""
    __tablename__ = "funding_events"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    event_type = Column(String)  # "seed", "series_a", "series_b", "bridge", "acquisition", "ipo"
    amount_usd = Column(Float, nullable=True)
    announced_date = Column(DateTime)
    source = Column(String, nullable=True)  # "crunchbase", "manual", "news"
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company")

class ScoreOverride(Base):
    """Manual score overrides by users."""
    __tablename__ = "score_overrides"

    id = Column(Integer, primary_key=True, index=True)
    lead_id = Column(Integer, ForeignKey("leads.id"))
    user = Column(String)  # Who made the override
    original_score = Column(Float)
    override_score = Column(Float)
    reason = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    lead = relationship("Lead", back_populates="score_overrides")

class ContentActivity(Base):
    """Track company content posting activity for inconsistency detection."""
    __tablename__ = "content_activity"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    platform = Column(String)  # "blog", "twitter", "linkedin", "instagram"
    post_date = Column(DateTime)
    post_url = Column(String, nullable=True)
    post_type = Column(String, nullable=True)  # "blog_post", "tweet", "linkedin_post"

    created_at = Column(DateTime, default=datetime.utcnow)

    company = relationship("Company")

def init_db(engine):
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
