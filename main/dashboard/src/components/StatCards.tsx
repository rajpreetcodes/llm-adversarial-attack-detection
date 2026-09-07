import { Paper, Typography } from "@mui/material";
import { useCountUp } from "../hooks";
import type { MetricsSummary } from "../api";

function Stat({ label, value, suffix, decimals = 0 }: {
  label: string; value: number; suffix?: string; decimals?: number;
}) {
  const v = useCountUp(value);
  return (
    <Paper className="reveal" sx={{ p: 2, minHeight: 88 }}>
      <Typography variant="overline" color="text.secondary" sx={{ fontSize: 11 }}>
        {label}
      </Typography>
      <Typography variant="h5" sx={{ fontFamily: '"JetBrains Mono", Consolas, monospace' }}>
        {v.toFixed(decimals)}
        {suffix && <span style={{ fontSize: 14, color: "#57534E" }}>{suffix}</span>}
      </Typography>
    </Paper>
  );
}

export default function StatCards({ summary }: { summary: MetricsSummary }) {
  const blocks = summary.by_decision["BLOCK"] ?? 0;
  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
      <Stat label="prompts screened" value={summary.total} />
      <Stat label="block rate" value={summary.total ? (blocks / summary.total) * 100 : 0} suffix="%" decimals={1} />
      <Stat label="escalation rate" value={summary.escalation_rate * 100} suffix="%" decimals={1} />
      <Stat label="avg latency" value={summary.avg_latency_ms} suffix=" ms" decimals={0} />
    </div>
  );
}
