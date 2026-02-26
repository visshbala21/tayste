import Link from "next/link";
import { api } from "@/lib/api";
import { WatchlistDetailClient } from "./client";

export const dynamic = "force-dynamic";

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
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-muted mb-3">
          <Link href="/dashboard" className="hover:text-gray-200 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <Link href={`/labels/${id}/watchlists`} className="hover:text-gray-200 transition-colors duration-200">Watchlists</Link>
          <span>/</span>
          <span className="text-gray-200">{detail.watchlist.name}</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{detail.watchlist.name}</h1>
            <p className="text-muted text-sm mt-1">{label.name} · {detail.items.length} artists</p>
          </div>
          <div className="flex gap-3">
            <Link href={`/labels/${id}/scout-feed`} className="text-sm bg-primary/10 text-primary px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-all duration-200">
              Scout Feed
            </Link>
            <Link href={`/labels/${id}/watchlists`} className="text-sm bg-surface-light text-muted px-3 py-1.5 rounded-lg hover:text-gray-200 transition-all duration-200">
              All Watchlists
            </Link>
          </div>
        </div>
      </div>

      <WatchlistDetailClient labelId={id} detail={detail} />
    </div>
  );
}
