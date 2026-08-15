"""Central configuration for DGAD.

Project rule: ALL thresholds and tunables live here. No magic numbers in
channel, gate, calibration, or eval code. Everything is overridable via
environment variables or a .env file (see .env.example).
"""

from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

DisagreementMetric = Literal["abs_diff", "region_conflict", "entropy"]
PolicyMode = Literal["block", "flag_and_pass", "observe_only"]
CalibrationMethod = Literal["platt", "isotonic"]


class Settings(BaseSettings):
    """Typed settings for the whole system, loaded from the environment."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Disagreement gate (core novelty; see docs/adr/0001-disagreement-gating.md)
    gate_t_low: float = 0.3
    """Below this calibrated score, all channels agreeing means PASS."""
    gate_t_high: float = 0.7
    """Above this calibrated score, all channels agreeing means BLOCK."""
    gate_t_d: float = 0.4
    """Minimum disagreement between channels that triggers ESCALATE."""
    gate_disagreement_metric: DisagreementMetric = "abs_diff"
    """How disagreement between channel scores is measured."""
    gate_escalation_rate_target: float = 0.15
    """Target ceiling for the fraction of traffic escalated to expensive verification."""

    # --- Policy
    policy_mode: PolicyMode = "block"
    """What to do with a BLOCK decision: block it, pass it with a flag, or only log it."""

    # --- Channel A: statistical (windowed perplexity, Jain et al.)
    perplexity_window: int = 16
    """Window size W in tokens for windowed perplexity."""
    perplexity_stride: int = 8
    """Stride S in tokens for windowed perplexity."""
    perplexity_model: str = "openai-community/gpt2"
    """Reference language model used to compute perplexity."""

    # --- Channel B / E models
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    """Sentence embedder for the semantic classifier and the representation offset."""

    # --- Channel C: behavioural probe
    behavioural_probe_k: int = 5
    """Number K of perturbations applied per contested prompt."""
    ollama_model: str = "qwen2.5:1.5b-instruct"
    """Local proxy model (via ollama) used by the behavioural probe."""
    ollama_base_url: str = "http://localhost:11434"

    # --- Channel E: representation offset
    offset_length_normalise: bool = False
    """Normalise the offset score by prompt length (long prompts drift naturally)."""

    # --- Channel D: LLM-as-a-judge
    judge_provider: Literal["anthropic", "openai", "ollama"] = "ollama"
    judge_model: str = "qwen2.5:1.5b-instruct"
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None

    # --- Calibration
    calibration_method: CalibrationMethod = "platt"
    """Score calibration method fitted on the validation split."""

    # --- Infrastructure
    database_url: str = "sqlite:///./dgad.db"
    """Audit log database. SQLite for local dev, PostgreSQL via docker compose."""
    redis_url: str | None = None
    """Score cache. None means use an in-process cache instead of Redis."""

    # --- Paths
    models_dir: str = "models"
    """Where trained heads and calibrators are persisted (joblib)."""
    data_dir: str = "data"
    """Dataset root; raw/interim/processed subdirs are gitignored."""

    # --- API / proxy
    api_key: str | None = None
    """If set, requests must carry this key (X-API-Key). None disables auth (dev only)."""
    upstream_base_url: str = "http://localhost:11434/v1"
    """Upstream LLM base URL for the OpenAI-compatible proxy."""

    # --- Judge cost accounting (USD per 1K tokens, for the cost comparison table)
    judge_cost_per_1k_input: float = 0.003
    judge_cost_per_1k_output: float = 0.015

    # --- Reproducibility
    random_seed: int = 42
    """Fixed seed for dataset splits, training runs, and the adversarial loop."""


def get_settings() -> Settings:
    """Construct a Settings instance from the environment and .env file."""
    return Settings()
