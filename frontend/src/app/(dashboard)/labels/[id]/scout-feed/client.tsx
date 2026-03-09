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
  const [expandedScores, setExpandedScores] = useState<Set<string>>(new Set());

  // Initialize watchlistAdded Set by checking which artists are already in watchlists
  useEffect(() => {
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
        await Promise.all(
          watchlists.map(async (watchlist) => {
            try {
              const detail = await api.getWatchlist(labelId, watchlist.id);
              detail.items.forEach((item) => {
                artistIdsInWatchlists.add(item.artist_id);
              });
            } catch (e) {
              console.error(`Failed to fetch watchlist ${watchlist.id}:`, e);
            }
          })
        );
        setWatchlistAdded(artistIdsInWatchlists);
      } catch (e) {
        console.error("Failed to check watchlists:", e);
      } finally {
        setCheckingWatchlists(false);
      }
    };

    checkWatchlists();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labelId]);

  const sendFeedback = async (artistId: string, action: string) => {
    try {
      await api.submitFeedback(labelId, { artist_id: artistId, action });
      setFeedbackSent((prev) => new Set(prev).add(artistId));
      router.refresh();
    } catch (e) {
      console.error("Feedback failed:", e);
    }
  };

  const toggleScores = (artistId: string) => {
    setExpandedScores((prev) => {
      const next = new Set(prev);
      if (next.has(artistId)) next.delete(artistId);
      else next.add(artistId);
      return next;
    });
  };

  if (items.length === 0) {
    const messages: Record<string, string> = {
      queued: "Pipeline queued. It will start shortly.",
      running: "Pipeline is running. Results will appear here shortly.",
      error: "Pipeline failed. Please retry the import or run again.",
      canceled: "Pipeline was canceled.",
    };
    return (
      <div className="bg-surface border border-white/[0.12] rounded-lg p-12 text-center relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
        <p className="text-white/60">{messages[pipelineStatus || ""] || "No candidates scored yet."}</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => {
        const showScores = expandedScores.has(item.artist_id);

        return (
          <div
            key={item.artist_id}
            className="bg-surface border border-white/[0.12] rounded-lg p-5 relative overflow-hidden hover:border-primary/40 hover:-translate-y-0.5 transition-all duration-200 group"
          >
            {/* Gradient top bar */}
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />

            <div className="flex items-start gap-4">
              {/* Vinyl instead of rank number */}
              <div className="vinyl flex-shrink-0" style={{ width: 50, height: 50 }}>
                <div className="rounded-full bg-[#0a0a0a] border-2 border-white/[0.12] absolute" style={{ width: 10, height: 10 }} />
              </div>

              <div className="flex-1 min-w-0">
                {/* Name + score badge */}
                <div className="flex items-center gap-3 mb-2">
                  <Link
                    href={`/artists/${item.artist_id}?label=${labelId}`}
                    className="font-display text-[18px] tracking-wide text-[#f5f5f0] hover:text-primary-light transition-colors duration-200"
                  >
                    {item.artist_name}
                  </Link>
                  {item.breakout_candidate && (
                    <span className="tag text-[10px]">Breakout Signal</span>
                  )}
                  {item.stage && (
                    <span className="text-xs bg-white/[0.03] text-white/35 px-2 py-0.5 rounded-full border border-white/[0.06]">
                      {item.stage}
                    </span>
                  )}
                </div>

                {/* Genre tags */}
                {(item.genre_tags || item.cultural_highlights) && (
                  <div className="flex flex-wrap gap-1 mb-3">
                    {item.genre_tags?.map((g) => (
                      <span key={g} className="tag">{g}</span>
                    ))}
                    {item.cultural_highlights?.map((h) => (
                      <span key={h} className="text-xs bg-white/[0.04] text-white/60 px-2 py-0.5 rounded-full border border-white/[0.06]">{h}</span>
                    ))}
                  </div>
                )}

                {/* Score bars (collapsible) */}
                <button
                  onClick={() => toggleScores(item.artist_id)}
                  className="text-[10px] text-white/30 hover:text-white/50 mb-2 transition-colors"
                >
                  {showScores ? "Hide scores" : "Show scores"} &middot; Fit {(item.fit_score * 100).toFixed(0)} / Mom. {(item.momentum_score * 100).toFixed(0)} / Risk {(item.risk_score * 100).toFixed(0)}
                </button>
                {showScores && (
                  <div className={`grid ${item.cultural_energy != null ? "grid-cols-4" : "grid-cols-3"} gap-3 mb-3`}>
                    <ScoreBar label="Fit" value={item.fit_score} color="bg-emerald-500" />
                    <ScoreBar label="Mom." value={item.momentum_score} color="bg-sky-500" />
                    <ScoreBar label="Risk" value={item.risk_score} color="bg-red-500" />
                    {item.cultural_energy != null && (
                      <ScoreBar label="Culture" value={item.cultural_energy} color="bg-primary" />
                    )}
                  </div>
                )}

                {/* Reasons */}
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

                {/* Growth metrics */}
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

                {/* Waveform decoration */}
                <div className="mt-3 wave" style={{ height: 20 }}>
                  {[8, 14, 6, 18, 10, 16, 7, 13, 20, 9, 15, 11, 5, 17, 12].map((h, i) => (
                    <div key={i} className="wave-bar" style={{ height: h, opacity: 0.25 + (i % 4) * 0.08 }} />
                  ))}
                </div>
              </div>

              {/* Match score badge (top-right) */}
              <div className="absolute top-4 right-4">
                <span className={`font-display text-[18px] tracking-wide ${scoreColor(item.final_score)} bg-primary/15 px-3 py-1 rounded-pill border border-primary/30`}>
                  {(item.final_score * 100).toFixed(0)}
                </span>
              </div>

              {/* Action buttons */}
              <div className="flex flex-col gap-1.5 shrink-0 mt-6">
                {feedbackSent.has(item.artist_id) ? (
                  <span className="text-xs text-emerald-400 px-3 py-1">Noted</span>
                ) : (
                  <>
                    <button
                      onClick={() => sendFeedback(item.artist_id, "shortlist")}
                      className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200 hover:-translate-y-px"
                    >
                      Shortlist
                    </button>
                    <button
                      onClick={() => sendFeedback(item.artist_id, "pass")}
                      className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-transparent border border-white/[0.12] text-white/40 hover:border-primary hover:text-primary transition-all duration-200 hover:-translate-y-px"
                    >
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
                    buttonClassName="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-transparent border border-white/[0.12] text-white/40 hover:border-primary hover:text-primary transition-all duration-200 hover:-translate-y-px"
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
        );
      })}
    </div>
  );
}
