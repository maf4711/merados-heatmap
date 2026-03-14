/** meradOS Logo — wordmark with compass rose O */

import { CompassRose } from "./CompassRose";

interface LogoProps {
  size?: "sm" | "md" | "lg" | "xl";
  tagline?: boolean;
  className?: string;
}

const sizes = {
  sm: { text: "text-lg", compass: 14, gap: "gap-0" },
  md: { text: "text-2xl", compass: 20, gap: "gap-0" },
  lg: { text: "text-4xl", compass: 28, gap: "gap-0" },
  xl: { text: "text-6xl", compass: 40, gap: "gap-0" },
};

export function Logo({ size = "md", tagline = false, className }: LogoProps) {
  const s = sizes[size];
  return (
    <div className={className}>
      <div className={`inline-flex items-baseline font-logo font-medium tracking-[-0.025em] ${s.text} ${s.gap}`}>
        <span>merad</span>
        <CompassRose size={s.compass} className="mb-[0.04em]" />
        <span>S</span>
      </div>
      {tagline && (
        <p className="mt-1 text-[11px] font-normal uppercase tracking-[0.3em] opacity-20">
          GPS for money
        </p>
      )}
    </div>
  );
}
