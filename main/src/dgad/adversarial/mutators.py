"""Meaning-preserving mutation operators (final_plan.md Phase 6 step 1).

Used by the behavioural probe (Channel C) and the self-adversarial loop.
Every operator is pure, seeded, and keeps the perturbation budget small:
an optimised attack should break under these, a genuine prompt should not.
"""

import random
import re
import string

# ponytail: tiny built-in synonym map covers common words; WordNet is tried
# lazily and used when its data happens to be installed, never downloaded.
_SYNONYMS: dict[str, list[str]] = {
    "write": ["compose", "draft", "produce"],
    "how": ["in what way"],
    "make": ["create", "build"],
    "give": ["provide", "supply"],
    "tell": ["inform", "explain to"],
    "show": ["demonstrate", "present"],
    "ignore": ["disregard", "skip"],
    "instructions": ["directions", "guidelines"],
    "please": ["kindly"],
    "explain": ["describe", "clarify"],
    "help": ["assist", "aid"],
    "need": ["require", "want"],
}

_PUNCT = ",.;:!?-"


def char_swap(rng: random.Random, text: str, rate: float = 0.02) -> str:
    """Swap adjacent characters at the given rate (typo simulation)."""
    chars = list(text)
    n = max(1, int(len(chars) * rate))
    for _ in range(n):
        i = rng.randrange(max(1, len(chars) - 1))
        chars[i], chars[i + 1] = chars[i + 1], chars[i]
    return "".join(chars)


def char_drop(rng: random.Random, text: str, rate: float = 0.01) -> str:
    """Delete characters at the given rate (never whitespace-adjacent ends)."""
    chars = list(text)
    n = max(1, int(len(chars) * rate))
    for _ in range(n):
        i = rng.randrange(len(chars))
        del chars[i]
        if not chars:
            break
    return "".join(chars)


def whitespace_jitter(rng: random.Random, text: str) -> str:
    """Randomly add/remove spaces and punctuation, preserving words."""
    out = []
    for ch in text:
        out.append(ch)
        if ch == " " and rng.random() < 0.05:
            out.append(" ")
        elif ch in _PUNCT and rng.random() < 0.1:
            out.append(rng.choice(_PUNCT))
    return "".join(out)


def synonym_replace(rng: random.Random, text: str, max_replacements: int = 2) -> str:
    """Replace up to N words with synonyms (built-in map, WordNet if present)."""
    words = text.split()
    candidates = [i for i, w in enumerate(words)
                  if re.sub(r"[^a-z]", "", w.lower()) in _SYNONYMS]
    rng.shuffle(candidates)
    for i in candidates[:max_replacements]:
        key = re.sub(r"[^a-z]", "", words[i].lower())
        words[i] = words[i].replace(key, rng.choice(_SYNONYMS[key]))
    return " ".join(words)


_OPERATORS = [char_swap, char_drop, whitespace_jitter, synonym_replace]


def random_mutation(rng: random.Random, text: str, strength: int = 1) -> str:
    """Apply `strength` randomly chosen operators in sequence."""
    for _ in range(strength):
        op = rng.choice(_OPERATORS)
        text = op(rng, text)
    return text


def printable_junk(rng: random.Random, length: int) -> str:
    """Random printable-character run, used to build synthetic GCG-style suffixes."""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return "".join(rng.choice(alphabet) for _ in range(length))
