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
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

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

  const toggleExpand = (id: string) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const sortedAlerts = useMemo(() => {
    return [...alerts].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
  }, [alerts]);

  const totalArtists = watchlists.reduce((sum, w) => sum + (w.item_count || 0), 0);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Watchlists panel */}
      <div className="bg-surface border border-white/[0.12] rounded-lg p-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />

        <div className="flex items-center justify-between mb-4">
          <h2 className="font-display text-[22px] tracking-wide text-[#f5f5f0]">Watchlists</h2>
          <div className="flex gap-3 text-xs text-white/40">
            <span>{watchlists.length} lists</span>
            <span>{totalArtists} artists</span>
          </div>
        </div>

        {/* Create form */}
        <div className="grid gap-2 mb-4">
          <input
            className="inp"
            placeholder="New watchlist name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="inp"
            placeholder="Description (optional)"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
          />
          <button
            className="inline-flex items-center justify-center rounded-pill px-5 py-2 text-xs bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200 hover:-translate-y-px disabled:opacity-50"
            onClick={createWatchlist}
            disabled={creating || !name.trim()}
          >
            {creating ? "Creating..." : "+ New List"}
          </button>
        </div>

        {/* Watchlist list */}
        <div className="grid gap-3">
          {watchlists.map((w) => (
            <div key={w.id} className="bg-white/[0.03] border border-white/[0.12] rounded-lg overflow-hidden">
              <button
                onClick={() => toggleExpand(w.id)}
                className="w-full p-4 flex items-center justify-between hover:bg-white/[0.02] transition-colors text-left"
              >
                <div>
                  <div className="font-display text-[18px] tracking-wide text-[#f5f5f0]">{w.name}</div>
                  {w.description && <div className="text-xs text-white/35 mt-1">{w.description}</div>}
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-xs text-white/35">{w.item_count} artists</span>
                  <span className="text-white/40 text-sm">{expandedIds.has(w.id) ? "▾" : "▸"}</span>
                </div>
              </button>
              {expandedIds.has(w.id) && (
                <div className="border-t border-white/[0.06] p-3">
                  <Link
                    href={`/labels/${labelId}/watchlists/${w.id}`}
                    className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200 hover:-translate-y-px"
                  >
                    View &rarr;
                  </Link>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Alerts panel */}
      <div className="bg-surface border border-white/[0.12] rounded-lg p-6 relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
        <h2 className="font-display text-[22px] tracking-wide mb-4 text-[#f5f5f0]">Alerts</h2>
        {sortedAlerts.length === 0 ? (
          <div className="text-sm text-white/35">No new alerts.</div>
        ) : (
          <div className="grid gap-3">
            {sortedAlerts.map((alert) => (
              <div key={alert.id} className="bg-white/[0.04] border border-white/[0.12] rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-bold text-white">{alert.title}</div>
                  <span className={`text-xs px-2 py-0.5 rounded-pill ${
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
                    className="inline-flex items-center rounded-pill px-3 py-1 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200"
                  >
                    View artist
                  </Link>
                  <button
                    onClick={() => dismissAlert(alert.id, "seen")}
                    className="inline-flex items-center rounded-pill px-3 py-1 text-xs bg-white/[0.03] border border-white/[0.12] text-white/40 hover:bg-white/[0.05] transition-all duration-200"
                  >
                    Mark seen
                  </button>
                  <button
                    onClick={() => dismissAlert(alert.id, "dismissed")}
                    className="inline-flex items-center rounded-pill px-3 py-1 text-xs bg-white/[0.03] border border-white/[0.12] text-white/40 hover:bg-white/[0.05] transition-all duration-200"
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
