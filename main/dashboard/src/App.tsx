import { useCallback, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { AppBar, Paper, Toolbar, Typography } from "@mui/material";
import ShieldOutlinedIcon from "@mui/icons-material/ShieldOutlined";
import { fetchDecisions, fetchMetricsSummary, type DecisionRow } from "./api";
import { mockDecisions, mockMetrics } from "./mock";
import StatCards from "./components/StatCards";
import DisagreementScatter from "./components/DisagreementScatter";
import LiveFeed from "./components/LiveFeed";
import EscalationFunnel from "./components/EscalationFunnel";
import ThresholdPlayground from "./components/ThresholdPlayground";
import FamilyBreakdown from "./components/FamilyBreakdown";
import PromptDetail from "./components/PromptDetail";
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

  // mock fallback keeps the demo alive if the API is down
  const rows = decisionsQuery.data ?? (decisionsQuery.isError ? mockDecisions() : null);
  const summary = metricsQuery.data ?? (metricsQuery.isError ? mockMetrics() : null);
  const offline = decisionsQuery.isError || metricsQuery.isError;

  const onThresholds = useCallback(
    (t: { t_low: number; t_high: number; t_d: number }) => setThresholds(t),
    [],
  );

  return (
    <div className="min-h-screen bg-paper text-ink">
      <AppBar position="static" elevation={0}
              sx={{ bgcolor: "white", borderBottom: `1px solid ${tokens.hairline}` }}>
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
              API offline: showing demo data
            </Typography>
          )}
        </Toolbar>
      </AppBar>

      <main className="max-w-7xl mx-auto p-4 space-y-4">
        {!rows || !summary ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
            {[0, 1, 2, 3].map((i) => (
              <Paper key={i} sx={{ height: 88 }} className="animate-pulse" />
            ))}
          </div>
        ) : (
          <StatCards summary={summary} />
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
            {summary && <EscalationFunnel summary={summary} />}
            <ThresholdPlayground onChange={onThresholds} />
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {rows && <LiveFeed rows={rows} onSelect={setSelected} />}
          <FamilyBreakdown />
        </div>
      </main>

      <PromptDetail row={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
