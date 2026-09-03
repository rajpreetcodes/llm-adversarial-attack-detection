"""Channel B: semantic classifier (final_plan.md Phase 3).

Embeds each prompt (meaning, not surface) and runs a logistic-regression
head. Catches fluent role-play jailbreaks that Channel A's statistics find
perfectly normal; the complementary blind-spot pattern between A and B is
the empirical justification for the disagreement gate.

The embedder is dependency-injected for tests; the default lazy-loads
all-MiniLM-L6-v2. A hashing fallback embedder keeps offline runs (CI,
synthetic eval) working with zero downloads.
"""

import hashlib
import time
from collections.abc import Callable
from pathlib import Path

import joblib
import numpy as np

from dgad.channels.base import Channel
from dgad.config import Settings, get_settings
from dgad.schemas import ChannelResult

Embedder = Callable[[list[str]], np.ndarray]

_MODEL = None


def sentence_transformer_embedder(model_name: str) -> Embedder:
    """Lazy singleton SentenceTransformer embedder."""
    global _MODEL
    if _MODEL is None:
        from sentence_transformers import SentenceTransformer

        _MODEL = SentenceTransformer(model_name)

    def encode(texts: list[str]) -> np.ndarray:
        return np.asarray(_MODEL.encode(texts, convert_to_numpy=True), dtype=float)

    return encode


def hashing_embedder(dim: int = 384) -> Embedder:
    """Deterministic offline embedder: hashed token counts + char n-grams.

    ponytail: not a semantic model, but separable enough for the synthetic
    evaluation and CI; real runs use the SentenceTransformer above.
    """

    def encode(texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), dim), dtype=float)
        for r, text in enumerate(texts):
            for tok in text.lower().split():
                h = int(hashlib.sha256(tok.encode()).hexdigest(), 16)
                out[r, h % dim] += 1.0
            low = text.lower()
            for i in range(max(0, len(low) - 2)):
                h = int(hashlib.sha256(low[i:i + 3].encode()).hexdigest(), 16)
                out[r, dim // 2 + h % (dim // 2)] += 0.5
            norm = np.linalg.norm(out[r])
            if norm > 0:
                out[r] /= norm
        return out

    return encode


class SemanticChannel(Channel):
    """Embedding + logistic-regression attack classifier."""

    name = "semantic"

    def __init__(self, settings: Settings | None = None,
                 embedder: Embedder | None = None) -> None:
        self.settings = settings or get_settings()
        self._embedder = embedder
        self._embedder_name = "custom" if embedder else self.settings.embedding_model
        self._head = None

    def _encode(self, texts: list[str]) -> np.ndarray:
        if self._embedder is None:
            try:
                self._embedder = sentence_transformer_embedder(self.settings.embedding_model)
                self._embedder_name = self.settings.embedding_model
            except Exception:
                self._embedder = hashing_embedder()
                self._embedder_name = "hashing"
        return self._embedder(texts)

    def fit(self, texts: list[str], labels: list[int]) -> "SemanticChannel":
        """Train the logistic-regression head on cached embeddings."""
        from sklearn.linear_model import LogisticRegression

        x = self._encode(texts)
        self._head = LogisticRegression(max_iter=1000).fit(x, np.asarray(labels))
        return self

    def save(self, directory: str | Path) -> Path:
        """Persist the head AND the embedder identity (they are a pair)."""
        path = Path(directory) / "channel_b_head.joblib"
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self._head, path)
        (Path(directory) / "channel_b_embedder.txt").write_text(self._embedder_name)
        return path

    def load(self, directory: str | Path) -> "SemanticChannel":
        path = Path(directory) / "channel_b_head.joblib"
        self._head = joblib.load(path) if path.exists() else None
        marker = Path(directory) / "channel_b_embedder.txt"
        # embedder must match the one the head was trained on
        if marker.exists() and marker.read_text().strip() == "hashing":
            self._embedder = hashing_embedder()
            self._embedder_name = "hashing"
        return self

    def score(self, text: str) -> ChannelResult:
        start = time.perf_counter()
        if self._head is None:
            raise RuntimeError(
                "Channel B head is not trained: run `python -m dgad.eval.runner --train` "
                "or SemanticChannel.fit(...) first"
            )
        emb = self._encode([text])
        raw = float(self._head.predict_proba(emb)[0, 1])
        return ChannelResult(
            raw_score=raw,
            latency_ms=(time.perf_counter() - start) * 1000,
            metadata={"embedding_dim": int(emb.shape[1])},
        )


def main() -> None:
    """Train Channel B on the processed training split.

    Usage: python -m dgad.channels.semantic --train
    """
    import sys

    import pandas as pd

    settings = get_settings()
    if "--train" not in sys.argv:
        print("usage: python -m dgad.channels.semantic --train")
        raise SystemExit(2)
    train_path = Path(settings.data_dir) / "processed" / "train.csv"
    df = pd.read_csv(train_path)
    ch = SemanticChannel(settings)
    ch.fit(df["text"].tolist(), df["label"].tolist())
    path = ch.save(settings.models_dir)
    print(f"trained on {len(df)} rows, saved head to {path}")


if __name__ == "__main__":
    main()
