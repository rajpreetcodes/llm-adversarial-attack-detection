import { Paper, Typography } from "@mui/material";
import type { DecisionRow, MetricsSummary } from "../api";
import { tokens } from "../theme";

/** Escalation funnel: total -> auto-passed -> auto-blocked -> escalated -> cost. */
export default function EscalationFunnel({ summary, rows }: { summary: MetricsSummary; rows: DecisionRow[] }) {
  const total = summary.total || 1;
  const escalated = rows.filter((row) => row.escalated).length;
  const passed = rows.filter((row) => !row.escalated && row.decision === "PASS").length;
  const blocked = rows.filter((row) => !row.escalated && row.decision === "BLOCK").length;
  const stages = [
        { label: "recent audit rows", n: rows.length, c: tokens.accent },
    { label: "auto-passed", n: passed, c: tokens.pass },
    { label: "auto-blocked", n: blocked, c: tokens.danger },
        { label: "escalated", n: escalated, c: tokens.warn },
  ];
  return (
    <Paper className="reveal" sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>Escalation funnel</Typography>
      <div className="space-y-2">
        {stages.map((s) => (
          <div key={s.label}>
            <div className="flex justify-between font-mono text-xs text-muted">
              <span>{s.label}</span>
              <span>{s.n} ({((s.n / total) * 100).toFixed(0)}%)</span>
            </div>
            <div className="h-3 border border-hairline bg-white">
              <div
                className="h-full"
                style={{
                  width: `${(s.n / total) * 100}%`,
                  background: s.c,
                  transition: "width 300ms ease-out",
                }}
              />
            </div>
          </div>
        ))}
      </div>
      <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>Counts use the loaded audit rows. Escalated outcomes are excluded from auto-pass and auto-block.</Typography>
    </Paper>
  );
}
