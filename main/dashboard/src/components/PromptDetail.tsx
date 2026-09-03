import { Dialog, DialogContent, DialogTitle, Typography, Chip, IconButton } from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import type { DecisionRow } from "../api";
import { tokens } from "../theme";

/** Prompt detail: every channel score, disagreement, judge rationale, traces. */
export default function PromptDetail({ row, onClose }: {
  row: DecisionRow | null; onClose: () => void;
}) {
  if (!row) return null;
  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <span className="font-mono text-sm">prompt {row.prompt_hash.slice(0, 16)}...</span>
        <IconButton onClick={onClose} aria-label="close detail view" size="small">
          <CloseIcon />
        </IconButton>
      </DialogTitle>
      <DialogContent dividers>
        <div className="space-y-3">
          <div>
            <Chip label={row.decision} size="small"
                  sx={{ border: `1px solid ${tokens.accent}`, borderRadius: 1, mr: 1 }} />
            <Chip label={`escalated: ${row.escalated}`} size="small" variant="outlined"
                  sx={{ borderRadius: 1 }} />
          </div>
          <div>
            <Typography variant="overline" color="text.secondary">channel scores</Typography>
            <div className="font-mono text-sm">
              {Object.entries(row.scores).map(([k, v]) => (
                <div key={k} className="flex justify-between border-b border-hairline py-1">
                  <span>{k}</span><span>{v.toFixed(3)}</span>
                </div>
              ))}
              <div className="flex justify-between py-1">
                <span>disagreement</span><span>{row.disagreement.toFixed(3)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span>latency</span><span>{row.latency_ms.toFixed(1)} ms</span>
              </div>
            </div>
          </div>
          {row.judge_verdict && (
            <div>
              <Typography variant="overline" color="text.secondary">judge verdict</Typography>
              <Typography variant="body2">
                {row.judge_verdict.verdict} ({(row.judge_verdict.confidence * 100).toFixed(0)}%
                {row.judge_verdict.attack_family ? `, ${row.judge_verdict.attack_family}` : ""})
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {row.judge_verdict.rationale}
              </Typography>
            </div>
          )}
          {row.rationale && !row.judge_verdict && (
            <Typography variant="body2" color="text.secondary">{row.rationale}</Typography>
          )}
          {row.degraded && (
            <Typography variant="body2" sx={{ color: tokens.warn }}>
              degraded: at least one channel was unavailable
            </Typography>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
