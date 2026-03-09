"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

const LAST_LABEL_KEY = "tayste:last-label-id";

export function NavBar() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [lastLabelId, setLastLabelId] = useState<string | null>(null);

  const activeLabelFromRoute = useMemo(() => {
    const labelMatch = pathname.match(/^\/labels\/([^/]+)/);
    if (labelMatch?.[1]) {
      return decodeURIComponent(labelMatch[1]);
    }

    const labelFromQuery = searchParams.get("label");
    return labelFromQuery || null;
  }, [pathname, searchParams]);

  useEffect(() => {
    if (activeLabelFromRoute) {
      window.localStorage.setItem(LAST_LABEL_KEY, activeLabelFromRoute);
      setLastLabelId(activeLabelFromRoute);
      return;
    }

    setLastLabelId(window.localStorage.getItem(LAST_LABEL_KEY));
  }, [activeLabelFromRoute]);

  const activeLabelId = activeLabelFromRoute || lastLabelId;

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
