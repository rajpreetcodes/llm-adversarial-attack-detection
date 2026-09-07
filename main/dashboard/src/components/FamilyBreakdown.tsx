import {
  Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { Paper, Typography } from "@mui/material";
import { tokens } from "../theme";
import snapshot from "../eval_snapshot.json";

/**
 * Attack-family breakdown from the latest evaluation run
 * (results/ablation.csv snapshot; regenerate with the eval runner).
 */
export default function FamilyBreakdown() {
  return (
    <Paper className="reveal" sx={{ p: 2 }}>
      <Typography variant="h6">Attack-family detection rate</Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        Latest evaluation run, recall per attack family at the tuned threshold.
      </Typography>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={snapshot.per_family} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke={tokens.hairline} />
          <XAxis dataKey="family" fontSize={11} stroke={tokens.muted}
                 fontFamily="JetBrains Mono, Consolas, monospace" />
          <YAxis domain={[0, 1]} fontSize={11} stroke={tokens.muted} />
          <Tooltip />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Bar dataKey="channel_a_only" name="Channel A" fill={tokens.accent} />
          <Bar dataKey="channel_b_only" name="Channel B" fill={tokens.muted} />
          <Bar dataKey="dgad_full" name="DGAD full" fill={tokens.pass} />
        </BarChart>
      </ResponsiveContainer>
    </Paper>
  );
}
