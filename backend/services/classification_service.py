"""Classification business logic service."""

from datetime import datetime
from typing import Dict, Any, Optional
import logging
from sqlalchemy.orm import Session

from database import Lead, Company, Contact, Signal, ICPProfile
from schemas.classification import SignalInput, ClassificationResult
from ollama_wrapper import OllamaManager
from config import Settings

logger = logging.getLogger(__name__)


class ClassificationService:
    """Service for signal classification and lead creation."""

    @staticmethod
    def compute_score_bucket(total_score: float) -> str:
        """
        Convert total score to score bucket.

        Args:
            total_score: Total lead score (0-100)

        Returns:
            Score bucket name
        """
        if total_score >= 80:
            return "red_hot"
        elif total_score >= 60:
            return "warm"
        elif total_score >= 40:
            return "nurture"
        else:
            return "parked"

    @staticmethod
    async def classify_signal(
        db: Session,
        signal: SignalInput,
        settings: Settings,
    ) -> ClassificationResult:
        """
        Classify a signal using 1B model and create a lead.

        Args:
            db: Database session
            signal: Signal input data
            settings: Application settings

        Returns:
            Classification result with lead info
        """
        # Get ICP context
        icps = db.query(ICPProfile).all()
        icp_context = {
            "size_buckets": ["1", "2-5", "6-10", "11-20"],
            "industries": list(set([ind for icp in icps for ind in icp.industries])),
            "pain_keywords": list(set([kw for icp in icps for kw in icp.pain_keywords])),
            "hiring_keywords": list(set([kw for icp in icps for kw in icp.hiring_keywords])),
        }

        # Initialize Ollama manager and classify
        ollama = OllamaManager()
        classification = await ollama.classify_signal(signal.signal_text, icp_context)

        # Compute total score
        total_score = (
            classification.get("score_fit", 0) +
            classification.get("score_pain", 0) +
            classification.get("score_data_quality", 0)
        )
        score_bucket = ClassificationService.compute_score_bucket(total_score)

        # Get or create company
        company_id = None
        if signal.company_name:
            company = db.query(Company).filter(
                (Company.name.ilike(signal.company_name)) |
                (Company.website == signal.company_website)
            ).first()

            if not company:
                company = Company(
                    name=signal.company_name,
                    website=signal.company_website,
                    country="india",
                )
                db.add(company)
                db.commit()
                db.refresh(company)

            company_id = company.id

        # Create signal record
        db_signal = Signal(
            company_id=company_id,
            source_type=signal.source_type,
            source_url=signal.source_url,
            raw_text=signal.signal_text,
        )
        db.add(db_signal)
        db.commit()
        db.refresh(db_signal)

        # Create lead
        db_lead = Lead(
            company_id=company_id,
            score_icp_fit=classification.get("score_fit", 0),
            score_marketing_pain=classification.get("score_pain", 0),
            score_data_quality=classification.get("score_data_quality", 0),
            total_score=total_score,
            score_bucket=score_bucket,
            role_type=classification.get("role_type", "unclear"),
            pain_tags=classification.get("pain_tags", []),
            situation=classification.get("situation", ""),
            problem=classification.get("problem", ""),
            implication=classification.get("implication", ""),
            need_payoff=classification.get("need_payoff", ""),
            economic_buyer_guess=classification.get("economic_buyer_guess", ""),
            key_pain=classification.get("key_pain", ""),
            chaos_flags=classification.get("chaos_flags", []),
            silver_bullet_phrases=classification.get("silver_bullet_phrases", []),
            status="new",
        )
        db.add(db_lead)
        db.commit()
        db.refresh(db_lead)

        logger.info(f"✅ Lead {db_lead.id} created with score {total_score}")

        return ClassificationResult(
            icp_match=classification.get("icp_match", False),
            total_score=total_score,
            score_bucket=score_bucket,
            classification=classification,
            company_id=company_id,
            lead_id=db_lead.id,
        )

    @staticmethod
    async def generate_dossier_async(
        lead_id: int,
        lead_json: Dict[str, Any],
        signal_snippets: list,
        db: Session,
    ):
        """
        Background task to generate 4B dossier for high-scoring leads.

        Args:
            lead_id: Lead ID
            lead_json: Lead data as JSON
            signal_snippets: Signal text snippets
            db: Database session
        """
        try:
            ollama = OllamaManager()
            dossier = await ollama.generate_dossier(lead_json, signal_snippets)

            lead = db.query(Lead).filter(Lead.id == lead_id).first()
            if lead:
                lead.context_dossier = dossier.get("snapshot", "") + "\n\n" + \
                                      "\n".join(dossier.get("why_pain_bullets", []))
                lead.challenger_insight = dossier.get("challenger_insight", "")
                lead.reframe_suggestion = dossier.get("reframe_suggestion", "")
                lead.updated_at = datetime.utcnow()
                db.add(lead)
                db.commit()
                logger.info(f"✅ Dossier generated for lead {lead_id}")
        except Exception as e:
            logger.error(f"Error generating dossier for lead {lead_id}: {e}")

    @staticmethod
    def should_generate_dossier(total_score: float, settings: Settings) -> bool:
        """
        Determine if dossier should be generated for a lead.

        Args:
            total_score: Total lead score
            settings: Application settings

        Returns:
            True if dossier should be generated
        """
        return total_score > settings.classifier_score_threshold
