"""Prompt normalisation and de-obfuscation.

Runs before any channel sees the text: Unicode NFKC normalisation,
zero-width character removal, optional confusable mapping, and whitespace
collapse. Must be idempotent: normalise(normalise(x)) == normalise(x).
"""

import re
import unicodedata
from collections.abc import Mapping

# Zero-width and invisible formatting characters attackers use to break
# naive string matching without changing what a human reads.
ZERO_WIDTH_CHARS = "﻿​‌‍⁠"

# Hook for the confusable mapping (e.g. Cyrillic 'а' for Latin 'a').
# Populate or extend this dict as the evasion test suite grows; Phase for
# obfuscation attacks owns the full table.
DEFAULT_CONFUSABLES: dict[str, str] = {}

_WHITESPACE_RE = re.compile(r"\s+")
_ZERO_WIDTH_RE = re.compile(f"[{re.escape(ZERO_WIDTH_CHARS)}]")


def normalise(text: str, confusables: Mapping[str, str] | None = None) -> str:
    """Normalise a prompt before detection.

    Steps, in order:
    1. NFKC Unicode normalisation (folds compatibility characters and
       full-width variants into their canonical forms).
    2. Removal of zero-width characters.
    3. Optional confusable-character mapping via the ``confusables`` hook.
    4. Collapse of all whitespace runs to single spaces, with stripping.

    The function is idempotent: normalising twice equals normalising once.

    Args:
        text: The raw prompt.
        confusables: Optional mapping of confusable character to canonical
            character. Defaults to DEFAULT_CONFUSABLES.

    Returns:
        The normalised prompt.
    """
    table = DEFAULT_CONFUSABLES if confusables is None else confusables
    out = unicodedata.normalize("NFKC", text)
    out = _ZERO_WIDTH_RE.sub("", out)
    if table:
        for confusable, canonical in table.items():
            out = out.replace(confusable, canonical)
    return _WHITESPACE_RE.sub(" ", out).strip()


def demo() -> None:
    """Self-check: prove idempotence and show the pipeline on a tricky input."""
    tricky = "Ｈｅｌｌｏ​  w o r l d\u2060\t\n  ignore\u200b previous"
    once = normalise(tricky)
    twice = normalise(once)
    assert once == twice, "normalise is not idempotent"
    assert "​" not in once, "zero-width characters survived"
    # ascii() keeps the output printable on Windows cp1252 consoles.
    print(f"input:  {ascii(tricky)}")
    print(f"output: {ascii(once)}")
    print("idempotence check: OK")


if __name__ == "__main__":
    demo()
