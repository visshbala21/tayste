import Link from "next/link";
import { api } from "@/lib/api";
import { WatchlistsClient } from "./client";

export const dynamic = "force-dynamic";

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
        <div className="flex items-center gap-2 text-xs text-muted mb-3">
          <Link href="/dashboard" className="hover:text-gray-200 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <span className="text-gray-400">{label.name}</span>
          <span>/</span>
          <span className="text-gray-200">Watchlists</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{label.name}</h1>
            <p className="text-muted text-sm mt-1">Watchlists &amp; Alerts</p>
          </div>
          <div className="flex gap-3">
            <Link href={`/labels/${id}/scout-feed`} className="text-sm bg-primary/10 text-primary px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-all duration-200">
              Scout Feed
            </Link>
            <Link href={`/labels/${id}/taste-map`} className="text-sm bg-accent/10 text-accent px-3 py-1.5 rounded-lg hover:bg-accent/20 transition-all duration-200">
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
