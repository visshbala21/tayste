"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { BatchInfo } from "@/lib/api";

interface RunSelectorProps {
  batches: BatchInfo[];
  currentBatchId: string;
  labelId: string;
  basePath: string;
  extraParams?: string;
}

function formatTimestamp(iso: string) {
  const d = new Date(iso);
  const date = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  return `${date} at ${time}`;
}

export function RunSelector({ batches, currentBatchId, labelId, basePath, extraParams }: RunSelectorProps) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  const router = useRouter();

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

  if (batches.length === 0) return null;

  const activeBatch = batches.find((b) => b.batch_id === currentBatchId) || batches[0];

  const handleSelect = (batch: BatchInfo, isLatest: boolean) => {
    setOpen(false);
    const params = new URLSearchParams();
    if (!isLatest) params.set("batch", batch.batch_id);
    if (extraParams) {
      const extra = new URLSearchParams(extraParams);
      extra.forEach((v, k) => { if (k !== "batch") params.set(k, v); });
    }
    const qs = params.toString();
    router.push(`/labels/${labelId}/${basePath}${qs ? `?${qs}` : ""}`);
  };

  return (
    <div ref={ref} className="relative inline-block mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-1.5 text-[11px] italic text-white/70 flex items-center gap-2 hover:border-white/[0.16] transition-colors"
      >
        <span>{formatTimestamp(activeBatch.created_at)}</span>
        <span className="text-white/30">&middot;</span>
        <span className="text-white/40">{activeBatch.candidate_count} candidates</span>
        <svg className={`w-3 h-3 opacity-40 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
      </button>
      {open && (
        <div className="absolute top-full left-0 mt-1 min-w-[340px] bg-[#141414] border border-white/[0.12] rounded-lg shadow-xl z-50 overflow-hidden max-h-[280px] overflow-y-auto">
          {batches.map((batch, idx) => {
            const isActive = batch.batch_id === currentBatchId;
            const isLatest = idx === 0;
            return (
              <button
                key={batch.batch_id}
                onClick={() => handleSelect(batch, isLatest)}
                className={`w-full text-left px-3 py-2 text-[11px] italic flex items-center gap-2 transition-colors ${
                  isActive
                    ? "bg-white/[0.06] text-white/90"
                    : "text-white/60 hover:bg-white/[0.04] hover:text-white/80"
                }`}
              >
                <span className="flex-1 truncate">
                  {formatTimestamp(batch.created_at)}
                  <span className="text-white/30 mx-1.5">&middot;</span>
                  <span className="text-white/40">{batch.candidate_count} candidates</span>
                </span>
                {isLatest && (
                  <span className="text-[9px] uppercase tracking-wider text-primary/70 flex-shrink-0">Latest</span>
                )}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
