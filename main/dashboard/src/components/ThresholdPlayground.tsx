import { useEffect, useState } from "react";
import { Paper, Slider, Typography } from "@mui/material";
import { postPlayground, type PlaygroundResult } from "../api";
import { mockPlayground } from "../mock";
import { tokens } from "../theme";

/**
 * Threshold playground: move t_low / t_high / t_d and watch the decision mix
 * and escalation rate recompute over historical traffic. The viva demo.
 */
export default function ThresholdPlayground({
  onChange,
}: {
  onChange: (t: { t_low: number; t_high: number; t_d: number }) => void;
}) {
  const [tLow, setTLow] = useState(0.3);
  const [tHigh, setTHigh] = useState(0.7);
  const [tD, setTD] = useState(0.4);
  const [result, setResult] = useState<PlaygroundResult | null>(null);

  useEffect(() => {
    const t = { t_low: tLow, t_high: tHigh, t_d: tD };
    onChange(t);
    const handle = setTimeout(() => {
      postPlayground(t).then(setResult).catch(() => setResult(mockPlayground(tLow, tHigh, tD)));
    }, 250);
    return () => clearTimeout(handle);
  }, [tLow, tHigh, tD, onChange]);

  const sliders: [string, number, (v: number) => void][] = [
    ["t_low (agree-benign ceiling)", tLow, setTLow],
    ["t_high (agree-attack floor)", tHigh, setTHigh],
    ["t_d (disagreement trigger)", tD, setTD],
  ];

  return (
    <Paper className="reveal" sx={{ p: 2 }}>
      <Typography variant="h6">Threshold playground</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        The accuracy/cost trade-off, live. Historical decisions recomputed with your thresholds.
      </Typography>
      {sliders.map(([label, value, set]) => (
        <div key={label} className="mb-3">
          <div className="flex justify-between font-mono text-xs text-muted">
            <span>{label}</span>
            <span>{value.toFixed(2)}</span>
          </div>
          <Slider
            value={value} min={0} max={1} step={0.01}
            onChange={(_, v) => set(v as number)}
            aria-label={label}
            sx={{ color: tokens.accent, height: 4 }}
          />
        </div>
      ))}
      {result && (
        <div className="font-mono text-xs border-t border-hairline pt-2 mt-2 space-y-1">
          <div>n = {result.n} historical prompts</div>
          <div>
            PASS {result.decision_mix["PASS"] ?? 0} / BLOCK {result.decision_mix["BLOCK"] ?? 0}
            {" "}/ ESCALATE {result.decision_mix["ESCALATE"] ?? 0}
          </div>
          <div style={{ color: tokens.warn }}>
            escalation rate: {(result.escalation_rate * 100).toFixed(1)}%
          </div>
        </div>
      )}
    </Paper>
  );
}
