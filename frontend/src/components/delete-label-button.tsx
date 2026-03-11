"use client";

import { useRef, useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export function DeleteLabelButton({ labelId }: { labelId: string }) {
  const [confirming, setConfirming] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const router = useRouter();

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (confirming) {
      if (timerRef.current) clearTimeout(timerRef.current);
      setConfirming(false);
      api.deleteLabel(labelId).then(() => router.refresh());
    } else {
      setConfirming(true);
      timerRef.current = setTimeout(() => setConfirming(false), 3000);
    }
  };

  return (
    <button
      onClick={handleClick}
      className={`inline-flex items-center rounded-pill px-3 py-1.5 text-xs transition-all duration-200 hover:-translate-y-px ${
        confirming
          ? "bg-red-500/15 border border-red-500/30 text-red-400"
          : "bg-transparent border border-white/[0.08] text-white/25 hover:text-red-400 hover:border-red-400/30"
      }`}
      title={confirming ? "Click again to confirm" : "Delete this label"}
    >
      {confirming ? (
        "Delete?"
      ) : (
        <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      )}
    </button>
  );
}
