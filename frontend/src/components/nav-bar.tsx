"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useActiveLabel } from "@/lib/label-context";

export function NavBar() {
  const pathname = usePathname();
  const { activeLabelId } = useActiveLabel();

  const links = [
    { label: "Home", href: "/dashboard" },
    ...(activeLabelId
      ? [
          { label: "Scout Feed", href: `/labels/${activeLabelId}/scout-feed` },
          { label: "Collections", href: `/labels/${activeLabelId}/watchlists` },
          { label: "Taste Map", href: `/labels/${activeLabelId}/taste-map` },
        ]
      : []),
    { label: "Import", href: "/import" },
  ];

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  };

  return (
    <div className="nav-links flex gap-1">
      {links.map((link) => (
        <Link
          key={link.href}
          href={link.href}
          className={`px-3.5 py-1 rounded text-[11px] italic font-body border transition-all duration-200 ${
            isActive(link.href)
              ? "bg-primary border-primary text-[#f5f5f0]"
              : "bg-white/[0.07] border-white/[0.12] text-[#f5f5f0] hover:bg-primary hover:border-primary"
          }`}
        >
          {link.label}
        </Link>
      ))}
    </div>
  );
}
