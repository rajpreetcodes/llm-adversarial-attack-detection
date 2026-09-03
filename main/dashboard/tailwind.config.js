/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        paper: "#FAFAF9",
        ink: "#1C1917",
        muted: "#57534E",
        hairline: "#E7E5E4",
        accent: "#3F4E6B",
        danger: "#B91C1C",
        pass: "#15803D",
        warn: "#A16207",
      },
      fontFamily: {
        sans: ['"IBM Plex Sans"', '"Segoe UI"', "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "Consolas", '"Cascadia Mono"', "monospace"],
      },
    },
  },
  plugins: [],
};
