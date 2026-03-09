const DEFAULT_HEIGHTS = [20, 35, 15, 40, 25, 38, 12, 30, 42, 18, 35, 28, 10, 36, 22];

type WaveformProps = {
  barCount?: number;
  accentColor?: string;
  heights?: number[];
  className?: string;
};

export function Waveform({
  barCount,
  accentColor = "var(--accent)",
  heights = DEFAULT_HEIGHTS,
  className = "",
}: WaveformProps) {
  const bars = barCount ? heights.slice(0, barCount) : heights;

  return (
    <div className={`wave ${className}`} style={{ height: 40 }}>
      {bars.map((h, i) => (
        <div
          key={i}
          className="wave-bar"
          style={{
            height: h,
            opacity: 0.4 + (i % 3) * 0.15,
            background: accentColor,
          }}
        />
      ))}
    </div>
  );
}
