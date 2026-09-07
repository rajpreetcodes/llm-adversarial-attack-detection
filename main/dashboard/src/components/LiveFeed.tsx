import { Paper, Typography, Chip } from "@mui/material";
import type { DecisionRow } from "../api";
import { tokens } from "../theme";

const colour = (d: string) =>
  d === "BLOCK" ? tokens.danger : d === "PASS" ? tokens.pass : tokens.warn;

/** Live feed: the most recent prompts, decision, latency. Polls every 5s. */
export default function LiveFeed({ rows, onSelect }: {
  rows: DecisionRow[]; onSelect: (r: DecisionRow) => void;
}) {
  return (
    <Paper className="reveal" sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>Live feed</Typography>
      <div className="max-h-96 overflow-auto">
        <table className="w-full text-sm" aria-label="recent prompts">
          <thead>
            <tr className="text-left text-muted font-mono text-xs border-b border-hairline">
              <th scope="col" className="py-1">time</th>
              <th scope="col" className="py-1">prompt hash</th>
              <th scope="col" className="py-1">decision</th>
              <th scope="col" className="py-1 text-right">latency</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id}
                  className="border-b border-hairline cursor-pointer hover:bg-zinc-800 transition-colors duration-150"
                  onClick={() => onSelect(r)}>
                <td className="py-1.5 font-mono text-xs text-muted">
                  {r.timestamp ? new Date(r.timestamp).toLocaleTimeString() : ":"}
                </td>
                <td className="py-1.5 font-mono text-xs">{r.prompt_hash.slice(0, 12)}...</td>
                <td className="py-1.5">
                  <Chip size="small" label={r.decision}
                        sx={{ bgcolor: "transparent", border: `1px solid ${colour(r.decision)}`,
                              color: colour(r.decision), fontFamily: '"JetBrains Mono", Consolas, monospace',
                              fontSize: 11, height: 22, borderRadius: 1 }} />
                </td>
                <td className="py-1.5 text-right font-mono text-xs">{r.latency_ms.toFixed(0)} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Paper>
  );
}
