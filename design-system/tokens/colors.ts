/** meradOS Design Tokens — Colors */

export const colors = {
  brand: {
    50: "#f0fdff",
    100: "#ccf7ff",
    200: "#99eeff",
    300: "#4de1ff",
    400: "#00d4ff", // ← Primary
    500: "#00b4d8",
    600: "#0090ad",
    700: "#006d83",
    800: "#004d5e",
    900: "#003340",
  },
  navy: {
    800: "#0a0a12",
    900: "#07070d",
    950: "#050508", // ← Background
  },
  neutral: {
    0: "#050508",
    50: "#0a0a0f",
    100: "#111118",
    200: "#1a1a24",
    300: "#2a2a3a",
    400: "#4a4a5a",
    500: "#6b7280",
    600: "#9ca3af",
    700: "#d1d5db",
    800: "#e8eaf0",
    900: "#f8f9fb",
  },
  semantic: {
    success: "#34d399",
    warning: "#f5a623",
    error: "#ef4444",
    info: "#3b82f6",
  },
  text: {
    primary: "rgba(255, 255, 255, 0.88)",
    secondary: "rgba(255, 255, 255, 0.45)",
    tertiary: "rgba(255, 255, 255, 0.2)",
    inverse: "rgba(0, 0, 0, 0.88)",
  },
} as const;

export type BrandColor = keyof typeof colors.brand;
export type NavyColor = keyof typeof colors.navy;
