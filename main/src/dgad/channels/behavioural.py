"""Channel C: black-box behavioural probe (final_plan.md Phase 6).

An optimised attack prompt is brittle: tuned character by character, it
collapses under small meaning-preserving perturbation. A genuine question is
robust. This channel generates K mutated variants of a contested prompt,
runs them through a small LOCAL proxy model, and scores the swing in the
model's willingness to comply.

Known limitation (cite "The Consistency Confound" in the report): this
signal is weak in isolation against well-aligned models, which is exactly
why DGAD uses it only as a tie-breaker on the small contested subset, never
as a primary detector.
"""

import random
import time
from collections.abc import Callable

import numpy as np

from dgad.adversarial import mutators
from dgad.channels.base import Channel
from dgad.config import Settings, get_settings
from dgad.schemas import ChannelResult

ProbeModel = Callable[[str], str]

# Transparent, documented refusal detector: curated refusal phrases.
# Limitation: phrasing drift evades it; the eval report measures this.
REFUSAL_PHRASES = [
    "i cannot", "i can't", "i am unable", "i'm unable", "i will not", "i won't",
    "cannot assist", "cannot help", "cannot provide", "against my guidelines",
    "not able to", "must refuse", "i apologize", "i'm sorry", "as an ai",
]


def is_refusal(response: str) -> bool:
    """True when the response looks like a refusal."""
    low = response.lower()
    return any(p in low for p in REFUSAL_PHRASES)


def ollama_probe(settings: Settings) -> ProbeModel:
    """Probe model via ollama (zero API cost; K calls per contested prompt)."""

    def generate(prompt: str) -> str:
        import ollama

        client = ollama.Client(host=settings.ollama_base_url)
        resp = client.chat(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return str(resp["message"]["content"])

    return generate


class BehaviouralChannel(Channel):
    """Compliance-variance scorer over K perturbations of the prompt."""

    name = "behavioural"

    def __init__(self, settings: Settings | None = None,
                 probe: ProbeModel | None = None) -> None:
        self.settings = settings or get_settings()
        self._probe = probe

    def score(self, text: str) -> ChannelResult:
        start = time.perf_counter()
        k = self.settings.behavioural_probe_k
        probe = self._probe
        degraded = False
        if probe is None:
            try:
                probe = ollama_probe(self.settings)
                probe("ping")  # reachability check before spending K calls
            except Exception:
                degraded = True
        traces: list[dict] = []
        if degraded:
            # ponytail: neutral 0.5 with degraded flag; the gate treats this
            # channel's contribution as uninformative rather than crashing.
            return ChannelResult(
                raw_score=0.5,
                latency_ms=(time.perf_counter() - start) * 1000,
                metadata={"degraded": True, "reason": "probe model unreachable"},
            )
        rng = random.Random(self.settings.random_seed)
        variants = [text] + [mutators.random_mutation(rng, text) for _ in range(k)]
        compliance: list[float] = []
        assert probe is not None
        for variant in variants:
            try:
                response = probe(variant)
                refused = is_refusal(response)
            except Exception:
                response, refused = "", True  # failed call counts as refusal
            compliance.append(0.0 if refused else 1.0)
            traces.append({"variant": variant[:200], "refused": refused,
                           "response_head": response[:120]})
        base, perturbed = compliance[0], np.array(compliance[1:])
        swing = float(np.abs(perturbed - base).mean()) if len(perturbed) else 0.0
        variance = float(np.var(compliance))
        raw = float(np.clip(0.5 * swing + 0.5 * min(variance * 4.0, 1.0), 0.0, 1.0))
        return ChannelResult(
            raw_score=raw,
            latency_ms=(time.perf_counter() - start) * 1000,
            metadata={
                "degraded": False,
                "k": k,
                "compliance_swing": swing,
                "compliance_variance": variance,
                "traces": traces,
            },
        )
