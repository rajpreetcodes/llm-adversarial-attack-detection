"""DGAD: Disagreement-Gated Adaptive Detection.

A security layer that inspects every LLM prompt before it reaches the model.
Cheap detectors score each prompt; when they disagree, only that contested
prompt is escalated to expensive verification.
"""

__version__ = "0.1.0"
