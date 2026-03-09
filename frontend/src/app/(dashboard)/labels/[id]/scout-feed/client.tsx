"use client";

import Link from "next/link";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { api, type ScoutFeedItem, type Watchlist } from "@/lib/api";
import { formatPercent, scoreColor } from "@/lib/utils";
import { WatchlistPickerButton } from "@/components/watchlist-picker-button";

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-white/35 w-10">{label}</span>
      <div className="flex-1 h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${Math.max(value * 100, 2)}%` }} />
      </div>
      <span className="w-10 text-right font-mono text-white/60">{(value * 100).toFixed(0)}</span>
    </div>
  );
}

export function ScoutFeedClient({
  items,
  labelId,
  pipelineStatus,
  watchlists,
}: {
  items: ScoutFeedItem[];
  labelId: string;
  pipelineStatus?: string;
  watchlists: Watchlist[];
}) {
  const router = useRouter();
  const [feedbackSent, setFeedbackSent] = useState<Set<string>>(new Set());
  const [watchlistAdded, setWatchlistAdded] = useState<Set<string>>(new Set());
  const [checkingWatchlists, setCheckingWatchlists] = useState(true);

  // Initialize watchlistAdded Set by checking which artists are already in watchlists
  useEffect(() => {
    // Only run on client side
    if (typeof window === "undefined") {
      setCheckingWatchlists(false);
      return;
    }

    const checkWatchlists = async () => {
      if (watchlists.length === 0) {
        setCheckingWatchlists(false);
        return;
      }

      try {
        const artistIdsInWatchlists = new Set<string>();

        // Check all watchlists to see which artists are already in them
        await Promise.all(
          watchlists.map(async (watchlist) => {
            try {
              const detail = await api.getWatchlist(labelId, watchlist.id);
              detail.items.forEach((item) => {
                artistIdsInWatchlists.add(item.artist_id);
              });
            } catch (e) {
              // If we can't fetch a watchlist, skip it
              console.error(`Failed to fetch watchlist ${watchlist.id}:`, e);
            }
          })
        );

        setWatchlistAdded(artistIdsInWatchlists);
      } catch (e) {
        // If checking fails, continue with empty set
        console.error("Failed to check watchlists:", e);
      } finally {
        setCheckingWatchlists(false);
      }
    };

    checkWatchlists();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labelId]); // Only depend on labelId, watchlists array reference may change

  const sendFeedback = async (artistId: string, action: string) => {
    try {
      await api.submitFeedback(labelId, { artist_id: artistId, action });
      setFeedbackSent((prev) => new Set(prev).add(artistId));
      router.refresh();
    } catch (e) {
      console.error("Feedback failed:", e);
    }
  };

  if (items.length === 0) {
    if (pipelineStatus === "queued") {
      return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-12 text-center">
          <p className="text-white/60">Pipeline queued. It will start shortly.</p>
        </div>
      );
    }
    if (pipelineStatus === "running") {
      return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-12 text-center">
          <p className="text-white/60">Pipeline is running. Results will appear here shortly.</p>
        </div>
      );
    }
    if (pipelineStatus === "error") {
      return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-12 text-center">
          <p className="text-white/60">Pipeline failed. Please retry the import or run again.</p>
        </div>
      );
    }
    if (pipelineStatus === "canceled") {
      return (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-12 text-center">
          <p className="text-white/60">Pipeline was canceled.</p>
        </div>
      );
    }
    return (
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-12 text-center">
        <p className="text-white/60">No candidates scored yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item, idx) => (
        <div key={item.artist_id} className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 hover:border-purple-500/20 hover:bg-white/[0.03] transition-all duration-200">
          <div className="flex items-start gap-4">
            <div className="text-2xl font-bold text-white/35 w-8 text-right shrink-0">
              {idx + 1}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-3 mb-2">
                <Link href={`/artists/${item.artist_id}?label=${labelId}`}
                  className="text-lg font-semibold text-white hover:text-purple-200 transition-colors duration-200">
                  {item.artist_name}
                </Link>
                <span className={`text-sm font-mono font-bold ${scoreColor(item.final_score)}`}>
                  {(item.final_score * 100).toFixed(0)}
                </span>
                {item.breakout_candidate && (
                  <span className="text-xs bg-purple-500/10 text-purple-300 px-2 py-0.5 rounded-full border border-purple-500/20 font-medium">
                    Breakout Signal
                  </span>
                )}
                {item.stage && (
                  <span className="text-xs bg-white/[0.03] text-white/35 px-2 py-0.5 rounded-full border border-white/[0.06]">
                    {item.stage}
                  </span>
                )}
              </div>

              {(item.genre_tags || item.cultural_highlights) && (
                <div className="flex flex-wrap gap-1 mb-3">
                  {item.genre_tags?.map((g) => (
                    <span key={g} className="text-xs bg-white/[0.03] text-white/35 px-2 py-0.5 rounded border border-white/[0.06]">{g}</span>
                  ))}
                  {item.cultural_highlights?.map((h) => (
                    <span key={h} className="text-xs bg-white/[0.04] text-white/60 px-2 py-0.5 rounded border border-white/[0.06]">{h}</span>
                  ))}
                </div>
              )}

              <div className={`grid ${item.cultural_energy != null ? "grid-cols-4" : "grid-cols-3"} gap-3 mb-3`}>
                <ScoreBar label="Fit" value={item.fit_score} color="bg-emerald-500" />
                <ScoreBar label="Mom." value={item.momentum_score} color="bg-sky-500" />
                <ScoreBar label="Risk" value={item.risk_score} color="bg-red-500" />
                {item.cultural_energy != null && (
                  <ScoreBar label="Culture" value={item.cultural_energy} color="bg-purple-500" />
                )}
              </div>

              {item.reasons && item.reasons.length > 0 && (
                <div className="flex flex-wrap gap-2 text-xs text-white/35 mb-2">
                  {item.reasons.map((reason) => (
                    <span
                      key={`${item.artist_id}-${reason}`}
                      className="bg-white/[0.03] px-2 py-0.5 rounded border border-white/[0.06] text-white/35"
                    >
                      {reason}
                    </span>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-4 text-xs text-white/35">
                {item.growth_7d != null && (
                  <span className={item.growth_7d > 0 ? "text-emerald-400" : "text-red-400"}>
                    7d: {item.growth_7d > 0 ? "+" : ""}{formatPercent(item.growth_7d)}
                  </span>
                )}
                {item.growth_30d != null && (
                  <span className={item.growth_30d > 0 ? "text-emerald-400" : "text-red-400"}>
                    30d: {item.growth_30d > 0 ? "+" : ""}{formatPercent(item.growth_30d)}
                  </span>
                )}
                {item.nearest_roster_artist && (
                  <span>Similar to: <span className="text-white/60">{item.nearest_roster_artist}</span></span>
                )}
              </div>
            </div>

            <div className="flex flex-col gap-1 shrink-0">
              {feedbackSent.has(item.artist_id) ? (
                <span className="text-xs text-emerald-400 px-3 py-1">Noted</span>
              ) : (
                <>
                  <button onClick={() => sendFeedback(item.artist_id, "shortlist")}
                    className="text-xs bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded border border-emerald-500/20 hover:bg-emerald-500/20 transition-all duration-200">
                    Shortlist
                  </button>
                  <button onClick={() => sendFeedback(item.artist_id, "pass")}
                    className="text-xs bg-white/[0.03] text-white/40 px-3 py-1 rounded border border-white/[0.06] hover:bg-white/[0.05] transition-all duration-200">
                    Pass
                  </button>
                </>
              )}
              {watchlistAdded.has(item.artist_id) ? (
                <span className="text-xs text-white/60 px-3 py-1">Watching</span>
              ) : (
                <WatchlistPickerButton
                  labelId={labelId}
                  artistId={item.artist_id}
                  watchlists={watchlists}
                  defaultWatchlistId={watchlists[0]?.id}
                  buttonClassName="text-xs bg-white/[0.03] text-white/40 px-3 py-1 rounded border border-white/[0.06] hover:bg-white/[0.05] transition-all duration-200"
                  buttonLabel="Watch"
                  onAdded={() => {
                    setWatchlistAdded((prev) => new Set(prev).add(item.artist_id));
                    router.refresh();
                  }}
                />
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
