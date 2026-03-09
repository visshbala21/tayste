type StatBadgeProps = {
  value: string | number;
  label: string;
  className?: string;
};

export function StatBadge({ value, label, className = "" }: StatBadgeProps) {
  return (
    <div
      className={`border border-white/[0.12] rounded-md p-3 text-center bg-white/[0.03] ${className}`}
    >
      <div className="font-display text-[32px] leading-none text-primary">
        {value}
      </div>
      <div className="text-[10px] text-white/40 tracking-wider uppercase mt-1">
        {label}
      </div>
    </div>
  );
}
