"""Ollama wrapper for 1B and 4B models."""

import json
import asyncio
import httpx
import logging
from typing import Optional, Dict, Any
from config import Settings

logger = logging.getLogger(__name__)

class OllamaManager:
    """Manages Ollama model interactions (1B for routing, 4B for dossiers)."""

    def __init__(self):
        self.settings = Settings()
        self.base_url = self.settings.ollama_base_url
        self.model_1b = self.settings.ollama_model_1b
        self.model_4b = self.settings.ollama_model_4b
        self.client = httpx.AsyncClient(timeout=300)

    async def ensure_models_loaded(self):
        """Ensure both models are available in Ollama."""
        try:
            models = await self._list_models()
            model_names = [m["name"] for m in models]

            if self.model_1b not in model_names:
                logger.warning(f"Model {self.model_1b} not found. Pulling...")
                await self._pull_model(self.model_1b)

            if self.model_4b not in model_names:
                logger.warning(f"Model {self.model_4b} not found. Pulling...")
                await self._pull_model(self.model_4b)

            logger.info(f"✅ Both models ready: {self.model_1b}, {self.model_4b}")
        except Exception as e:
            logger.error(f"Error checking Ollama models: {e}")
            raise

    async def _list_models(self) -> list:
        """List available models in Ollama."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            return []

    async def _pull_model(self, model_name: str):
        """Pull a model from Ollama."""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/pull",
                json={"name": model_name},
                timeout=None,
            )
            response.raise_for_status()
            logger.info(f"✅ Model {model_name} pulled successfully")
        except Exception as e:
            logger.error(f"Error pulling model {model_name}: {e}")
            raise

    async def classify_signal(
        self,
        signal_text: str,
        icp_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Use Gemma 3 1B to quickly classify a signal.
        Returns structured JSON with ICP match, pain score, tags, SPIN/MEDDIC fields.
        """
        # Build classifier prompt
        icp_info = ""
        if icp_context:
            icp_info = f"""
ICP Context:
- Size buckets: {icp_context.get('size_buckets', [])}
- Industries: {icp_context.get('industries', [])}
- Pain keywords: {icp_context.get('pain_keywords', [])}
- Hiring keywords: {icp_context.get('hiring_keywords', [])}
"""

        prompt = f"""You are a lead classifier for Raptorflow, a marketing SaaS platform focused on small teams (<20 people) in India.
Analyze the signal text and return STRICT JSON. No extra text. ONLY JSON.

{icp_info}

Signal Text:
{signal_text}

Return exactly this JSON structure:
{{
    "icp_match": true/false,
    "size_bucket": "1" or "2-5" or "6-10" or "11-20" or "unknown",
    "region": "india" or "other" or "unknown",
    "role_type": "first_marketer" or "agency_replacement" or "extra_headcount" or "unclear",
    "pain_tags": ["list", "of", "tags"],
    "score_fit": 0-50,
    "score_pain": 0-40,
    "score_data_quality": 0-10,
    "reason_short": "max 25 words",
    "situation": "max 40 words",
    "problem": "max 40 words",
    "implication": "max 40 words",
    "need_payoff": "max 40 words",
    "economic_buyer_guess": "founder or ceo or gm or other",
    "key_pain": "max 40 words",
    "chaos_flags": ["list", "of", "flags"],
    "silver_bullet_phrases": ["list", "of", "phrases"]
}}"""

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_1b,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,  # Lower temperature for consistent JSON
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_ctx": 4096,  # Keep context small for 1B
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "").strip()

            # Try to extract JSON from response
            try:
                # Try direct JSON parse
                result = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to find JSON in the response
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    result = json.loads(response_text[start_idx:end_idx])
                else:
                    logger.warning(f"Could not parse JSON from 1B response: {response_text[:200]}")
                    result = self._default_classification()

            return result
        except Exception as e:
            logger.error(f"Error in classify_signal: {e}")
            return self._default_classification()

    async def generate_dossier(
        self,
        lead_json: Dict[str, Any],
        signal_snippets: list,
    ) -> Dict[str, str]:
        """
        Use Gemma 3 4B to generate rich context dossier for a hot lead.
        Only call this for leads scoring >70.
        """
        snippets_text = "\n".join([f"- {s}" for s in signal_snippets[:5]])  # Max 5 snippets

        prompt = f"""You are a senior growth advisor for Raptorflow, a marketing SaaS platform.
Given structured lead data + signal snippets, generate sharp, non-fluffy context.

Lead Data:
{json.dumps(lead_json, indent=2)}

Signal Snippets:
{snippets_text}

Return STRICT JSON with these fields:
{{
    "snapshot": "40 words max, one sentence on who they are",
    "why_pain_bullets": ["bullet 1 why they have marketing pain", "bullet 2", "bullet 3"],
    "uncomfortable_truth": "1-2 sentences on what happens if they don't fix this",
    "reframe_suggestion": "1 strong reframe sentence flipping their thinking",
    "best_angle_bullets": ["angle 1 to approach them", "angle 2", "angle 3"],
    "challenger_insight": "The one uncomfortable truth to lead with"
}}"""

        try:
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_4b,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.5,  # Slightly higher for better narrative
                        "top_p": 0.9,
                        "num_ctx": 8192,  # 4B can handle more context
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "").strip()

            try:
                result = json.loads(response_text)
            except json.JSONDecodeError:
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    result = json.loads(response_text[start_idx:end_idx])
                else:
                    logger.warning(f"Could not parse JSON from 4B dossier: {response_text[:200]}")
                    result = self._default_dossier()

            return result
        except Exception as e:
            logger.error(f"Error in generate_dossier: {e}")
            return self._default_dossier()

    def _default_classification(self) -> Dict[str, Any]:
        """Default classification when model fails."""
        return {
            "icp_match": False,
            "size_bucket": "unknown",
            "region": "unknown",
            "role_type": "unclear",
            "pain_tags": [],
            "score_fit": 0,
            "score_pain": 0,
            "score_data_quality": 0,
            "reason_short": "Classification failed",
            "situation": "",
            "problem": "",
            "implication": "",
            "need_payoff": "",
            "economic_buyer_guess": "unknown",
            "key_pain": "",
            "chaos_flags": [],
            "silver_bullet_phrases": [],
        }

    def _default_dossier(self) -> Dict[str, Any]:
        """Default dossier when model fails."""
        return {
            "snapshot": "Lead context generation failed.",
            "why_pain_bullets": [],
            "uncomfortable_truth": "Unable to generate insight.",
            "reframe_suggestion": "Unable to generate reframe.",
            "best_angle_bullets": [],
            "challenger_insight": "Unable to generate insight.",
        }
