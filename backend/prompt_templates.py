"""Prompt template management for AI models."""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

logger = logging.getLogger(__name__)


class PromptTemplateManager:
    """
    Manages prompt templates for AI classification and dossier generation.

    Features:
    - Load templates from YAML/JSON files
    - Variable interpolation
    - Version control friendly (external files)
    - Easy A/B testing of prompts
    - No code changes required to update prompts
    """

    def __init__(self, template_path: str = "./prompts", enable_custom: bool = False):
        """
        Initialize prompt template manager.

        Args:
            template_path: Directory containing template files
            enable_custom: Whether to load custom templates or use defaults
        """
        self.template_path = Path(template_path)
        self.enable_custom = enable_custom
        self.templates: Dict[str, str] = {}

        # Load templates
        if enable_custom:
            self._load_templates_from_disk()
        else:
            self._load_default_templates()

        logger.info(f"PromptTemplateManager initialized with {len(self.templates)} templates (custom={enable_custom})")

    def _load_default_templates(self):
        """Load default hardcoded prompt templates."""
        # Classification template (1B model)
        self.templates["classification"] = """You are an expert lead qualification analyst. Your job is to analyze social media signals (posts, comments, job ads, etc.) and classify them according to an Ideal Customer Profile (ICP).

**ICP Context:**
{icp_context}

**Signal to Analyze:**
{signal_text}

**Your Task:**
Analyze the signal and return a JSON object with the following structure. Be precise and evidence-based.

**Required JSON Output:**
{{
  "icp_match": <boolean>,
  "size_bucket": "<1|2-5|6-10|11-20|unknown>",
  "region": "<india|other|unknown>",
  "role_type": "<first_marketer|agency_replacement|extra_headcount|unclear>",
  "pain_tags": ["<array of pain indicators>"],
  "score_fit": <0-50, ICP fitness score>,
  "score_pain": <0-40, pain intensity score>,
  "score_data_quality": <0-10, signal quality score>,
  "situation": "<SPIN: current situation>",
  "problem": "<SPIN: problem identified>",
  "implication": "<SPIN: implications of problem>",
  "need_payoff": "<SPIN: potential payoff>",
  "economic_buyer_guess": "<founder|ceo|gm|other>",
  "key_pain": "<40 words max>",
  "chaos_flags": ["<array of chaos indicators>"],
  "silver_bullet_phrases": ["<array of compelling phrases>"]
}}

**Scoring Guidelines:**
- score_fit (0-50): How well does this match the ICP? Consider company size, industry, region.
- score_pain (0-40): How intense is the marketing pain? Look for urgency, frustration, budget mentions.
- score_data_quality (0-10): How complete and reliable is the signal data?

Return ONLY the JSON object, no additional text."""

        # Dossier template (4B model)
        self.templates["dossier"] = """You are a strategic sales analyst. You've been given a high-scoring lead signal that needs a detailed dossier for the sales team.

**Signal Text:**
{signal_text}

**Classification Data:**
{classification_json}

**Your Task:**
Create a comprehensive strategic dossier that will help the sales team understand WHY this lead matters and HOW to approach them effectively.

**Required JSON Output:**
{{
  "snapshot": "<40 words max: executive summary>",
  "why_pain_bullets": [
    "<bullet 1: specific pain reason>",
    "<bullet 2: specific pain reason>",
    "<bullet 3: specific pain reason>"
  ],
  "uncomfortable_truth": "<1-2 sentences on consequences of inaction>",
  "reframe_suggestion": "<1 strong sentence reframing their problem>",
  "best_angle_bullets": [
    "<approach angle 1>",
    "<approach angle 2>",
    "<approach angle 3>"
  ],
  "challenger_insight": "<The one key insight that will make them rethink their approach>"
}}

**Guidelines:**
- Be specific and evidence-based
- Focus on strategic insights, not generic advice
- Use Challenger Sale principles
- Make it actionable for the sales team

Return ONLY the JSON object, no additional text."""

        # Embedding ICP template
        self.templates["icp_embedding"] = """Summarize the following Ideal Customer Profile (ICP) description into a dense, semantic representation suitable for embedding-based matching:

{icp_text}

Return a concise summary (2-3 sentences) that captures the essence of the ICP for semantic similarity matching."""

        # Signal embedding template
        self.templates["signal_embedding"] = """Summarize the following signal text into a dense, semantic representation suitable for embedding-based matching:

{signal_text}

Return a concise summary (2-3 sentences) that captures the key information for semantic similarity matching."""

    def _load_templates_from_disk(self):
        """Load custom templates from YAML/JSON files."""
        if not self.template_path.exists():
            logger.warning(f"Template path {self.template_path} does not exist. Creating it and falling back to defaults.")
            self.template_path.mkdir(parents=True, exist_ok=True)
            self._save_default_templates_to_disk()
            self._load_default_templates()
            return

        # Load all YAML and JSON files
        template_files = list(self.template_path.glob("*.yaml")) + list(self.template_path.glob("*.yml")) + list(self.template_path.glob("*.json"))

        if not template_files:
            logger.warning(f"No template files found in {self.template_path}. Creating defaults.")
            self._save_default_templates_to_disk()
            self._load_default_templates()
            return

        for file_path in template_files:
            try:
                with open(file_path, "r") as f:
                    if file_path.suffix in [".yaml", ".yml"]:
                        data = yaml.safe_load(f)
                    else:
                        data = json.load(f)

                # Each file should be a dict of template_name: template_text
                if isinstance(data, dict):
                    for template_name, template_text in data.items():
                        self.templates[template_name] = template_text
                        logger.debug(f"Loaded template '{template_name}' from {file_path.name}")
                else:
                    logger.warning(f"Template file {file_path.name} is not a dict. Skipping.")

            except Exception as e:
                logger.error(f"Failed to load template from {file_path.name}: {e}")

        # Fallback to defaults for missing templates
        default_manager = PromptTemplateManager(enable_custom=False)
        for template_name in ["classification", "dossier", "icp_embedding", "signal_embedding"]:
            if template_name not in self.templates:
                logger.warning(f"Template '{template_name}' not found in custom templates. Using default.")
                self.templates[template_name] = default_manager.templates[template_name]

    def _save_default_templates_to_disk(self):
        """Save default templates to disk for easy editing."""
        self._load_default_templates()

        # Save each template as a separate YAML file
        templates_to_save = {
            "classification.yaml": {"classification": self.templates["classification"]},
            "dossier.yaml": {"dossier": self.templates["dossier"]},
            "embeddings.yaml": {
                "icp_embedding": self.templates["icp_embedding"],
                "signal_embedding": self.templates["signal_embedding"]
            }
        }

        for filename, content in templates_to_save.items():
            file_path = self.template_path / filename
            try:
                with open(file_path, "w") as f:
                    yaml.dump(content, f, default_flow_style=False, sort_keys=False)
                logger.info(f"Saved default template to {file_path}")
            except Exception as e:
                logger.error(f"Failed to save template to {file_path}: {e}")

    def get_template(self, template_name: str) -> Optional[str]:
        """Get a template by name."""
        return self.templates.get(template_name)

    def render_template(self, template_name: str, **kwargs) -> str:
        """
        Render a template with variable interpolation.

        Args:
            template_name: Name of the template
            **kwargs: Variables to interpolate

        Returns:
            Rendered template string
        """
        template = self.get_template(template_name)
        if not template:
            logger.error(f"Template '{template_name}' not found")
            return ""

        try:
            return template.format(**kwargs)
        except KeyError as e:
            logger.error(f"Missing variable {e} in template '{template_name}'")
            return template
        except Exception as e:
            logger.error(f"Failed to render template '{template_name}': {e}")
            return template

    def reload_templates(self):
        """Reload templates from disk (useful for hot-reloading)."""
        if self.enable_custom:
            self._load_templates_from_disk()
            logger.info("Reloaded custom templates from disk")
        else:
            logger.warning("Custom templates not enabled. Cannot reload.")

    def list_templates(self) -> list[str]:
        """List all available template names."""
        return list(self.templates.keys())


# Singleton instance
_prompt_manager: Optional[PromptTemplateManager] = None


def get_prompt_manager() -> Optional[PromptTemplateManager]:
    """Get the singleton prompt template manager instance."""
    return _prompt_manager


def init_prompt_manager(template_path: str = "./prompts", enable_custom: bool = False) -> PromptTemplateManager:
    """Initialize the singleton prompt template manager."""
    global _prompt_manager
    _prompt_manager = PromptTemplateManager(template_path=template_path, enable_custom=enable_custom)
    return _prompt_manager
