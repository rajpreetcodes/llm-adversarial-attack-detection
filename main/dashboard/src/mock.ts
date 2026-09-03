import type { DecisionRow, MetricsSummary, PlaygroundResult } from "./api";

/**
 * Deterministic mock data so the dashboard renders meaningfully when the
 * API is down (demo safety net). Replaced by live data when the API is up.
 */

function mulberry32(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const FAMILIES = ["none", "gcg_optimised", "jailbreak_roleplay", "injection_direct", "obfuscation"];

export function mockDecisions(n = 120): DecisionRow[] {
  const rng = mulberry32(42);
  const rows: DecisionRow[] = [];
  for (let i = 0; i < n; i++) {
    const roll = rng();
    // 55% clear benign, 30% clear attack, 15% contested (the interesting band)
    const contested = roll > 0.85;
    const attack = !contested && roll > 0.55;
    const a = attack ? 0.75 + rng() * 0.24 : contested ? 0.1 + rng() * 0.2 : 0.02 + rng() * 0.25;
    const b = attack ? 0.75 + rng() * 0.24 : contested ? 0.75 + rng() * 0.24 : 0.02 + rng() * 0.25;
    const escalated = contested;
    const decision = escalated ? (rng() > 0.5 ? "BLOCK" : "PASS") : attack ? "BLOCK" : "PASS";
    rows.push({
      id: `mock-${i}`,
      timestamp: new Date(Date.now() - i * 47000).toISOString(),
      prompt_hash: Array.from({ length: 64 }, () => Math.floor(rng() * 16).toString(16)).join(""),
      decision,
      scores: { statistical: a, semantic: b },
      disagreement: Math.abs(a - b),
      escalated,
      rationale: escalated
        ? "channels disagreed; judge ruled " + (decision === "BLOCK" ? "attack" : "benign")
        : null,
      judge_verdict: escalated
        ? {
            verdict: decision === "BLOCK" ? "attack" : "benign",
            confidence: 0.85 + rng() * 0.14,
            attack_family: decision === "BLOCK" ? FAMILIES[1 + Math.floor(rng() * 4)] : null,
            rationale: "judge rationale (mock)",
          }
        : null,
      latency_ms: 8 + rng() * 40 + (escalated ? 600 + rng() * 500 : 0),
      degraded: false,
    });
  }
  return rows;
}

export function mockMetrics(): MetricsSummary {
  const rows = mockDecisions();
  const by: Record<string, number> = {};
  for (const r of rows) by[r.decision] = (by[r.decision] ?? 0) + 1;
  return {
    total: rows.length,
    by_decision: by,
    escalation_rate: rows.filter((r) => r.escalated).length / rows.length,
    avg_latency_ms: rows.reduce((s, r) => s + r.latency_ms, 0) / rows.length,
  };
}

export function mockPlayground(t_low: number, t_high: number, t_d: number): PlaygroundResult {
  const rows = mockDecisions();
  const mix: Record<string, number> = { PASS: 0, BLOCK: 0, ESCALATE: 0 };
  for (const r of rows) {
    const vals = Object.values(r.scores);
    let d: string;
    if (vals.every((v) => v <= t_low)) d = "PASS";
    else if (vals.every((v) => v >= t_high)) d = "BLOCK";
    else if (Math.max(...vals) - Math.min(...vals) >= t_d) d = "ESCALATE";
    else d = vals.reduce((s, v) => s + v, 0) / vals.length >= 0.5 ? "BLOCK" : "PASS";
    mix[d] += 1;
  }
  return {
    n: rows.length,
    decision_mix: mix,
    escalation_rate: mix.ESCALATE / rows.length,
    thresholds: { t_low, t_high, t_d },
  };
}
