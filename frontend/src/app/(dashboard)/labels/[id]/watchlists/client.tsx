"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, type AlertItem, type Watchlist } from "@/lib/api";

type Props = {
  labelId: string;
  initialWatchlists: Watchlist[];
  initialAlerts: AlertItem[];
};

export function WatchlistsClient({ labelId, initialWatchlists, initialAlerts }: Props) {
  const router = useRouter();
  const [watchlists, setWatchlists] = useState<Watchlist[]>(initialWatchlists);
  const [alerts, setAlerts] = useState<AlertItem[]>(initialAlerts);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [creating, setCreating] = useState(false);

  const createWatchlist = async () => {
    const trimmed = name.trim();
    if (!trimmed || creating) return;
    setCreating(true);
    try {
      const created = await api.createWatchlist(labelId, { name: trimmed, description: desc.trim() || undefined });
      setWatchlists((prev) => [...prev, created]);
      setName("");
      setDesc("");
      router.refresh();
    } finally {
      setCreating(false);
    }
  };

  const dismissAlert = async (alertId: string, status: string) => {
    try {
      await api.updateAlertStatus(labelId, alertId, status);
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
      router.refresh();
    } catch {
      // ignore
    }
  };

  const sortedAlerts = useMemo(() => {
    return [...alerts].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
  }, [alerts]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4 text-white">Watchlists</h2>

        <div className="grid gap-2 mb-4">
          <input
            className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30"
            placeholder="New watchlist name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30"
            placeholder="Description (optional)"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
          />
          <button
            className="bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-lg px-4 py-2 hover:bg-purple-500/15 transition disabled:opacity-50"
            onClick={createWatchlist}
            disabled={creating || !name.trim()}
          >
            {creating ? "Creating..." : "Create Watchlist"}
          </button>
        </div>

        <div className="grid gap-3">
          {watchlists.map((w) => (
            <Link
              key={w.id}
              href={`/labels/${labelId}/watchlists/${w.id}`}
              className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 hover:border-purple-500/20 hover:bg-white/[0.03] transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-bold text-white">{w.name}</div>
                  {w.description && <div className="text-xs text-white/35 mt-1">{w.description}</div>}
                </div>
                <div className="text-xs text-white/35">{w.item_count} artists</div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
        <h2 className="text-lg font-bold mb-4 text-white">Alerts</h2>
        {sortedAlerts.length === 0 ? (
          <div className="text-sm text-white/35">No new alerts.</div>
        ) : (
          <div className="grid gap-3">
            {sortedAlerts.map((alert) => (
              <div key={alert.id} className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-bold text-white">{alert.title}</div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    alert.severity === "high" ? "bg-red-500/10 text-red-400 border border-red-500/20" :
                    alert.severity === "medium" ? "bg-amber-500/10 text-amber-400 border border-amber-500/20" :
                    "bg-white/[0.03] text-white/35 border border-white/[0.06]"
                  }`}>
                    {alert.severity}
                  </span>
                </div>
                <div className="text-xs text-white/35 mb-2">{alert.artist_name}</div>
                {alert.description && (
                  <div className="text-xs text-white/35 mb-3">{alert.description}</div>
                )}
                <div className="flex items-center gap-2">
                  <Link
                    href={`/artists/${alert.artist_id}?label=${labelId}`}
                    className="text-xs text-purple-300/80 hover:text-purple-200"
                  >
                    View artist
                  </Link>
                  <button
                    onClick={() => dismissAlert(alert.id, "seen")}
                    className="text-xs bg-white/[0.03] border border-white/[0.06] rounded px-2 py-1 text-white/40 hover:bg-white/[0.05]"
                  >
                    Mark seen
                  </button>
                  <button
                    onClick={() => dismissAlert(alert.id, "dismissed")}
                    className="text-xs bg-white/[0.03] border border-white/[0.06] rounded px-2 py-1 text-white/40 hover:bg-white/[0.05]"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
