/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#09090B",
        surface: "#18181B",
        ink: "#F4F4F5",
        muted: "#A1A1AA",
        hairline: "#27272A",
        accent: "#F59E0B",
        danger: "#EF4444",
        pass: "#10B981",
        warn: "#F59E0B",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Segoe UI"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "Consolas", '"Cascadia Mono"', "monospace"],
      },
    },
  },
  plugins: [],
};
