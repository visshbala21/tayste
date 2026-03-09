import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        background: "#0a0a0a",
        surface: "#1e1e28",
        "surface-light": "#2a2a36",
        border: "rgba(255,255,255,0.12)",
        primary: "#7c5cfc",
        "primary-light": "#9b7eff",
        accent: "#06b6d4",
        accent2: "#c45cfc",
        "accent-light": "#22d3ee",
        success: "#10b981",
        warning: "#f59e0b",
        danger: "#ef4444",
        muted: "#6b7280",
      },
      fontFamily: {
        display: ['"Bebas Neue"', "sans-serif"],
        body: ["Verdana", "Geneva", "sans-serif"],
      },
      borderRadius: {
        pill: "30px",
      },
    },
  },
  plugins: [],
};

export default config;
