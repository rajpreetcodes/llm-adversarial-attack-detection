import axios from "axios";
import { z } from "zod";

const api = axios.create({ baseURL: "/", timeout: 8000 });

export const DecisionSchema = z.object({
  id: z.string(),
  timestamp: z.string().nullable(),
  prompt_hash: z.string(),
  decision: z.enum(["PASS", "BLOCK", "ESCALATE"]),
  scores: z.record(z.string(), z.number()),
  disagreement: z.number(),
  escalated: z.boolean(),
  rationale: z.string().nullable(),
  judge_verdict: z
    .object({
      verdict: z.enum(["attack", "benign"]),
      confidence: z.number(),
      attack_family: z.string().nullable(),
      rationale: z.string(),
    })
    .nullable(),
  latency_ms: z.number(),
  degraded: z.boolean().default(false),
});
export type DecisionRow = z.infer<typeof DecisionSchema>;

export const MetricsSummarySchema = z.object({
  total: z.number(),
  by_decision: z.record(z.string(), z.number()),
  escalation_rate: z.number(),
  avg_latency_ms: z.number(),
});
export type MetricsSummary = z.infer<typeof MetricsSummarySchema>;

export const PlaygroundResultSchema = z.object({
  n: z.number(),
  decision_mix: z.record(z.string(), z.number()),
  escalation_rate: z.number(),
  thresholds: z.object({ t_low: z.number(), t_high: z.number(), t_d: z.number() }),
});
export type PlaygroundResult = z.infer<typeof PlaygroundResultSchema>;

export const ChannelResultSchema = z.object({
  raw_score: z.number(),
  calibrated_score: z.number().nullable(),
  latency_ms: z.number(),
  metadata: z.record(z.string(), z.unknown()).default({}),
});

export const DetectResponseSchema = z.object({
  decision: z.enum(["PASS", "BLOCK", "ESCALATE"]),
  scores: z.record(z.string(), z.number()),
  disagreement: z.number(),
  rationale: z.string().nullable().default(null),
  escalated: z.boolean(),
  latency_ms: z.number(),
  channel_results: z.record(z.string(), ChannelResultSchema).default({}),
  degraded: z.boolean().default(false),
  metadata: z.object({
    missing_required_channels: z.array(z.string()).default([]),
    escalation_degraded: z.boolean().default(false),
  }).passthrough().default({ missing_required_channels: [], escalation_degraded: false }),
});
export type DetectResponse = z.infer<typeof DetectResponseSchema>;

export async function fetchDecisions(limit = 100): Promise<DecisionRow[]> {
  const { data } = await api.get(`/admin/decisions?limit=${limit}`);
  return z.array(DecisionSchema).parse(data);
}

export async function fetchMetricsSummary(): Promise<MetricsSummary> {
  const { data } = await api.get("/admin/metrics-summary");
  return MetricsSummarySchema.parse(data);
}

export async function postPlayground(
  t: { t_low: number; t_high: number; t_d: number },
): Promise<PlaygroundResult> {
  const { data } = await api.post("/admin/playground", t);
  return PlaygroundResultSchema.parse(data);
}

export async function detectPrompt(prompt: string): Promise<DetectResponse> {
  const { data } = await api.post("/v1/detect", { prompt });
  return DetectResponseSchema.parse(data);
}
