import { createTheme } from "@mui/material";

/**
 * Utilitarian design tokens (named style, see docs/adr/0005-dashboard-style.md):
 * flat surfaces, hairline borders, industrial type, restrained colour.
 */
export const tokens = {
  paper: "#FAFAF9",
  ink: "#1C1917",
  muted: "#57534E",
  hairline: "#E7E5E4",
  accent: "#3F4E6B",
  danger: "#B91C1C",
  pass: "#15803D",
  warn: "#A16207",
} as const;

export const theme = createTheme({
  palette: {
    background: { default: tokens.paper, paper: "#FFFFFF" },
    text: { primary: tokens.ink, secondary: tokens.muted },
    primary: { main: tokens.accent },
    error: { main: tokens.danger },
    success: { main: tokens.pass },
  },
  typography: {
    fontFamily: '"IBM Plex Sans", "Segoe UI", system-ui, sans-serif',
    h5: { fontWeight: 600, letterSpacing: "-0.01em" },
    h6: { fontWeight: 600 },
    overline: { fontFamily: '"JetBrains Mono", Consolas, monospace' },
  },
  shape: { borderRadius: 2 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: { boxShadow: "none", border: `1px solid ${tokens.hairline}` },
      },
    },
    MuiButton: { styleOverrides: { root: { textTransform: "none" } } },
  },
});
