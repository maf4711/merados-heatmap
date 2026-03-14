/** meradOS Design Tokens — Typography */

export const fontFamily = {
  sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "SF Pro Display", "Helvetica Neue", "system-ui", "sans-serif"],
  logo: ["Inter", "SF Pro Display", "SF Pro", "-apple-system", "BlinkMacSystemFont", "Helvetica Neue", "sans-serif"],
};

export const typeScale = {
  display: { size: "48px", weight: 500, tracking: "-0.03em" },
  h1:      { size: "36px", weight: 500, tracking: "-0.025em" },
  h2:      { size: "28px", weight: 500, tracking: "-0.02em" },
  h3:      { size: "22px", weight: 500, tracking: "-0.015em" },
  h4:      { size: "18px", weight: 500, tracking: "-0.01em" },
  body:    { size: "16px", weight: 400, tracking: "0" },
  small:   { size: "14px", weight: 400, tracking: "0" },
  caption: { size: "12px", weight: 500, tracking: "0.02em" },
  overline:{ size: "11px", weight: 500, tracking: "0.08em", transform: "uppercase" as const },
} as const;

export const spacing = [0, 4, 8, 12, 16, 24, 32, 48, 64, 96] as const;
