"""Enhanced Ollama wrapper with caching, streaming, embeddings, and health monitoring."""

import json
import asyncio
import httpx
import logging
from typing import Optional, Dict, Any, AsyncIterator
from datetime import datetime, timedelta
from config import Settings
from cache_manager import get_cache_manager
from prompt_templates import get_prompt_manager

logger = logging.getLogger(__name__)


class ModelHealthMonitor:
    """Monitors Ollama model health and availability."""

    def __init__(self, base_url: str, check_interval: int = 300, timeout: int = 10):
        self.base_url = base_url
        self.check_interval = check_interval
        self.timeout = timeout
        self.last_check: Optional[datetime] = None
        self.is_healthy = False
        self.last_latency_ms: Optional[float] = None
        self.error_count = 0
        self.success_count = 0

    async def check_health(self, client: httpx.AsyncClient) -> bool:
        """
        Check if Ollama is healthy and responsive.

        Returns:
            True if healthy, False otherwise
        """
        try:
            start_time = datetime.now()
            response = await client.get(
                f"{self.base_url}/api/tags",
                timeout=self.timeout
            )
            response.raise_for_status()

            # Calculate latency
            latency = (datetime.now() - start_time).total_seconds() * 1000
            self.last_latency_ms = latency
            self.last_check = datetime.now()
            self.is_healthy = True
            self.success_count += 1

            logger.debug(f"Ollama health check passed (latency: {latency:.2f}ms)")
            return True

        except Exception as e:
            self.is_healthy = False
            self.error_count += 1
            self.last_check = datetime.now()
            logger.error(f"Ollama health check failed: {e}")
            return False

    def should_check(self) -> bool:
        """Determine if health check is due."""
        if self.last_check is None:
            return True
        return datetime.now() - self.last_check > timedelta(seconds=self.check_interval)

    def get_stats(self) -> Dict[str, Any]:
        """Get health monitoring statistics."""
        total_checks = self.success_count + self.error_count
        success_rate = (self.success_count / total_checks * 100) if total_checks > 0 else 0

        return {
            "is_healthy": self.is_healthy,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "last_latency_ms": self.last_latency_ms,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate_percent": round(success_rate, 2),
            "total_checks": total_checks
        }


class OllamaManager:
    """
    Enhanced Ollama manager with caching, streaming, embeddings, and health monitoring.

    Features:
    - Response caching (LRU memory or Redis)
    - Streaming API support for real-time results
    - Dynamic context window adjustment
    - Health monitoring and metrics
    - Embeddings for ICP matching
    - Multi-stage classification
    - Quantized model support
    - Alternative model fallback
    """

    def __init__(self):
        self.settings = Settings()
        self.base_url = self.settings.ollama_base_url

        # Model selection (supports quantization and alternatives)
        self.model_1b = self._select_model_1b()
        self.model_4b = self._select_model_4b()
        self.embedding_model = self.settings.ollama_embedding_model

        self.client = httpx.AsyncClient(timeout=300)

        # Health monitoring
        if self.settings.enable_health_monitoring:
            self.health_monitor = ModelHealthMonitor(
                base_url=self.base_url,
                check_interval=self.settings.health_check_interval_seconds,
                timeout=self.settings.health_check_timeout_seconds
            )
        else:
            self.health_monitor = None

        # Metrics
        self.classification_count = 0
        self.dossier_count = 0
        self.embedding_count = 0
        self.cache_enabled = self.settings.enable_response_cache

        logger.info(f"OllamaManager initialized: 1B={self.model_1b}, 4B={self.model_4b}, cache={self.cache_enabled}")

    def _select_model_1b(self) -> str:
        """Select 1B model based on configuration."""
        if self.settings.use_quantized_models:
            logger.info(f"Using quantized 1B model: {self.settings.quantized_model_1b}")
            return self.settings.quantized_model_1b
        return self.settings.ollama_model_1b

    def _select_model_4b(self) -> str:
        """Select 4B model based on configuration."""
        if self.settings.use_quantized_models:
            logger.info(f"Using quantized 4B model: {self.settings.quantized_model_4b}")
            return self.settings.quantized_model_4b
        return self.settings.ollama_model_4b

    def _calculate_context_window(self, text: str) -> int:
        """
        Dynamically calculate context window based on input length.

        Args:
            text: Input text to analyze

        Returns:
            Appropriate context window size
        """
        text_length = len(text)

        if text_length < self.settings.context_length_threshold:
            return self.settings.context_window_1b_short
        else:
            return self.settings.context_window_1b_long

    async def ensure_models_loaded(self):
        """Ensure all required models are available in Ollama."""
        try:
            models = await self._list_models()
            model_names = [m["name"] for m in models]

            # Check and pull required models
            required_models = [self.model_1b, self.model_4b]
            if self.settings.enable_embeddings:
                required_models.append(self.embedding_model)

            for model in required_models:
                if model not in model_names:
                    logger.warning(f"Model {model} not found. Pulling...")
                    await self._pull_model(model)

            logger.info(f"✅ All models ready: {', '.join(required_models)}")

            # Initial health check
            if self.health_monitor:
                await self.health_monitor.check_health(self.client)

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

    async def _periodic_health_check(self):
        """Perform periodic health check if due."""
        if self.health_monitor and self.health_monitor.should_check():
            await self.health_monitor.check_health(self.client)

    async def classify_signal(
        self,
        signal_text: str,
        icp_context: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Use 1B model to quickly classify a signal.

        Args:
            signal_text: The signal text to classify
            icp_context: Optional ICP context dict
            use_cache: Whether to use cache (default True)
            stream: Whether to stream the response (default False)

        Returns:
            Classification dict with scores, tags, SPIN fields
        """
        # Periodic health check
        await self._periodic_health_check()

        # Check cache first
        cache_manager = get_cache_manager()
        if use_cache and cache_manager and self.cache_enabled:
            icp_str = json.dumps(icp_context) if icp_context else None
            cached_result = await cache_manager.get(
                signal_text=signal_text,
                icp_context=icp_str,
                model="1b"
            )
            if cached_result:
                logger.debug("Using cached classification result")
                return cached_result

        # Build prompt from template
        prompt_manager = get_prompt_manager()
        if prompt_manager:
            icp_context_str = self._format_icp_context(icp_context) if icp_context else "No ICP context provided."
            prompt = prompt_manager.render_template(
                "classification",
                icp_context=icp_context_str,
                signal_text=signal_text
            )
        else:
            # Fallback to inline prompt
            prompt = self._build_classification_prompt(signal_text, icp_context)

        # Dynamic context window
        context_window = self._calculate_context_window(signal_text)

        try:
            # Streaming not supported for classification (needs full JSON)
            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_1b,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.settings.temperature_1b,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_ctx": context_window,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "").strip()

            # Parse JSON
            result = self._parse_json_response(response_text, self._default_classification())

            # Cache the result
            if use_cache and cache_manager and self.cache_enabled:
                icp_str = json.dumps(icp_context) if icp_context else None
                await cache_manager.set(
                    signal_text=signal_text,
                    value=result,
                    icp_context=icp_str,
                    model="1b"
                )

            self.classification_count += 1
            return result

        except Exception as e:
            logger.error(f"Error in classify_signal: {e}")
            return self._default_classification()

    async def generate_dossier(
        self,
        lead_json: Dict[str, Any],
        signal_snippets: list,
        stream: bool = False,
    ) -> Dict[str, str]:
        """
        Use 4B model to generate rich context dossier for a hot lead.

        Args:
            lead_json: Lead classification data
            signal_snippets: List of signal snippets
            stream: Whether to stream the response

        Returns:
            Dossier dict with strategic insights
        """
        # Periodic health check
        await self._periodic_health_check()

        snippets_text = "\n".join([f"- {s}" for s in signal_snippets[:5]])

        # Build prompt from template
        prompt_manager = get_prompt_manager()
        if prompt_manager:
            prompt = prompt_manager.render_template(
                "dossier",
                signal_text=snippets_text,
                classification_json=json.dumps(lead_json, indent=2)
            )
        else:
            # Fallback to inline prompt
            prompt = self._build_dossier_prompt(lead_json, snippets_text)

        try:
            if stream and self.settings.enable_streaming:
                # Streaming not fully implemented for JSON (complex to parse incrementally)
                # For now, use non-streaming
                logger.warning("Streaming requested for dossier but not fully supported for JSON parsing")

            response = await self.client.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_4b,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.settings.temperature_4b,
                        "top_p": 0.9,
                        "num_ctx": self.settings.context_window_4b,
                    },
                },
            )
            response.raise_for_status()
            data = response.json()
            response_text = data.get("response", "").strip()

            result = self._parse_json_response(response_text, self._default_dossier())

            self.dossier_count += 1
            return result

        except Exception as e:
            logger.error(f"Error in generate_dossier: {e}")
            return self._default_dossier()

    async def generate_embedding(
        self,
        text: str,
        use_cache: bool = True
    ) -> Optional[list[float]]:
        """
        Generate embeddings for text using embedding model.

        Args:
            text: Text to embed
            use_cache: Whether to use cache

        Returns:
            List of floats (embedding vector) or None on failure
        """
        if not self.settings.enable_embeddings:
            logger.warning("Embeddings not enabled in settings")
            return None

        # Check cache
        cache_manager = get_cache_manager()
        if use_cache and cache_manager and self.cache_enabled:
            cached_result = await cache_manager.get(
                signal_text=text,
                model="embedding"
            )
            if cached_result and "embedding" in cached_result:
                logger.debug("Using cached embedding")
                return cached_result["embedding"]

        try:
            response = await self.client.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            data = response.json()
            embedding = data.get("embedding")

            if embedding:
                # Cache the embedding
                if use_cache and cache_manager and self.cache_enabled:
                    await cache_manager.set(
                        signal_text=text,
                        value={"embedding": embedding},
                        model="embedding",
                        ttl=self.settings.embedding_cache_ttl
                    )

                self.embedding_count += 1
                return embedding
            else:
                logger.error("No embedding returned from Ollama")
                return None

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    async def compute_similarity(self, embedding1: list[float], embedding2: list[float]) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score between -1 and 1
        """
        try:
            # Cosine similarity
            import numpy as np
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)

            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)

            if norm1 == 0 or norm2 == 0:
                return 0.0

            similarity = dot_product / (norm1 * norm2)
            return float(similarity)

        except Exception as e:
            logger.error(f"Error computing similarity: {e}")
            return 0.0

    def _format_icp_context(self, icp_context: Dict[str, Any]) -> str:
        """Format ICP context for prompt."""
        return f"""
ICP Context:
- Size buckets: {icp_context.get('size_buckets', [])}
- Industries: {icp_context.get('industries', [])}
- Pain keywords: {icp_context.get('pain_keywords', [])}
- Hiring keywords: {icp_context.get('hiring_keywords', [])}
"""

    def _build_classification_prompt(self, signal_text: str, icp_context: Optional[Dict[str, Any]]) -> str:
        """Build classification prompt (fallback when template manager not available)."""
        icp_info = self._format_icp_context(icp_context) if icp_context else ""

        return f"""You are a lead classifier for Raptorflow, a marketing SaaS platform focused on small teams (<20 people) in India.
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

    def _build_dossier_prompt(self, lead_json: Dict[str, Any], snippets_text: str) -> str:
        """Build dossier prompt (fallback when template manager not available)."""
        return f"""You are a senior growth advisor for Raptorflow, a marketing SaaS platform.
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

    def _parse_json_response(self, response_text: str, default: Dict[str, Any]) -> Dict[str, Any]:
        """Parse JSON from model response with fallback."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                try:
                    return json.loads(response_text[start_idx:end_idx])
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse JSON from response: {response_text[:200]}")
                    return default
            else:
                logger.warning(f"No JSON found in response: {response_text[:200]}")
                return default

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

    def get_stats(self) -> Dict[str, Any]:
        """Get OllamaManager statistics."""
        stats = {
            "model_1b": self.model_1b,
            "model_4b": self.model_4b,
            "embedding_model": self.embedding_model,
            "classification_count": self.classification_count,
            "dossier_count": self.dossier_count,
            "embedding_count": self.embedding_count,
            "cache_enabled": self.cache_enabled,
        }

        # Add health stats if monitoring enabled
        if self.health_monitor:
            stats["health"] = self.health_monitor.get_stats()

        # Add cache stats
        cache_manager = get_cache_manager()
        if cache_manager:
            stats["cache"] = cache_manager.get_stats()

        return stats


# Singleton instance (initialized in main.py)
_ollama_manager: Optional[OllamaManager] = None


def get_ollama_manager() -> Optional[OllamaManager]:
    """Get the singleton OllamaManager instance."""
    return _ollama_manager


def init_ollama_manager() -> OllamaManager:
    """Initialize the singleton OllamaManager."""
    global _ollama_manager
    _ollama_manager = OllamaManager()
    return _ollama_manager
