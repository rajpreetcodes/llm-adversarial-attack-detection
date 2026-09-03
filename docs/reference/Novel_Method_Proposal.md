---
title: "PRISM: A Novel Detection Method Proposal (response to mentor novelty objection)"
date: 2026-07-28
status: draft for team + mentor discussion
authors: prepared for Rajpreet Khurana (K033), Sumit Pandey (K044), Dhruv Rathod (K055)
note: "This document proposes the METHOD and the SCIENCE. All implementation code is to be written by the team."
---

# PRISM: Detecting Adversarial Prompts via Score-Trajectory Instability under Meaning-Preserving Transformations

## 1. The mentor's objection, restated honestly

Dr. Sharma's critique: the synopsis pipeline (perplexity tier + embedding classifier tier + LLM-judge tier with calibrated fusion) is an *ensemble of three known detectors*. Each tier is a published method; the fusion is standard score calibration. The architecture matches existing open-source stacks (Rebuff, LLM Guard) closely enough that the contribution reads as integration engineering, not research.

The objection is correct. The fix is not to swap components. The fix is to add a **new detection signal that none of the components produces on its own**, so the system measures something no prior detector measures.

## 2. First-principles teardown (why every current tier is the same idea)

Strip the three tiers to primitives:

| Tier | What it computes |
|---|---|
| Perplexity filter | one static score of the frozen prompt text |
| Embedding classifier | one static score of the frozen prompt text |
| LLM judge | one static verdict on the frozen prompt text |

Every existing detector in the synopsis, and almost every detector in the literature (Prompt Guard, InjecGuard, Llama Guard, perplexity filters), shares one unexamined convention: **detection is a single-pass function of a single, frozen input**. The prompt is photographed once and the photograph is classified.

That convention is not physics. It is an inherited habit from spam filtering and malware signature scanning. Discard it, and a new axis of measurement appears: **how detection scores MOVE when the input is transformed without changing its meaning**. Measure the derivative, not just the value.

## 3. The core invention

### 3.1 The physical intuition

Adversarial prompts are, by construction, *fragile objects* in semantic space:

- A GCG suffix is a precise token sequence found by gradient search. Paraphrase it, translate it and back, or even normalize its characters, and the optimized structure shatters. The synopsis's own ref [9] (windowed perplexity) exists precisely because these suffixes are locally improbable.
- An obfuscated injection (base64, leetspeak, Unicode homoglyphs, payload splitting: the exact evasions Hackett et al. [13] used to achieve up to 100% bypass) *changes drastically* under normalization. Decode it and it suddenly looks like an attack; leave it enc