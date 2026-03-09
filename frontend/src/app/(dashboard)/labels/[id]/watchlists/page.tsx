import Link from "next/link";
import { api } from "@/lib/api";
import { WatchlistsClient } from "./client";

export default async function WatchlistsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [label, watchlists, alerts] = await Promise.all([
    api.getLabel(id),
    api.getWatchlists(id),
    api.getAlerts(id, "new", 50),
  ]);

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-white/35 mb-3">
          <Link href="/dashboard" className="hover:text-purple-300 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <span className="text-white/35">{label.name}</span>
          <span>/</span>
          <span className="text-white">Watchlists</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{label.name}</h1>
            <p className="text-white/60 text-sm mt-1">Watchlists &amp; Alerts</p>
          </div>
          <div className="flex gap-3">
            <Link href={`/labels/${id}/scout-feed`} className="text-sm text-purple-300/80 hover:text-purple-200 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 transition-all duration-200">
              Scout Feed
            </Link>
            <Link href={`/labels/${id}/taste-map`} className="text-sm text-purple-300/80 hover:text-purple-200 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 transition-all duration-200">
              Taste Map
            </Link>
          </div>
        </div>
      </div>

      <WatchlistsClient
        labelId={id}
        initialWatchlists={watchlists}
        initialAlerts={alerts}
      />
    </div>
  );
}
