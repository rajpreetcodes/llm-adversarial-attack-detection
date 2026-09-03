# ADR 0005: Dashboard style: Utilitarian

## Status
Accepted.

## Context
The dashboard is how examiners meet the system; they look for two minutes.
Candidates considered: Utilitarian (technical, functional), Bento Box
(organised, friendly), Cybercore (futuristic "hacker" look).

## Decision
Utilitarian. Bento Box reads too friendly for a security audit tool; Cybercore
is the category reflex for "security" and reads as decoration, undermining the
rigour the project needs to project.

Tokens: strict 8px grid, hairline borders (#E7E5E4), flat surfaces, no
decorative shadows; paper #FAFAF9, ink #1C1917, muted #57534E, structural
accent slate-blue #3F4E6B, signal red #B91C1C (attacks/blocks), muted green
#15803D (pass). IBM Plex Sans for UI, JetBrains Mono for scores/hashes/
latency, Windows-safe fallbacks (Segoe UI, Consolas) so it renders offline.

Motion: utility only (count-up stats, 150-300 ms fade-up reveals, skeleton
loading, toasts), full prefers-reduced-motion static fallback. No
scroll-jacking, no WebGL, no ambient loops: it is a task-driven page.

## Consequences
- The disagreement scatter plot (the thesis made visible) is the hero;
  nothing decorative competes with it.
- All tokens live in dashboard/src/theme.ts and tailwind.config.js.
