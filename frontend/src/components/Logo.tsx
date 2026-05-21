/*
 * NexGenIQ logo — an inline-SVG mark and wordmark.
 *
 * The mark is a hexagon (a clean genetics / data motif) enclosing three
 * ascending bars: it reads as selection progress — successive
 * generations improving — which is exactly what NexGenIQ does. It is
 * deliberately geometric and simple so it stays crisp from a 16px
 * favicon up to a page header, and it uses the app's Graphite / Sage
 * palette so it sits naturally in the UI.
 *
 * `LogoMark` is the icon alone (used for the favicon and tight spaces);
 * `Logo` is the mark plus the "NexGenIQ" wordmark for the top bar.
 */

interface LogoProps {
  /** Pixel height of the mark; the wordmark scales with it. */
  size?: number;
  /** Render the mark only, without the wordmark. */
  markOnly?: boolean;
}

/* The mark on its own — a hexagon with three ascending bars inside. */
export function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      role="img"
      aria-label="NexGenIQ"
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* hexagon outline */}
      <path
        d="M24 3 42 13.5 42 34.5 24 45 6 34.5 6 13.5 Z"
        fill="var(--sage-600, #3d6b4e)"
      />
      <path
        d="M24 8 37.5 15.75 37.5 31.25 24 39 10.5 31.25 10.5 15.75 Z"
        fill="var(--graphite-900, #2f3a37)"
      />
      {/* three ascending bars — selection progress across generations */}
      <rect
        x="15"
        y="26"
        width="5"
        height="8"
        rx="1"
        fill="var(--sage-300, #7d9a82)"
      />
      <rect
        x="21.5"
        y="21"
        width="5"
        height="13"
        rx="1"
        fill="var(--sage-300, #7d9a82)"
      />
      <rect
        x="28"
        y="15"
        width="5"
        height="19"
        rx="1"
        fill="#ffffff"
      />
    </svg>
  );
}

/* The full lockup — mark plus wordmark — for the top bar. */
export function Logo({ size = 28, markOnly = false }: LogoProps) {
  if (markOnly) return <LogoMark size={size} />;
  return (
    <span className="nx-logo">
      <LogoMark size={size} />
      <span className="nx-logo-word">
        NexGen<span className="nx-logo-iq">IQ</span>
      </span>
    </span>
  );
}
