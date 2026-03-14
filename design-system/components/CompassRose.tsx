/** meradOS Compass Rose — the O in meradOS */

interface CompassRoseProps {
  size?: number | string;
  className?: string;
  color?: string;
}

export function CompassRose({ size = 24, className, color = "#00d4ff" }: CompassRoseProps) {
  return (
    <svg
      viewBox="0 0 100 100"
      width={size}
      height={size}
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="50" cy="50" r="44" stroke="currentColor" strokeWidth="1.5" />
      <polygon points="50,10 52.5,45 50,50 47.5,45" fill={color} opacity="0.75" />
      <polygon points="50,90 47.5,55 50,50 52.5,55" fill="currentColor" opacity="0.2" />
      <polygon points="10,50 45,47.5 50,50 45,52.5" fill="currentColor" opacity="0.12" />
      <polygon points="90,50 55,52.5 50,50 55,47.5" fill="currentColor" opacity="0.12" />
    </svg>
  );
}

/** Inline compass for use inside text (as the O in meradOS) */
export function CompassInline({ className }: { className?: string }) {
  return (
    <span className={`inline-flex items-baseline ${className ?? ""}`}>
      <CompassRose className="mb-[0.04em] h-[0.62em] w-[0.62em]" />
    </span>
  );
}
