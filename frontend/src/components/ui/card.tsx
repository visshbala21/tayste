type CardProps = {
  accent?: boolean;
  className?: string;
  children: React.ReactNode;
};

export function Card({ accent = true, className = "", children }: CardProps) {
  return (
    <div
      className={`bg-surface border border-white/[0.12] rounded-lg p-5 relative overflow-hidden ${className}`}
    >
      {accent && (
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
      )}
      {children}
    </div>
  );
}
