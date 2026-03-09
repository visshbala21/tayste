"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { FeedbackAction } from "@/types";

const ACTIONS: { action: FeedbackAction; label: string; color: string }[] = [
  { action: "shortlist", label: "Shortlist", color: "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500/20" },
  { action: "sign", label: "Sign", color: "bg-purple-500/10 text-purple-300 border border-purple-500/20 hover:bg-purple-500/15" },
  { action: "pass", label: "Pass", color: "bg-white/[0.03] text-white/40 border border-white/[0.06] hover:bg-white/[0.05]" },
  { action: "archive", label: "Archive", color: "bg-red-500/10 text-red-400 border border-red-500/20 hover:bg-red-500/20" },
];

export function ArtistFeedback({
  artistId,
  labelId,
  history,
}: {
  artistId: string;
  labelId: string;
  history: { action: string; notes?: string; created_at: string }[];
}) {
  const router = useRouter();
  const [notes, setNotes] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (action: string) => {
    setLoading(true);
    try {
      await api.submitFeedback(labelId, { artist_id: artistId, action, notes: notes || undefined });
      setSubmitted(true);
      router.refresh();
    } catch (e) {
      console.error("Feedback failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
      <h2 className="text-lg font-bold mb-4 text-white">A&amp;R Feedback</h2>

      {submitted ? (
        <p className="text-emerald-400">Feedback recorded.</p>
      ) : (
        <div className="space-y-4">
          <textarea
            className="w-full bg-white/[0.03] border border-white/[0.08] rounded-xl p-3 text-sm text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30 resize-none"
            rows={3}
            placeholder="Notes (optional)..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <div className="flex gap-2">
            {ACTIONS.map(({ action, label, color }) => (
              <button key={action} onClick={() => submit(action)} disabled={loading}
                className={`text-sm px-4 py-2 rounded-lg transition ${color} disabled:opacity-50`}>
                {label}
              </button>
            ))}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="mt-6 border-t border-white/[0.06] pt-4">
          <h3 className="text-sm text-white/35 mb-2">History</h3>
          <div className="space-y-2">
            {history.map((fb, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-xs bg-white/[0.03] px-2 py-0.5 rounded border border-white/[0.06] text-white/35">{fb.action}</span>
                {fb.notes && <span className="text-white/35">{fb.notes}</span>}
                <span className="text-white/35 text-xs ml-auto">{new Date(fb.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
