"use client";

import Link from "next/link";
import type { BatchInfo } from "@/lib/api";

interface RunPickerProps {
  batches: BatchInfo[];
  currentBatchId: string;
  labelId: string;
  basePath: string;
  extraParams?: string;
}

export function RunPicker({ batches, currentBatchId, labelId, basePath, extraParams }: RunPickerProps) {
  if (batches.length <= 1) return null;

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  };

  return (
    <div className="mt-3 flex items-center gap-2 flex-wrap">
      <span className="text-xs text-white/35">Runs:</span>
      {batches.map((batch, idx) => {
        const isActive = batch.batch_id === currentBatchId;
        const isLatest = idx === 0;
        const params = new URLSearchParams();
        if (!isLatest) params.set("batch", batch.batch_id);
        if (extraParams) {
          const extra = new URLSearchParams(extraParams);
          extra.forEach((v, k) => { if (k !== "batch") params.set(k, v); });
        }
        const qs = params.toString();
        const href = `/labels/${labelId}/${basePath}${qs ? `?${qs}` : ""}`;

        return (
          <Link
            key={batch.batch_id}
            href={href}
            className={`inline-flex items-center gap-1.5 rounded-pill px-3 py-1 text-xs transition-all duration-200 ${
              isActive
                ? "bg-primary text-[#f5f5f0]"
                : "bg-transparent border border-white/[0.12] text-white/40 hover:border-primary hover:text-primary"
            }`}
          >
            {formatDate(batch.created_at)}
            <span className="opacity-60">{batch.candidate_count}</span>
            {isLatest && (
              <span className={`text-[9px] uppercase tracking-wider ${isActive ? "text-[#f5f5f0]/70" : "text-primary/70"}`}>
                Latest
              </span>
            )}
          </Link>
        );
      })}
    </div>
  );
}
