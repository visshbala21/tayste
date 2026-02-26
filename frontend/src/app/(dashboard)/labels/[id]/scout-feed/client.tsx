"use client";

import Link from "next/link";
import { useState } from "react";
import type { ScoutFeedItem } from "@/lib/api";
import { formatPercent, scoreColor } from "@/lib/utils";

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-muted w-10">{label}</span>
      <div className="flex-1 h-1.5 bg-surface-light rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(value * 100, 2)}%` }} />
      </div>
      <span className="w-10 text-right font-mono">{(value * 100).toFixed(0)}</span>
    </div>
  );
}

export function ScoutFeedClient({
  items,
  labelId,
  pipelineStatus,
  defaultWatchlistId,
}: {
  items: ScoutFeedItem[];
  labelId: string;
  pipelineStatus?: string;
  defaultWatchlistId?: string;
}) {
  const [feedbackSent, setFeedbackSent] = useState<Set<string>>(new Set());
  const [watchlistAdded, setWatchlistAdded] = useState<Set<string>>(new Set());

  const sendFeedback = async (artistId: string, action: string) => {
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      await fetch(`${API_BASE}/api/labels/${labelId}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artist_id: artistId, action }),
      });
      setFeedbackSent((prev) => new Set(prev).add(artistId));
    } catch (e) {
      console.error("Feedback failed:", e);
    }
  };

  const addToWatchlist = async (artistId: string) => {
    if (!defaultWatchlistId) return;
    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      await fetch(`${API_BASE}/api/labels/${labelId}/watchlists/${defaultWatchlistId}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artist_id: artistId }),
      });
      setWatchlistAdded((prev) => new Set(prev).add(artistId));
    } catch (e) {
      console.error("Watchlist add failed:", e);
    }
  };

  if (items.length === 0) {
    if (pipelineStatus === "queued") {
      return (
        <div className="bg-surface border border-border rounded-lg p-12 text-center">
          <p className="text-muted">Pipeline queued. It will start shortly.</p>
        </div>
      );
    }
    if (pipelineStatus === "running") {
      return (
        <div className="bg-surface border border-border rounded-lg p-12 text-center">
          <p className="text-muted">Pipeline is running. Results will appear here shortly.</p>
        </div>
      );
    }
    if (pipelineStatus === "error") {
      return (
        <div className="bg-surface border border-border rounded-lg p-12 text-center">
          <p className="text-muted">Pipeline failed. Please retry the import or run again.</p>
        </div>
      );
    }
    if (pipelineStatus === "canceled") {
      return (
        <div className="bg-surface border border-border rounded-lg p-12 text-center">
          <p className="text-muted">Pipeline was canceled.</p>
        </div>
      );
    }
    return (
      <div className="bg-surface border border-border rounded-lg p-12 text-center">
        <p className="text-muted">No candidates scored yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={item.artist_id} className="bg-surface border border-border rounded-lg p-5 hover:border-primary/30 transition-all duration-200">
          <div className="flex items-start gap-4">
            <div className="text-2xl font-bold text-muted w-8 text-right shrink-0">
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <Link href={`/artists/${item.artist_id}?label=${labelId}`}
                  className="text-lg font-semibold hover:text-primary transition-colors duration-200">
                  {item.artist_name}
                </Link>
                <span className={`text-sm font-mono font-bold ${scoreColor(item.final_score)}`}>
                  {(item.final_score * 100).toFixed(0)}
                </span>
                {item.stage && (
                  <span className="text-xs bg-surface-light text-muted px-2 py-0.5 rounded">
                    {item.stage}
                  </span>
                )}
              </div>

              {item.genre_tags && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {item.genre_tags.map((g) => (
                    <span key={g} className="text-xs bg-surface-light text-gray-400 px-2 py-0.5 rounded">{g}</span>
                  ))}
                </div>
              )}

              <div className="grid grid-cols-3 gap-3 mb-3">
                <ScoreBar label="Fit" value={item.fit_score} color="bg-primary" />
                <ScoreBar label="Mom." value={item.momentum_score} color="bg-accent" />
                <ScoreBar label="Risk" value={item.risk_score} color="bg-danger" />
              </div>

              {item.reasons && item.reasons.length > 0 && (
                <div className="flex flex-wrap gap-2 text-xs text-muted mb-2">
                  {item.reasons.map((reason) => (
                    <span
                      key={`${item.artist_id}-${reason}`}
                      className="bg-surface-light px-2 py-0.5 rounded text-gray-400"
                    >
                      {reason}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-4 text-xs text-muted">
                {item.growth_7d != null && (
                  <span className={item.growth_7d > 0 ? "text-success" : "text-danger"}>
                    7d: {item.growth_7d > 0 ? "+" : ""}{formatPercent(item.growth_7d)}
                  </span>
                )}
                {item.growth_30d != null && (
                  <span className={item.growth_30d > 0 ? "text-success" : "text-danger"}>
                    30d: {item.growth_30d > 0 ? "+" : ""}{formatPercent(item.growth_30d)}
                  </span>
                )}
                {item.nearest_roster_artist && (
                  <span>Similar to: <span className="text-primary-light">{item.nearest_roster_artist}</span></span>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-1 shrink-0">
              {feedbackSent.has(item.artist_id) ? (
                <span className="text-xs text-success px-3 py-1">Noted</span>
              ) : (
                <>
                  <button onClick={() => sendFeedback(item.artist_id, "shortlist")}
                    className="text-xs bg-success/10 text-success px-3 py-1 rounded hover:bg-success/20 transition-all duration-200">
                    Shortlist
                  </button>
                  <button onClick={() => sendFeedback(item.artist_id, "pass")}
                    className="text-xs bg-surface-light text-muted px-3 py-1 rounded hover:bg-border transition-all duration-200">
                    Pass
                  </button>
                </>
              )}
              {defaultWatchlistId && (
                watchlistAdded.has(item.artist_id) ? (
                  <span className="text-xs text-accent px-3 py-1">Watching</span>
                ) : (
                  <button onClick={() => addToWatchlist(item.artist_id)}
                    className="text-xs bg-accent/10 text-accent px-3 py-1 rounded hover:bg-accent/20 transition-all duration-200">
                    Watch
                  </button>
                )
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
