type SectionLabelProps = {
  children: React.ReactNode;
  className?: string;
};

export function SectionLabel({ children, className = "" }: SectionLabelProps) {
  return (
    <h2
      className={`font-display text-[22px] tracking-wide py-3.5 border-b border-dashed border-white/[0.12] text-[#f5f5f0] ${className}`}
    >
      {children}
    </h2>
  );
}
