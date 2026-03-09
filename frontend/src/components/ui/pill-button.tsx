import Link from "next/link";

type PillButtonProps = {
  variant?: "filled" | "outline";
  href?: string;
  onClick?: () => void;
  disabled?: boolean;
  type?: "button" | "submit";
  className?: string;
  children: React.ReactNode;
};

export function PillButton({
  variant = "filled",
  href,
  onClick,
  disabled,
  type = "button",
  className = "",
  children,
}: PillButtonProps) {
  const base =
    "inline-flex items-center gap-2 rounded-pill px-5 py-2 text-xs font-body cursor-pointer transition-all duration-200 hover:-translate-y-px disabled:opacity-50 disabled:cursor-not-allowed";
  const filled = "bg-primary text-[#f5f5f0] border-none hover:bg-accent2";
  const outline =
    "bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0]";

  const cls = `${base} ${variant === "outline" ? outline : filled} ${className}`;

  if (href) {
    return (
      <Link href={href} className={cls}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} onClick={onClick} disabled={disabled} className={cls}>
      {children}
    </button>
  );
}
