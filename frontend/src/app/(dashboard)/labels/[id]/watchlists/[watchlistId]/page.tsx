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
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-white/35 mb-3">
          <Link href="/dashboard" className="hover:text-purple-300 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <Link href={`/labels/${id}/watchlists`} className="hover:text-purple-300 transition-colors duration-200">Watchlists</Link>
          <span>/</span>
          <span className="text-white">{detail.watchlist.name}</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{detail.watchlist.name}</h1>
            <p className="text-white/60 text-sm mt-1">{label.name} · {detail.items.length} artists</p>
          </div>
          <div className="flex gap-3">
            <Link href={`/labels/${id}/scout-feed`} className="text-sm text-purple-300/80 hover:text-purple-200 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 transition-all duration-200">
              Scout Feed
            </Link>
            <Link href={`/labels/${id}/watchlists`} className="text-sm text-white/40 hover:text-white/60 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-all duration-200">
              All Watchlists
            </Link>
          </div>
        </div>
      </div>

      <WatchlistDetailClient labelId={id} detail={detail} />
    </div>
  );
}
