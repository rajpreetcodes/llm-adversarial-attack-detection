import { useMemo, useState } from "react";
import {
  CartesianGrid, ReferenceArea, ResponsiveContainer, Scatter, ScatterChart,
  Tooltip, XAxis, YAxis,
} from "recharts";
import { Paper, Typography } from "@mui/material";
import type { DecisionRow } from "../api";
import { tokens } from "../theme";

/**
 * THE HERO VIEW. X = Channel A (statistical), Y = Channel B (semantic).
 * The shaded band is the escalation region: where the two cheap channels
 * disagree. The entire thesis is visible in this one plot.
 */
export default function DisagreementScatter({
  rows, tLow, tHigh, onSelect,
}: {
  rows: DecisionRow[];
  tLow: number;
  tHigh: number;
  onSelect: (row: DecisionRow) => void;
}) {
  const points = useMemo(
    () =>
      rows
        .filter((r) => r.scores.statistical !== undefined && r.scores.semantic !== undefined)
        .map((r) => ({
          x: r.scores.statistical,
          y: r.scores.semantic,
          decision: r.decision,
          row: r,
        })),
    [rows],
  );
  const [active, setActive] = useState<string | null>(null);

  return (
    <Paper className="reveal" sx={{ p: 2 }}>
      <Typography variant="h6">Disagreement map</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        Every prompt as a point. Green passed, red blocked, amber contested (sent to the
        escalation tier). The middle band is where cheap detectors disagree.
      </Typography>
      <ResponsiveContainer width="100%" height={420}>
        <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke={tokens.hairline} />
          <XAxis type="number" dataKey="x" domain={[0, 1]} name="Channel A"
                 label={{ value: "Channel A: statistical score", position: "insideBottom", offset: -4 }}
                 stroke={tokens.muted} fontSize={12} fontFamily="JetBrains Mono, Consolas, monospace" />
          <YAxis type="number" dataKey="y" domain={[0, 1]} name="Channel B"
                 label={{ value: "Channel B: semantic score", angle: -90, position: "insideLeft" }}
                 stroke={tokens.muted} fontSize={12} fontFamily="JetBrains Mono, Consolas, monospace" />
          {/* escalation band: the contested middle region */}
          <ReferenceArea x1={tLow} x2={tHigh} y1={tLow} y2={tHigh}
                         fill={tokens.warn} fillOpacity={0.08} stroke="none" />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            content={({ payload }) => {
              const p = payload?.[0]?.payload;
              if (!p) return null;
              return (
                <div className="bg-surface border border-hairline p-2 font-mono text-xs text-ink">
                  <div>A: {p.x.toFixed(3)} B: {p.y.toFixed(3)}</div>
                  <div>decision: {p.decision}</div>
                  <div>hash: {p.row.prompt_hash.slice(0, 12)}...</div>
                </div>
              );
            }}
          />
          <Scatter
            data={points}
            shape={(props: any) => {
              const { cx, cy, payload } = props;
              const colour =
                payload.decision === "BLOCK" ? tokens.danger
                : payload.row.escalated ? tokens.warn
                : tokens.pass;
              return (
                <circle
                  cx={cx} cy={cy} r={5} fill={colour} fillOpacity={0.75}
                  stroke={active === payload.row.id ? tokens.ink : "none"}
                  strokeWidth={2}
                  style={{ cursor: "pointer", transition: "fill-opacity 150ms" }}
                  onMouseEnter={() => setActive(payload.row.id)}
                  onMouseLeave={() => setActive(null)}
                  onClick={() => onSelect(payload.row)}
                  aria-label={`prompt ${payload.row.prompt_hash.slice(0, 8)}, ${payload.decision}`}
                />
              );
            }}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </Paper>
  );
}
