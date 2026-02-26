"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import type { AlertItem, Watchlist } from "@/lib/api";

type Props = {
  labelId: string;
  initialWatchlists: Watchlist[];
  initialAlerts: AlertItem[];
};

export function WatchlistsClient({ labelId, initialWatchlists, initialAlerts }: Props) {
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
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const res = await fetch(`${API_BASE}/api/labels/${labelId}/watchlists`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: trimmed, description: desc.trim() || undefined }),
      });
      if (res.ok) {
        const created = await res.json();
        setWatchlists((prev) => [...prev, created]);
        setName("");
        setDesc("");
      }
    } finally {
      setCreating(false);
    }
  };

  const updateAlertStatus = async (alertId: string, status: string) => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    const res = await fetch(`${API_BASE}/api/labels/${labelId}/alerts/${alertId}/status`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status }),
    });
    if (res.ok) {
      setAlerts((prev) => prev.filter((a) => a.id !== alertId));
    }
  };

  const sortedAlerts = useMemo(() => {
    return [...alerts].sort((a, b) => (a.created_at < b.created_at ? 1 : -1));
  }, [alerts]);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-surface border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Watchlists</h2>

        <div className="grid gap-2 mb-4">
          <input
            className="bg-surface-light border border-border rounded px-3 py-2"
            placeholder="New watchlist name"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
          <input
            className="bg-surface-light border border-border rounded px-3 py-2"
            placeholder="Description (optional)"
            value={desc}
            onChange={(e) => setDesc(e.target.value)}
          />
          <button
            className="bg-primary text-white rounded px-4 py-2 disabled:opacity-50"
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
              className="bg-surface-light border border-border rounded-lg p-4 hover:border-primary/50 transition"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-semibold">{w.name}</div>
                  {w.description && <div className="text-xs text-muted mt-1">{w.description}</div>}
                </div>
                <div className="text-xs text-muted">{w.item_count} artists</div>
              </div>
            </Link>
          ))}
        </div>
      </div>

      <div className="bg-surface border border-border rounded-lg p-6">
        <h2 className="text-lg font-semibold mb-4">Alerts</h2>
        {sortedAlerts.length === 0 ? (
          <div className="text-sm text-muted">No new alerts.</div>
        ) : (
          <div className="grid gap-3">
            {sortedAlerts.map((alert) => (
              <div key={alert.id} className="bg-surface-light border border-border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="text-sm font-semibold">{alert.title}</div>
                  <span className={`text-xs px-2 py-0.5 rounded ${
                    alert.severity === "high" ? "bg-danger/10 text-danger" :
                    alert.severity === "medium" ? "bg-accent/10 text-accent" :
                    "bg-surface-light text-muted"
                  }`}>
                    {alert.severity}
                  </span>
                </div>
                <div className="text-xs text-muted mb-2">{alert.artist_name}</div>
                {alert.description && (
                  <div className="text-xs text-gray-400 mb-3">{alert.description}</div>
                )}
                <div className="flex items-center gap-2">
                  <Link
                    href={`/artists/${alert.artist_id}?label=${labelId}`}
                    className="text-xs text-primary hover:text-primary-light"
                  >
                    View artist
                  </Link>
                  <button
                    onClick={() => updateAlertStatus(alert.id, "seen")}
                    className="text-xs bg-surface border border-border rounded px-2 py-1 hover:bg-surface-light"
                  >
                    Mark seen
                  </button>
                  <button
                    onClick={() => updateAlertStatus(alert.id, "dismissed")}
                    className="text-xs bg-surface border border-border rounded px-2 py-1 hover:bg-surface-light"
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
