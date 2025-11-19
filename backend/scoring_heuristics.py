"""Advanced scoring heuristics and detection logic for lead qualification."""

import re
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from collections import Counter

logger = logging.getLogger(__name__)


@dataclass
class ScoringAdjustment:
    """Represents a scoring adjustment with reason."""
    category: str  # e.g., "ghost_job", "first_marketer", "founder_tone"
    adjustment: float  # Score adjustment (positive or negative)
    reason: str  # Human-readable explanation
    confidence: float  # Confidence in this adjustment (0-1)


class ScoringHeuristics:
    """
    Advanced heuristics for lead scoring and quality detection.

    Features:
    - Ghost job detection
    - First marketer phrasing detection
    - Founder vs HR tone classification
    - Silver-bullet seeker detection
    - Spammy copy detection
    - Content inconsistency analysis
    - Industry-specific adjustments
    """

    # Regex patterns for first marketer detection
    FIRST_MARKETER_PATTERNS = [
        r"\bfirst\s+marketing\s+hire\b",
        r"\bfirst\s+marketer\b",
        r"\bown\s+all\s+of\s+marketing\b",
        r"\bown\s+marketing\b",
        r"\bfounding\s+marketer\b",
        r"\bhead\s+of\s+growth\b.*\bfirst\b",
        r"\b0\s*to\s*1\b.*\bmarketing\b",
        r"\bbuild.*marketing\s+from\s+scratch\b",
        r"\bestablish.*marketing\s+function\b",
    ]

    # Patterns for founder tone (personal, mission-driven)
    FOUNDER_TONE_PATTERNS = [
        r"\bwe're\s+building\b",
        r"\bour\s+mission\b",
        r"\bour\s+vision\b",
        r"\bjoin\s+us\b",
        r"\bwe\s+believe\b",
        r"\bI'm\s+looking\b",  # First person
        r"\bI\s+need\b",
        r"\bmy\s+team\b",
        r"\bhelp\s+us\s+\w+\b",  # "help us grow", etc.
        r"\bexcited\s+to\b",
        r"\bpassionate\s+about\b",
    ]

    # Patterns for HR/generic tone
    HR_TONE_PATTERNS = [
        r"\bthe\s+successful\s+candidate\b",
        r"\bthe\s+ideal\s+candidate\b",
        r"\bresponsibilities\s+include\b",
        r"\bqualifications\b",
        r"\brequirements\b",
        r"\bcompetitive\s+salary\b",
        r"\bbenefits\s+package\b",
        r"\bequal\s+opportunity\s+employer\b",
        r"\bplease\s+submit\b",
        r"\bto\s+apply\b",
    ]

    # Silver-bullet seeker patterns (unrealistic expectations)
    SILVER_BULLET_PATTERNS = [
        r"\b10x\s+growth\b",
        r"\b100x\s+growth\b",
        r"\bhockey\s+stick\s+growth\b",
        r"\bovernight\s+success\b",
        r"\binstant\s+results\b",
        r"\bviral\s+growth\b",
        r"\bguaranteed\s+success\b",
        r"\btriple.*revenue.*month\b",
        r"\bexplosive\s+growth\b",
    ]

    # Spammy copy patterns
    SPAM_PATTERNS = [
        r"\bearn\s+money\s+fast\b",
        r"\bwork\s+from\s+home\b",
        r"\bno\s+experience\s+needed\b",
        r"\bMLM\b",
        r"\bmulti[-\s]?level\s+marketing\b",
        r"\bpyramid\b",
        r"\bget\s+rich\s+quick\b",
        r"\bclick\s+here\b",
        r"\blimited\s+time\s+offer\b",
    ]

    # Industry-specific pain keywords
    INDUSTRY_PAIN_KEYWORDS = {
        "d2c": [
            "retention", "churn", "CAC", "LTV", "abandoned cart",
            "repeat purchase", "customer loyalty", "DTC"
        ],
        "saas": [
            "pipeline", "MQL", "SQL", "conversion", "trial-to-paid",
            "activation", "onboarding", "expansion", "PLG"
        ],
        "b2b": [
            "lead generation", "enterprise sales", "ABM", "demand gen",
            "sales cycle", "deal velocity", "pipeline"
        ],
        "ecommerce": [
            "cart abandonment", "conversion rate", "AOV", "ROAS",
            "product pages", "checkout", "SEO"
        ],
        "marketplace": [
            "supply-demand", "liquidity", "GMV", "take rate",
            "network effects", "two-sided"
        ],
    }

    def __init__(self, scoring_weights: Optional[Dict[str, float]] = None):
        """
        Initialize scoring heuristics.

        Args:
            scoring_weights: Custom weights for different scoring factors
        """
        self.scoring_weights = scoring_weights or {
            "icp_fit": 1.0,
            "marketing_pain": 1.0,
            "data_quality": 1.0,
        }

        # Compile regex patterns for performance
        self.first_marketer_regex = [re.compile(p, re.IGNORECASE) for p in self.FIRST_MARKETER_PATTERNS]
        self.founder_tone_regex = [re.compile(p, re.IGNORECASE) for p in self.FOUNDER_TONE_PATTERNS]
        self.hr_tone_regex = [re.compile(p, re.IGNORECASE) for p in self.HR_TONE_PATTERNS]
        self.silver_bullet_regex = [re.compile(p, re.IGNORECASE) for p in self.SILVER_BULLET_PATTERNS]
        self.spam_regex = [re.compile(p, re.IGNORECASE) for p in self.SPAM_PATTERNS]

    def detect_ghost_job(
        self,
        signal_text: str,
        post_date: Optional[datetime] = None,
        company_name: Optional[str] = None,
        source_url: Optional[str] = None
    ) -> ScoringAdjustment:
        """
        Detect ghost jobs (old posts, missing company info, boilerplate).

        Ghost job indicators:
        - Post older than 30 days
        - No company name
        - Generic boilerplate text
        - Duplicate postings across platforms

        Returns:
            ScoringAdjustment with penalty if ghost job detected
        """
        penalties = []
        reasons = []

        # Check post age
        if post_date:
            age_days = (datetime.utcnow() - post_date).days
            if age_days > 30:
                penalty = min(age_days - 30, 20)  # Max 20 point penalty
                penalties.append(penalty)
                reasons.append(f"Post is {age_days} days old (stale)")

        # Check company name
        if not company_name or company_name.lower() in ["unknown", "n/a", "confidential"]:
            penalties.append(10)
            reasons.append("No company name provided")

        # Check for boilerplate text (very short or very long)
        text_length = len(signal_text.strip())
        if text_length < 100:
            penalties.append(5)
            reasons.append("Very short job description")
        elif text_length > 5000:
            penalties.append(3)
            reasons.append("Excessively long boilerplate")

        # Check for generic phrases indicating template
        boilerplate_phrases = [
            "this is a template",
            "[insert company name]",
            "[company name]",
            "TBD",
            "to be determined"
        ]
        if any(phrase.lower() in signal_text.lower() for phrase in boilerplate_phrases):
            penalties.append(15)
            reasons.append("Contains template placeholders")

        total_penalty = sum(penalties)

        if total_penalty > 0:
            return ScoringAdjustment(
                category="ghost_job",
                adjustment=-total_penalty,
                reason="; ".join(reasons),
                confidence=min(total_penalty / 30, 1.0)  # Higher penalty = higher confidence
            )
        else:
            return ScoringAdjustment(
                category="ghost_job",
                adjustment=0,
                reason="No ghost job indicators detected",
                confidence=0.5
            )

    def detect_first_marketer(self, signal_text: str) -> ScoringAdjustment:
        """
        Detect "first marketer" phrasing and boost scores.

        Returns:
            ScoringAdjustment with bonus if first marketer detected
        """
        matches = []
        for pattern in self.first_marketer_regex:
            if pattern.search(signal_text):
                matches.append(pattern.pattern)

        if matches:
            # More matches = higher confidence
            bonus = min(len(matches) * 5, 15)  # 5 points per match, max 15
            return ScoringAdjustment(
                category="first_marketer",
                adjustment=bonus,
                reason=f"First marketer role detected ({len(matches)} indicators)",
                confidence=min(len(matches) * 0.3, 1.0)
            )
        else:
            return ScoringAdjustment(
                category="first_marketer",
                adjustment=0,
                reason="Not a first marketer role",
                confidence=0.3
            )

    def classify_tone(self, signal_text: str) -> ScoringAdjustment:
        """
        Classify job post tone as founder-written vs HR-generated.

        Founder tone = personal, mission-driven, passionate
        HR tone = formal, generic, procedural

        Returns:
            ScoringAdjustment with bonus for founder tone
        """
        founder_matches = sum(1 for pattern in self.founder_tone_regex if pattern.search(signal_text))
        hr_matches = sum(1 for pattern in self.hr_tone_regex if pattern.search(signal_text))

        total_matches = founder_matches + hr_matches
        if total_matches == 0:
            return ScoringAdjustment(
                category="tone_classification",
                adjustment=0,
                reason="Unable to classify tone",
                confidence=0.1
            )

        founder_ratio = founder_matches / total_matches

        if founder_ratio > 0.6:
            # Founder-written (good!)
            bonus = int(founder_ratio * 10)  # Max 10 points
            return ScoringAdjustment(
                category="tone_classification",
                adjustment=bonus,
                reason=f"Founder-written tone detected ({founder_matches} founder indicators, {hr_matches} HR indicators)",
                confidence=founder_ratio
            )
        elif founder_ratio < 0.4:
            # HR-written (less ideal)
            penalty = int((1 - founder_ratio) * 5)  # Max 5 point penalty
            return ScoringAdjustment(
                category="tone_classification",
                adjustment=-penalty,
                reason=f"HR/generic tone detected ({hr_matches} HR indicators, {founder_matches} founder indicators)",
                confidence=1 - founder_ratio
            )
        else:
            # Mixed tone
            return ScoringAdjustment(
                category="tone_classification",
                adjustment=0,
                reason="Mixed tone (both founder and HR elements)",
                confidence=0.5
            )

    def detect_silver_bullet_seekers(self, signal_text: str) -> ScoringAdjustment:
        """
        Detect unrealistic expectations ("10x growth overnight").

        Returns:
            ScoringAdjustment with penalty for silver-bullet language
        """
        matches = [pattern.pattern for pattern in self.silver_bullet_regex if pattern.search(signal_text)]

        if matches:
            penalty = min(len(matches) * 8, 20)  # 8 points per match, max 20
            return ScoringAdjustment(
                category="silver_bullet_seeker",
                adjustment=-penalty,
                reason=f"Unrealistic expectations detected ({len(matches)} red flags)",
                confidence=min(len(matches) * 0.4, 1.0)
            )
        else:
            return ScoringAdjustment(
                category="silver_bullet_seeker",
                adjustment=0,
                reason="No unrealistic expectations detected",
                confidence=0.5
            )

    def detect_spam(self, signal_text: str) -> ScoringAdjustment:
        """
        Detect spammy copy ("earn money fast", "MLM").

        Returns:
            ScoringAdjustment with heavy penalty for spam
        """
        matches = [pattern.pattern for pattern in self.spam_regex if pattern.search(signal_text)]

        if matches:
            penalty = min(len(matches) * 15, 40)  # 15 points per match, max 40
            return ScoringAdjustment(
                category="spam_detection",
                adjustment=-penalty,
                reason=f"Spammy language detected ({len(matches)} spam indicators)",
                confidence=min(len(matches) * 0.5, 1.0)
            )
        else:
            return ScoringAdjustment(
                category="spam_detection",
                adjustment=0,
                reason="No spam detected",
                confidence=0.8
            )

    def adjust_for_industry(
        self,
        signal_text: str,
        industry: Optional[str] = None
    ) -> ScoringAdjustment:
        """
        Adjust scoring based on industry-specific pain signals.

        Returns:
            ScoringAdjustment with bonus for industry-specific pain
        """
        if not industry or industry not in self.INDUSTRY_PAIN_KEYWORDS:
            # Try to detect industry from text
            industry = self._detect_industry(signal_text)

        if industry and industry in self.INDUSTRY_PAIN_KEYWORDS:
            pain_keywords = self.INDUSTRY_PAIN_KEYWORDS[industry]
            matches = sum(1 for kw in pain_keywords if kw.lower() in signal_text.lower())

            if matches > 0:
                bonus = min(matches * 3, 12)  # 3 points per keyword, max 12
                return ScoringAdjustment(
                    category="industry_specific",
                    adjustment=bonus,
                    reason=f"{industry.upper()} industry pain detected ({matches} keywords)",
                    confidence=min(matches * 0.2, 0.9)
                )

        return ScoringAdjustment(
            category="industry_specific",
            adjustment=0,
            reason="No industry-specific pain detected",
            confidence=0.3
        )

    def _detect_industry(self, signal_text: str) -> Optional[str]:
        """Auto-detect industry from signal text."""
        text_lower = signal_text.lower()

        # Simple keyword-based detection
        if any(kw in text_lower for kw in ["d2c", "direct to consumer", "dtc", "ecom brand"]):
            return "d2c"
        elif any(kw in text_lower for kw in ["saas", "software as a service", "b2b software"]):
            return "saas"
        elif any(kw in text_lower for kw in ["marketplace", "platform", "two-sided"]):
            return "marketplace"
        elif any(kw in text_lower for kw in ["ecommerce", "e-commerce", "online store"]):
            return "ecommerce"
        elif any(kw in text_lower for kw in ["b2b", "enterprise", "business to business"]):
            return "b2b"

        return None

    def apply_all_heuristics(
        self,
        signal_text: str,
        post_date: Optional[datetime] = None,
        company_name: Optional[str] = None,
        source_url: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Tuple[float, List[ScoringAdjustment]]:
        """
        Apply all scoring heuristics and return total adjustment.

        Args:
            signal_text: The signal text to analyze
            post_date: When the signal was posted
            company_name: Company name (if available)
            source_url: Source URL (if available)
            industry: Industry classification (if available)

        Returns:
            Tuple of (total_adjustment, list of adjustments)
        """
        adjustments = []

        # Apply all heuristics
        adjustments.append(self.detect_ghost_job(signal_text, post_date, company_name, source_url))
        adjustments.append(self.detect_first_marketer(signal_text))
        adjustments.append(self.classify_tone(signal_text))
        adjustments.append(self.detect_silver_bullet_seekers(signal_text))
        adjustments.append(self.detect_spam(signal_text))
        adjustments.append(self.adjust_for_industry(signal_text, industry))

        # Calculate total adjustment
        total_adjustment = sum(adj.adjustment for adj in adjustments)

        # Log significant adjustments
        significant_adjustments = [adj for adj in adjustments if abs(adj.adjustment) > 5]
        if significant_adjustments:
            logger.info(f"Significant scoring adjustments: {[(adj.category, adj.adjustment) for adj in significant_adjustments]}")

        return total_adjustment, adjustments

    def explain_score(
        self,
        base_scores: Dict[str, float],
        adjustments: List[ScoringAdjustment]
    ) -> Dict[str, Any]:
        """
        Generate detailed score explanation.

        Args:
            base_scores: Original scores (fit, pain, data_quality)
            adjustments: List of scoring adjustments applied

        Returns:
            Dict with score breakdown and explanation
        """
        # Apply weights
        weighted_base = {
            "icp_fit": base_scores.get("score_fit", 0) * self.scoring_weights.get("icp_fit", 1.0),
            "marketing_pain": base_scores.get("score_pain", 0) * self.scoring_weights.get("marketing_pain", 1.0),
            "data_quality": base_scores.get("score_data_quality", 0) * self.scoring_weights.get("data_quality", 1.0)
        }

        base_total = sum(weighted_base.values())
        adjustment_total = sum(adj.adjustment for adj in adjustments)
        final_total = base_total + adjustment_total

        return {
            "base_scores": {
                "icp_fit": base_scores.get("score_fit", 0),
                "marketing_pain": base_scores.get("score_pain", 0),
                "data_quality": base_scores.get("score_data_quality", 0)
            },
            "scoring_weights": self.scoring_weights,
            "weighted_base_scores": weighted_base,
            "base_total": base_total,
            "adjustments": [
                {
                    "category": adj.category,
                    "adjustment": adj.adjustment,
                    "reason": adj.reason,
                    "confidence": adj.confidence
                }
                for adj in adjustments
            ],
            "adjustment_total": adjustment_total,
            "final_score": final_total,
            "score_bucket": self._get_bucket(final_total)
        }

    def _get_bucket(self, score: float) -> str:
        """Get score bucket for a given score."""
        if score >= 80:
            return "red_hot"
        elif score >= 60:
            return "warm"
        elif score >= 40:
            return "nurture"
        else:
            return "parked"


# Singleton instance
_scoring_heuristics: Optional[ScoringHeuristics] = None


def get_scoring_heuristics() -> Optional[ScoringHeuristics]:
    """Get the singleton scoring heuristics instance."""
    return _scoring_heuristics


def init_scoring_heuristics(scoring_weights: Optional[Dict[str, float]] = None) -> ScoringHeuristics:
    """Initialize the singleton scoring heuristics."""
    global _scoring_heuristics
    _scoring_heuristics = ScoringHeuristics(scoring_weights=scoring_weights)
    return _scoring_heuristics
