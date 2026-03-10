"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { BatchInfo, Label } from "@/lib/api";

const PINNED_KEY = "tayste:pinned-batch";

interface PinnedBatch {
  labelId: string;
  batchId: string;
}

function getPinned(): PinnedBatch | null {
  try {
    const raw = window.localStorage.getItem(PINNED_KEY);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function setPinned(val: PinnedBatch | null) {
  if (val) {
    window.localStorage.setItem(PINNED_KEY, JSON.stringify(val));
  } else {
    window.localStorage.removeItem(PINNED_KEY);
  }
}

interface LabelCardsProps {
  labels: Label[];
  labelBatches: Record<string, BatchInfo | null>;
}

export function LabelCards({ labels, labelBatches }: LabelCardsProps) {
  const [pinned, setPinnedState] = useState<PinnedBatch | null>(null);

  useEffect(() => {
    setPinnedState(getPinned());
  }, []);

  const handleToggle = (labelId: string, batchId: string) => {
    if (pinned?.labelId === labelId) {
      // Turn off
      setPinned(null);
      setPinnedState(null);
    } else {
      // Pin this label's batch (turns off any previous)
      const val = { labelId, batchId };
      setPinned(val);
      setPinnedState(val);
    }
  };

  return (
    <div className="grid gap-4">
      {labels.map((label) => {
        const lastBatch = labelBatches[label.id];
        const isRunning = label.pipeline_status === "running" || label.pipeline_status === "queued";
        const isPinned = pinned?.labelId === label.id;
        const batchQuery = isPinned && pinned?.batchId ? `?batch=${pinned.batchId}` : "";

        return (
          <div
            key={label.id}
            className={`bg-surface border rounded-lg p-5 relative overflow-hidden transition-all duration-300 group ${
              isPinned
                ? "border-primary/50 ring-1 ring-primary/20"
                : "border-white/[0.12] hover:border-primary/40"
            }`}
          >
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-display text-[22px] tracking-wide text-[#f5f5f0] group-hover:text-primary-light transition">
                    {label.name}
                  </h3>
                  <PipelineBadge status={label.pipeline_status} />

                  {/* iOS-style toggle — only show if there's a batch to pin */}
                  {lastBatch && (
                    <button
                      onClick={() => handleToggle(label.id, lastBatch.batch_id)}
                      className={`relative inline-flex h-[22px] w-[40px] items-center rounded-full transition-colors duration-200 flex-shrink-0 ${
                        isPinned ? "bg-emerald-500" : "bg-white/[0.12]"
                      }`}
                      title={isPinned ? "Unpin this run" : "Pin this run"}
                    >
                      <span
                        className={`inline-block h-[18px] w-[18px] rounded-full bg-white shadow-sm transition-transform duration-200 ${
                          isPinned ? "translate-x-[20px]" : "translate-x-[2px]"
                        }`}
                      />
                    </button>
                  )}
                </div>
                <p className="text-white/35 text-sm mt-1">{label.description}</p>

                {/* Batch info line */}
                {(() => {
                  if (isRunning && lastBatch) {
                    const d = new Date(lastBatch.created_at);
                    const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
                    return (
                      <p className="text-xs text-amber-300/60 mt-1">
                        Running... &middot; Last run: {dateStr} &middot; {lastBatch.candidate_count} candidates
                      </p>
                    );
                  }
                  if (lastBatch) {
                    const d = new Date(lastBatch.created_at);
                    const dateStr = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
                    return (
                      <p className={`text-xs mt-1 ${isPinned ? "text-primary/60" : "text-white/30"}`}>
                        {isPinned && <span className="text-emerald-400/70 mr-1">Pinned</span>}
                        Last run: {dateStr} &middot; {lastBatch.candidate_count} candidates
                      </p>
                    );
                  }
                  if (!isRunning) {
                    return <p className="text-xs text-white/20 mt-1">No runs yet</p>;
                  }
                  return <p className="text-xs text-amber-300/60 mt-1">Running...</p>;
                })()}

                {label.genre_tags && (
                  <div className="flex gap-2 mt-3">
                    {(label.genre_tags as any).primary?.map((g: string) => (
                      <span key={g} className="tag">{g}</span>
                    ))}
                  </div>
                )}

                {/* Waveform decoration */}
                <div className="mt-3 wave" style={{ height: 24 }}>
                  {[12, 20, 8, 24, 16, 22, 10, 18, 26, 14, 20, 12].map((h, i) => (
                    <div
                      key={i}
                      className="wave-bar"
                      style={{ height: h, opacity: 0.3 + (i % 3) * 0.1 }}
                    />
                  ))}
                </div>
              </div>
              <div className="flex gap-2 ml-4">
                <Link
                  href={`/labels/${label.id}/scout-feed${batchQuery}`}
                  className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200 hover:-translate-y-px"
                >
                  Scout Feed
                </Link>
                <Link
                  href={`/labels/${label.id}/taste-map${batchQuery}`}
                  className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200 hover:-translate-y-px"
                >
                  Taste Map
                </Link>
                <Link
                  href={`/labels/${label.id}/watchlists`}
                  className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-transparent border border-white/[0.12] text-white/40 hover:bg-white/[0.05] hover:text-white/60 transition-all duration-200 hover:-translate-y-px"
                >
                  Collections
                </Link>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PipelineBadge({ status }: { status?: string }) {
  if (status === "queued") {
    return (
      <span className="inline-flex items-center gap-1.5 text-[11px] bg-amber-500/10 text-amber-300/80 px-2.5 py-0.5 rounded-pill border border-amber-500/20">
        <span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400/80 animate-pulse" />
        Queued
      </span>
    );
  }
  if (status === "running") {
    return (
      <span className="inline-flex items-center gap-1.5 text-[11px] bg-primary/10 text-primary-light px-2.5 py-0.5 rounded-pill border border-primary/20">
        <svg className="animate-spin h-3 w-3" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        Running
      </span>
    );
  }
  if (status === "complete") {
    return (
      <span className="text-[11px] bg-emerald-500/10 text-emerald-300/80 px-2.5 py-0.5 rounded-pill border border-emerald-500/20">
        Ready
      </span>
    );
  }
  if (status === "error") {
    return (
      <span className="text-[11px] bg-red-500/10 text-red-300/80 px-2.5 py-0.5 rounded-pill border border-red-500/20">
        Error
      </span>
    );
  }
  if (status === "canceled") {
    return (
      <span className="text-[11px] bg-white/[0.04] text-white/30 px-2.5 py-0.5 rounded-pill border border-white/[0.06]">
        Canceled
      </span>
    );
  }
  return (
    <span className="text-[11px] bg-white/[0.04] text-white/30 px-2.5 py-0.5 rounded-pill border border-white/[0.06]">
      Not run
    </span>
  );
}
