"use client";

import { useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, type BatchInfo } from "@/lib/api";

interface LabelRunsProps {
  labelId: string;
  batches: BatchInfo[];
  isRunning: boolean;
}

function formatTimestamp(iso: string) {
  const d = new Date(iso);
  const date = d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
  const time = d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  return `${date} at ${time}`;
}

export function LabelRuns({ labelId, batches, isRunning }: LabelRunsProps) {
  const [expanded, setExpanded] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [localBatches, setLocalBatches] = useState(batches);
  const deleteTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const router = useRouter();

  useEffect(() => {
    setLocalBatches(batches);
  }, [batches]);

  useEffect(() => {
    return () => {
      if (deleteTimerRef.current) clearTimeout(deleteTimerRef.current);
    };
  }, []);

  if (localBatches.length === 0 && !isRunning) {
    return <p className="text-xs text-white/20 mt-1">No runs yet</p>;
  }

  if (localBatches.length === 0 && isRunning) {
    return <p className="text-xs text-amber-300/60 mt-1">Running...</p>;
  }

  const latest = localBatches[0];
  const latestDate = new Date(latest.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric" });

  const handleDelete = (e: React.MouseEvent, batchId: string) => {
    e.stopPropagation();
    if (deletingId === batchId) {
      if (deleteTimerRef.current) clearTimeout(deleteTimerRef.current);
      setDeletingId(null);
      // Optimistic removal
      setLocalBatches((prev) => prev.filter((b) => b.batch_id !== batchId));
      api.deleteBatch(labelId, batchId).then(() => {
        router.refresh();
      });
    } else {
      setDeletingId(batchId);
      if (deleteTimerRef.current) clearTimeout(deleteTimerRef.current);
      deleteTimerRef.current = setTimeout(() => setDeletingId(null), 3000);
    }
  };

  return (
    <div className="mt-1">
      {/* Summary line */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="text-xs text-white/30 hover:text-white/50 transition-colors flex items-center gap-1.5"
      >
        {isRunning && <span className="text-amber-300/60">Running...</span>}
        {isRunning && <span className="text-white/15">&middot;</span>}
        <span>
          {localBatches.length} {localBatches.length === 1 ? "run" : "runs"}
        </span>
        <span className="text-white/15">&middot;</span>
        <span>Latest: {latestDate}</span>
        <span className="text-white/15">&middot;</span>
        <span>{latest.candidate_count} candidates</span>
        <svg
          className={`w-3 h-3 opacity-40 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Expanded runs list */}
      {expanded && (
        <div className="mt-2 bg-white/[0.02] border border-white/[0.06] rounded-lg overflow-hidden">
          {localBatches.map((batch, idx) => {
            const isLatest = idx === 0;
            const isDeleting = deletingId === batch.batch_id;
            return (
              <div
                key={batch.batch_id}
                className="flex items-center gap-2 px-3 py-1.5 text-[11px] italic text-white/50 border-b border-white/[0.04] last:border-b-0"
              >
                <span className="flex-1">
                  {formatTimestamp(batch.created_at)}
                  <span className="text-white/20 mx-1.5">&middot;</span>
                  <span className="text-white/30">{batch.candidate_count} candidates</span>
                </span>
                {isLatest && (
                  <span className="text-[9px] uppercase tracking-wider text-primary/60">Latest</span>
                )}
                <button
                  onClick={(e) => handleDelete(e, batch.batch_id)}
                  className={`flex-shrink-0 px-1.5 py-0.5 rounded transition-colors ${
                    isDeleting
                      ? "text-red-400 text-[10px] font-medium"
                      : "text-white/15 hover:text-red-400"
                  }`}
                  title={isDeleting ? "Click again to confirm" : "Delete this run"}
                >
                  {isDeleting ? (
                    "Delete?"
                  ) : (
                    <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
