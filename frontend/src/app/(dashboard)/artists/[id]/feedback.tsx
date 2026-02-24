"use client";

import { useState } from "react";
import type { FeedbackAction } from "@/types";

const ACTIONS: { action: FeedbackAction; label: string; color: string }[] = [
  { action: "shortlist", label: "Shortlist", color: "bg-success/10 text-success hover:bg-success/20" },
  { action: "sign", label: "Sign", color: "bg-primary/10 text-primary hover:bg-primary/20" },
  { action: "pass", label: "Pass", color: "bg-surface-light text-muted hover:bg-border" },
  { action: "archive", label: "Archive", color: "bg-danger/10 text-danger hover:bg-danger/20" },
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
  const [notes, setNotes] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [loading, setLoading] = useState(false);

  const submit = async (action: string) => {
    setLoading(true);
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      await fetch(`${API_BASE}/api/labels/${labelId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artist_id: artistId, action, notes: notes || undefined }),
      });
      setSubmitted(true);
    } catch (e) {
      console.error("Feedback failed:", e);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-surface border border-border rounded-lg p-6">
      <h2 className="text-lg font-semibold mb-4">A&amp;R Feedback</h2>

      {submitted ? (
        <p className="text-success">Feedback recorded.</p>
      ) : (
        <div className="space-y-4">
          <textarea
            className="w-full bg-surface-light border border-border rounded-lg p-3 text-sm text-gray-200 placeholder-muted focus:outline-none focus:border-primary/50 resize-none"
            rows={3}
            placeholder="Notes (optional)..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
          />
          <div className="flex gap-2">
            {ACTIONS.map(({ action, label, color }) => (
              <button key={action} onClick={() => submit(action)} disabled={loading}
                className={`text-sm px-4 py-2 rounded transition ${color} disabled:opacity-50`}>
                {label}
              </button>
            ))}
          </div>
        </div>
      )}

      {history.length > 0 && (
        <div className="mt-6 border-t border-border pt-4">
          <h3 className="text-sm text-muted mb-2">History</h3>
          <div className="space-y-2">
            {history.map((fb, i) => (
              <div key={i} className="flex items-center gap-3 text-sm">
                <span className="text-xs bg-surface-light px-2 py-0.5 rounded">{fb.action}</span>
                {fb.notes && <span className="text-gray-400">{fb.notes}</span>}
                <span className="text-muted text-xs ml-auto">{new Date(fb.created_at).toLocaleDateString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
