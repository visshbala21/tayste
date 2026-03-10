import Link from "next/link";
import { api } from "@/lib/api";
import { PipelinePoller } from "@/components/pipeline-poller";
import { ScoutFeedClient } from "./client";

export default async function ScoutFeedPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ limit?: string }>;
}) {
  const { id } = await params;
  const resolvedSearch = searchParams ? await searchParams : undefined;
  const limit = Math.max(1, Math.min(parseInt(resolvedSearch?.limit || "50", 10) || 50, 200));
  const [feed, label, watchlists, rosterArtists] = await Promise.all([
    api.getScoutFeed(id, limit).catch(() => ({ label_id: id, batch_id: "", items: [], total: 0 })),
    api.getLabel(id),
    api.getWatchlists(id).catch(() => []),
    api.getRoster(id).catch(() => []),
  ]);

  // Pre-compute which artists are already in watchlists (server-side, avoids N client-side calls)
  let watchlistedArtistIds: string[] = [];
  if (watchlists.length > 0) {
    try {
      const details = await Promise.all(
        watchlists.map((w) => api.getWatchlist(id, w.id).catch(() => null))
      );
      const ids = new Set<string>();
      for (const detail of details) {
        if (detail) detail.items.forEach((item) => ids.add(item.artist_id));
      }
      watchlistedArtistIds = Array.from(ids);
    } catch {
      // ignore
    }
  }

  // Only show filter options that are less than or equal to total results
  const availableFilters = [20, 50, 100].filter((n) => feed.total >= n);
  const genreContext = (label.genre_tags as any)?.primary?.join(", ") || "";

  return (
    <div className="page-fade">
      <PipelinePoller status={label.pipeline_status} />

      {/* Back link + Header */}
      <div className="mb-6">
        <Link
          href="/dashboard"
          className="text-xs text-white/35 hover:text-primary-light transition-colors inline-flex items-center gap-1 mb-3"
        >
          &larr; Back to Home
        </Link>

        <h1 className="font-display text-[clamp(36px,8vw,72px)] leading-none tracking-wide text-[#f5f5f0]">
          SCOUT FEED
        </h1>
        {genreContext && (
          <p className="text-white/45 mt-2 italic text-sm">
            {label.name} &middot; {genreContext}
          </p>
        )}
        {!genreContext && (
          <p className="text-white/45 mt-2 italic text-sm">{label.name}</p>
        )}

        {/* Feature bar */}
        <div className="mt-4 bg-white/[0.06] border-y border-white/[0.12] py-2.5 px-0 text-[11px] text-white/50 tracking-wide">
          Sorted by Final Score &middot; AI-curated &middot; Showing top {feed.items.length} of {feed.total}
        </div>

        {/* Limit filters */}
        {availableFilters.length > 0 && (
          <div className="mt-3 flex items-center gap-2">
            <span className="text-xs text-white/35">Show:</span>
            {availableFilters.map((n) => (
              <Link
                key={n}
                href={`/labels/${id}/scout-feed?limit=${n}`}
                className={`inline-flex items-center rounded-pill px-3 py-1 text-xs transition-all duration-200 ${
                  limit === n
                    ? "bg-primary text-[#f5f5f0]"
                    : "bg-transparent border border-white/[0.12] text-white/40 hover:border-primary hover:text-primary"
                }`}
              >
                Top {n}
              </Link>
            ))}
          </div>
        )}
      </div>

      <ScoutFeedClient
        items={feed.items}
        labelId={id}
        pipelineStatus={label.pipeline_status}
        watchlists={watchlists}
        initialWatchlistedIds={watchlistedArtistIds}
        rosterArtists={rosterArtists}
      />
    </div>
  );
}
