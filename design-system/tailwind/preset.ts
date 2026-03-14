/** meradOS Tailwind Preset — import in any project's tailwind.config.ts */
import type { Config } from "tailwindcss";
import { colors } from "../tokens/colors";
import { fontFamily } from "../tokens/typography";

const preset: Partial<Config> = {
  theme: {
    extend: {
      colors: {
        brand: colors.brand,
        navy: colors.navy,
      },
      fontFamily: {
        sans: fontFamily.sans,
        logo: fontFamily.logo,
      },
      animation: {
        "fade-in": "fadeIn 0.8s ease-out forwards",
        "fade-in-up": "fadeInUp 0.8s ease-out forwards",
      },
      keyframes: {
        fadeIn: { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        fadeInUp: { "0%": { opacity: "0", transform: "translateY(8px)" }, "100%": { opacity: "1", transform: "translateY(0)" } },
      },
    },
  },
};

export default preset;
