import { createTheme } from "@mui/material";

/**
 * Utilitarian design tokens (named style, see docs/adr/0005-dashboard-style.md):
 * flat surfaces, hairline borders, industrial type, restrained colour.
 */
export const tokens = {
  paper: "#09090B",
  surface: "#18181B",
  ink: "#F4F4F5",
  muted: "#A1A1AA",
  hairline: "#27272A",
  accent: "#F59E0B",
  danger: "#EF4444",
  pass: "#10B981",
  warn: "#F59E0B",
} as const;

export const theme = createTheme({
  palette: {
    mode: "dark",
    background: { default: tokens.paper, paper: tokens.surface },
    text: { primary: tokens.ink, secondary: tokens.muted },
    primary: { main: tokens.accent },
    error: { main: tokens.danger },
    success: { main: tokens.pass },
  },
  typography: {
    fontFamily: '"Geist", "Segoe UI", system-ui, sans-serif',
    h5: { fontWeight: 600, letterSpacing: "-0.01em" },
    h6: { fontWeight: 600 },
    overline: { fontFamily: '"JetBrains Mono", Consolas, monospace' },
  },
  shape: { borderRadius: 2 },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: { boxShadow: "none", border: `1px solid ${tokens.hairline}`, backgroundImage: "none" },
      },
    },
    MuiButton: { styleOverrides: { root: { textTransform: "none" } } },
  },
});
