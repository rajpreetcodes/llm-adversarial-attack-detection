import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Alert, AppBar, Button, Paper, Toolbar, Typography } from "@mui/material";
import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";
import { fetchDecisions, fetchMetricsSummary, type DecisionRow } from "./api";
import StatCards from "./components/StatCards";
import DisagreementScatter from "./components/DisagreementScatter";
import LiveFeed from "./components/LiveFeed";
import EscalationFunnel from "./components/EscalationFunnel";
import ThresholdPlayground from "./components/ThresholdPlayground";
import PromptDetail from "./components/PromptDetail";
import LivePromptPlayground from "./components/LivePromptPlayground";
import { tokens } from "./theme";

export default function App() {
  const [thresholds, setThresholds] = useState({ t_low: 0.3, t_high: 0.7, t_d: 0.4 });
  const [selected, setSelected] = useState<DecisionRow | null>(null);

  const decisionsQuery = useQuery({
    queryKey: ["decisions"],
    queryFn: () => fetchDecisions(100),
  });
  const metricsQuery = useQuery({
    queryKey: ["metrics"],
    queryFn: fetchMetricsSummary,
  });

  const rows = decisionsQuery.data;
  const summary = metricsQuery.data;
  const offline = decisionsQuery.isError || metricsQuery.isError;

  const onThresholds = useCallback(
    (t: { t_low: number; t_high: number; t_d: number }) => setThresholds(t),
    [],
  );

  return (
    <div className="min-h-screen bg-paper text-ink">
      <AppBar position="static" elevation={0}
              sx={{ bgcolor: tokens.paper, borderBottom: `1px solid ${tokens.hairline}` }}>
        <Toolbar sx={{ gap: 1 }}>
          <ShieldOutlinedIcon sx={{ color: tokens.accent }} />
          <Typography variant="h6" sx={{ color: tokens.ink, flexGrow: 1 }}>
            DGAD
            <span className="font-mono text-xs text-muted" style={{ marginLeft: 12 }}>
              disagreement-gated adaptive detection
            </span>
          </Typography>
          {offline && (
            <Typography variant="body2" sx={{ color: tokens.warn }} className="font-mono">
              API unavailable
            </Typography>
          )}
        </Toolbar>
      </AppBar>

      <main className="max-w-7xl mx-auto p-4 space-y-4">
        <LivePromptPlayground />
        {offline && <Alert severity="error" action={<Button color="inherit" size="small" onClick={() => { decisionsQuery.refetch(); metricsQuery.refetch(); }}>Retry</Button>}>
          Live audit data could not be loaded. No simulated records are shown.
        </Alert>}
        {!rows || !summary ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[0, 1, 2, 3].map((i) => (
              <Paper key={i} sx={{ height: 88 }} className="animate-pulse" />
            ))}
          </div>
        ) : (
          summary ? <StatCards summary={summary} /> : !offline ? <Paper sx={{ p: 2 }}><Typography color="text.secondary">No metrics have been recorded yet.</Typography></Paper> : null
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-2">
            {rows && (
              <DisagreementScatter
                rows={rows}
                tLow={thresholds.t_low}
                tHigh={thresholds.t_high}
                onSelect={setSelected}
              />
            )}
          </div>
          <div className="space-y-4">
            {summary && rows && <EscalationFunnel summary={summary} rows={rows} />}
            <ThresholdPlayground onChange={onThresholds} />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {rows && <LiveFeed rows={rows} onSelect={setSelected} />}
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6">Evidence status</Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, maxWidth: "65ch" }}>
              Evaluation snapshots are excluded from this live cockpit because the committed ablation does not exercise the full C/D escalation path. Use a reproduced, commit-linked evaluation report for research claims.
            </Typography>
          </Paper>
        </div>
      </main>

      <PromptDetail row={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
