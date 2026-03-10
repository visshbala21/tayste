"use client";

import { useEffect, useRef, useState, useMemo } from "react";
import { usePathname, useRouter } from "next/navigation";
import Link from "next/link";
import type { Label } from "@/lib/api";

const LAST_LABEL_KEY = "tayste:last-label-id";

export function LabelSwitcher({ labels }: { labels: Label[] }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const router = useRouter();

  const activeLabelId = useMemo(() => {
    const match = pathname.match(/\/labels\/([^/]+)/);
    if (match?.[1]) return decodeURIComponent(match[1]);
    if (typeof window !== "undefined") {
      return window.localStorage.getItem(LAST_LABEL_KEY);
    }
    return null;
  }, [pathname]);

  const activeLabel = labels.find((l) => l.id === activeLabelId);

  // Click-outside to close
  useEffect(() => {
    if (!open) return;
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  // Escape to close
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open]);

  const handleSelect = (labelId: string) => {
    setOpen(false);
    if (typeof window !== "undefined") {
      window.localStorage.setItem(LAST_LABEL_KEY, labelId);
    }
    // Determine current sub-page
    const subPageMatch = pathname.match(/\/labels\/[^/]+\/(.*)/);
    const subPage = subPageMatch?.[1]?.split("?")[0] || "scout-feed";
    router.push(`/labels/${labelId}/${subPage}`);
  };

  if (labels.length === 0) {
    return (
      <div ref={ref} className="relative">
        <button
          onClick={() => setOpen(!open)}
          className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-1 text-[11px] italic text-white/50 max-w-[200px] truncate flex items-center gap-1.5"
        >
          No labels yet
          <svg className="w-3 h-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
        </button>
        {open && (
          <div className="absolute top-full left-0 mt-1 min-w-[200px] bg-[#141414] border border-white/[0.12] rounded-lg shadow-xl z-50 overflow-hidden">
            <Link
              href="/import"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-[11px] italic text-white/35 hover:text-primary hover:bg-white/[0.04] transition-colors"
            >
              + New Import
            </Link>
          </div>
        )}
      </div>
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-1 text-[11px] italic text-white/80 max-w-[200px] truncate flex items-center gap-1.5"
      >
        {activeLabel?.name || "Select label"}
        <svg className={`w-3 h-3 opacity-40 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 min-w-[220px] bg-[#141414] border border-white/[0.12] rounded-lg shadow-xl z-50 overflow-hidden">
          {labels.map((label) => {
            const isActive = label.id === activeLabelId;
            return (
              <button
                key={label.id}
                onClick={() => handleSelect(label.id)}
                className={`w-full text-left px-3 py-2 text-[11px] italic flex items-center justify-between transition-colors ${
                  isActive
                    ? "bg-white/[0.06] text-white/90"
                    : "text-white/60 hover:bg-white/[0.04] hover:text-white/80"
                }`}
              >
                <span className="truncate">{label.name}</span>
                {isActive && (
                  <svg className="w-3 h-3 text-primary flex-shrink-0 ml-2" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                )}
              </button>
            );
          })}
          <div className="border-t border-white/[0.08]">
            <Link
              href="/import"
              onClick={() => setOpen(false)}
              className="block px-3 py-2 text-[11px] italic text-white/35 hover:text-primary hover:bg-white/[0.04] transition-colors"
            >
              + New Import
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
