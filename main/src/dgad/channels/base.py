"""The Channel contract. THIS MUST NOT BE BROKEN.

Every detection channel (A statistical, B semantic, C behavioural,
D judge, E representation offset) implements this interface. The ablation
study and the disagreement gate depend on channels being interchangeable.
"""

from abc import ABC, abstractmethod

from dgad.schemas import ChannelResult


class Channel(ABC):
    """Abstract detection channel."""

    name: str
    """Short stable identifier, used as the key in GateDecision.scores."""

    @abstractmethod
    def score(self, text: str) -> ChannelResult:
        """Score one normalised prompt.

        Args:
            text: The prompt after normalisation (dgad.normalise.normalise).

        Returns:
            A ChannelResult with a raw score in [0, 1]-ish range (higher is
            more attack-like), the measured latency, and optional metadata.
            calibrated_score is left None; the calibration layer fills it in.
        """
        ...
