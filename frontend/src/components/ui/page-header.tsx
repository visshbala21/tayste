type PageHeaderProps = {
  title: string;
  subtitle?: string;
  className?: string;
  children?: React.ReactNode;
};

export function PageHeader({ title, subtitle, className = "", children }: PageHeaderProps) {
  return (
    <div className={`mb-6 ${className}`}>
      <h1 className="font-display text-[clamp(36px,8vw,72px)] leading-none tracking-wide text-[#f5f5f0]">
        {title}
      </h1>
      {subtitle && (
        <p className="text-white/45 mt-2 italic text-sm">{subtitle}</p>
      )}
      {children}
    </div>
  );
}
