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
    <div className="page-fade">
      <div className="mb-6">
        <Link
          href="/dashboard"
          className="text-xs text-white/35 hover:text-primary-light transition-colors inline-flex items-center gap-1 mb-3"
        >
          &larr; Back to Home
        </Link>
        <h1 className="font-display text-[clamp(36px,8vw,72px)] leading-none tracking-wide text-[#f5f5f0]">
          COLLECTIONS
        </h1>
        <p className="text-white/45 mt-2 italic text-sm">{label.name} &middot; Watchlists &amp; Alerts</p>

        <div className="flex gap-2 mt-4">
          <Link
            href={`/labels/${id}/scout-feed`}
            className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200 hover:-translate-y-px"
          >
            Scout Feed
          </Link>
          <Link
            href={`/labels/${id}/taste-map`}
            className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200 hover:-translate-y-px"
          >
            Taste Map
          </Link>
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
