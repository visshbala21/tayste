"use client";

import { useState } from "react";
import Link from "next/link";
import type { WatchlistDetail, WatchlistItem } from "@/lib/api";

export function WatchlistDetailClient({ labelId, detail }: { labelId: string; detail: WatchlistDetail }) {
  const [items, setItems] = useState<WatchlistItem[]>(detail.items);

  const remove = async (artistId: string) => {
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
    const res = await fetch(
      `${API_BASE}/api/labels/${labelId}/watchlists/${detail.watchlist.id}/items/${artistId}`,
      { method: "DELETE" }
    );
    if (res.ok) {
      setItems((prev) => prev.filter((i) => i.artist_id !== artistId));
    }
  };

  if (items.length === 0) {
    return (
      <div className="bg-surface border border-border rounded-lg p-12 text-center">
        <p className="text-muted">No artists in this watchlist yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.artist_id} className="bg-surface border border-border rounded-lg p-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {item.image_url && (
                <img src={item.image_url} alt={item.artist_name} className="w-10 h-10 rounded object-cover" />
              )}
              <div>
                <Link
                  href={`/artists/${item.artist_id}?label=${labelId}`}
                  className="font-semibold hover:text-primary transition-colors"
                >
                  {item.artist_name}
                </Link>
                <div className="text-xs text-muted mt-1">
                  Added {new Date(item.added_at).toLocaleDateString()}
                  {item.stage && <span className="ml-2 px-2 py-0.5 bg-surface-light rounded">{item.stage}</span>}
                </div>
              </div>
            </div>
            <button
              onClick={() => remove(item.artist_id)}
              className="text-xs bg-surface-light text-muted px-3 py-1 rounded hover:bg-border transition-all duration-200"
            >
              Remove
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
