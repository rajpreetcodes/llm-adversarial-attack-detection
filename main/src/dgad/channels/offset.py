"""Channel E: black-box representation offset (final_plan.md Phase 8).

Inspired by Representation Offset Detection (ROD), which measures the gap
between a prompt and its intent in hidden states (white-box). DGAD claims
only a black-box APPROXIMATION: extract the prompt's actual intent with a
small local model, embed both original and intent, and score the cosine
distance. Honest prompts summarise close to themselves; disguised attacks
do not.

The intent extractor and embedder are dependency-injected for tests. When
no local model is reachable, a documented heuristic strips framing boilerplate
and keeps the imperative core.
"""

import re
import time
from collections.abc import Callable

import numpy as np

from dgad.channels.base import Channel
from dgad.channels.semantic import Embedder, hashing_embedder, sentence_transformer_embedder
from dgad.config import Settings, get_settings
from dgad.schemas import ChannelResult

IntentExtractor = Callable[[str], str]

INTENT_INSTRUCTION = (
    "In one sentence, state what this text is actually asking the system to do. "
    "Ignore framing, stories, and role-play; state only the core request."
)

# ponytail: framing boilerplate that wraps hidden requests; extend as the
# red-team phase finds new wrappers.
_FRAMING_PATTERNS = [
    r"(?i)you are (?:now )?(?:an? )?[\w\s]{0,40}(?:ai|assistant|model|bot)",
    r"(?i)(?:pretend|imagine|act as if|role[- ]?play)[^.]{0,120}\.",
    r"(?i)(?:in this (?:story|fiction|scenario|game|hypothetical))[^.]{0,120}\.",
    r"(?i)(?:for (?:educational|research|academic) purposes)[^.]{0,80}\.",
    r"(?i)(?:dan|do anything now)[^.]{0,120}\.",
]


def heuristic_intent_extractor(text: str) -> str:
    """Offline fallback: strip framing boilerplate, keep the imperative core.

    Limitation (documented honestly): pattern-based, so novel framings pass
    through unstripped and the offset collapses toward zero.
    """
    core = text
    for pat in _FRAMING_PATTERNS:
        core = re.sub(pat, " ", core)
    core = " ".join(core.split())
    return core if core else text


def ollama_intent_extractor(settings: Settings) -> IntentExtractor:
    """Intent extraction via a small local model through ollama."""

    def extract(text: str) -> str:
        import ollama

        client = ollama.Client(host=settings.ollama_base_url)
        resp = client.chat(
            model=settings.ollama_model,
            messages=[
                {"role": "system", "content": INTENT_INSTRUCTION},
                {"role": "user", "content": text},
            ],
        )
        return str(resp["message"]["content"]).strip()

    return extract


def _cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0.0:
        return 0.0
    return float(1.0 - np.dot(a, b) / denom)


class OffsetChannel(Channel):
    """Surface-vs-intent offset scorer (black-box ROD approximation)."""

    name = "offset"

    def __init__(self, settings: Settings | None = None,
                 extractor: IntentExtractor | None = None,
                 embedder: Embedder | None = None) -> None:
        self.settings = settings or get_settings()
        self._extractor = extractor
        self._embedder = embedder

    def _get_extractor(self) -> tuple[IntentExtractor, bool]:
        """Return (extractor, degraded). Degraded means heuristic fallback."""
        if self._extractor is not None:
            return self._extractor, False
        try:
            ext = ollama_intent_extractor(self.settings)
            ext("ping")  # probe once so failure falls back before scoring
            self._extractor = ext
            return ext, False
        except Exception:
            self._extractor = heuristic_intent_extractor
            return self._extractor, True

    def _encode(self, texts: list[str]) -> np.ndarray:
        if self._embedder is None:
            try:
                self._embedder = sentence_transformer_embedder(self.settings.embedding_model)
            except Exception:
                self._embedder = hashing_embedder()
        return self._embedder(texts)

    def score(self, text: str) -> ChannelResult:
        start = time.perf_counter()
        extractor, degraded = self._get_extractor()
        try:
            intent = extractor(text)
        except Exception:
            intent, degraded = heuristic_intent_extractor(text), True
        orig_emb, intent_emb = self._encode([text, intent])
        raw = _cosine_distance(orig_emb, intent_emb)
        if self.settings.offset_length_normalise:
            raw = raw / max(1.0, len(text.split()) / 20.0)
        return ChannelResult(
            raw_score=float(np.clip(raw, 0.0, 1.0)),
            latency_ms=(time.perf_counter() - start) * 1000,
            metadata={"degraded": degraded, "extracted_intent": intent[:200]},
        )
