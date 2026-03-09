import Link from "next/link";
import { api } from "@/lib/api";
import { WatchlistDetailClient } from "./client";

export default async function WatchlistDetailPage({
  params,
}: {
  params: Promise<{ id: string; watchlistId: string }>;
}) {
  const { id, watchlistId } = await params;
  const [label, detail] = await Promise.all([
    api.getLabel(id),
    api.getWatchlist(id, watchlistId),
  ]);

  return (
    <div className="page-fade">
      <div className="mb-6">
        <Link
          href={`/labels/${id}/watchlists`}
          className="text-xs text-white/35 hover:text-primary-light transition-colors inline-flex items-center gap-1 mb-3"
        >
          &larr; Back to Collections
        </Link>
        <h1 className="font-display text-[clamp(36px,8vw,60px)] leading-none tracking-wide text-[#f5f5f0]">
          {detail.watchlist.name.toUpperCase()}
        </h1>
        <p className="text-white/45 mt-2 italic text-sm">
          {label.name} &middot; {detail.items.length} artists
        </p>

        <div className="flex gap-2 mt-4">
          <Link
            href={`/labels/${id}/scout-feed`}
            className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200 hover:-translate-y-px"
          >
            Scout Feed
          </Link>
          <Link
            href={`/labels/${id}/watchlists`}
            className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-transparent border border-white/[0.12] text-white/40 hover:border-primary hover:text-primary transition-all duration-200 hover:-translate-y-px"
          >
            All Collections
          </Link>
        </div>
      </div>

      <WatchlistDetailClient labelId={id} detail={detail} />
    </div>
  );
}
