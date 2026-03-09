import Link from "next/link";
import { api } from "@/lib/api";
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
  const [feed, label, watchlists] = await Promise.all([
    api.getScoutFeed(id, limit),
    api.getLabel(id),
    api.getWatchlists(id),
  ]);

  // Only show filter options that are less than or equal to total results
  const availableFilters = [20, 50, 100].filter((n) => feed.total >= n);

  return (
    <div>
      {/* Breadcrumb + header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-white/35 mb-3">
          <Link href="/dashboard" className="hover:text-purple-300 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <span className="text-white/35">{label.name}</span>
          <span>/</span>
          <span className="text-white">Scout Feed</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{label.name}</h1>
            <p className="text-white/60 text-sm mt-1">
              Scout Feed &middot; Showing top {feed.items.length} of {feed.total} candidates
            </p>
          </div>
          <div className="flex gap-3">
            <Link href={`/labels/${id}/taste-map`} className="text-sm text-purple-300/80 hover:text-purple-200 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 transition-all duration-200">
              Taste Map
            </Link>
            <Link href={`/labels/${id}/watchlists`} className="text-sm text-white/40 hover:text-white/60 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-all duration-200">
              Watchlists
            </Link>
            <Link href="/dashboard" className="text-sm text-white/40 hover:text-white/60 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-all duration-200">
              All Labels
            </Link>
          </div>
        </div>
        {availableFilters.length > 0 && (
          <div className="mt-3 flex items-center gap-2 text-xs text-white/35">
            <span>Show:</span>
            {availableFilters.map((n) => (
              <Link
                key={n}
                href={`/labels/${id}/scout-feed?limit=${n}`}
                className={`px-2 py-1 rounded ${limit === n ? "bg-purple-500/10 text-purple-300 border border-purple-500/20" : "bg-white/[0.03] border border-white/[0.06] text-white/40 hover:text-white/60 hover:bg-white/[0.05]"}`}
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
      />
    </div>
  );
}
