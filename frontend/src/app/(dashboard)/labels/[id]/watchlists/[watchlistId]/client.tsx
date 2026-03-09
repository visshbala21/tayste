"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, type WatchlistDetail, type WatchlistItem } from "@/lib/api";

export function WatchlistDetailClient({ labelId, detail }: { labelId: string; detail: WatchlistDetail }) {
  const router = useRouter();
  const [items, setItems] = useState<WatchlistItem[]>(detail.items);

  const remove = async (artistId: string) => {
    try {
      await api.removeFromWatchlist(labelId, detail.watchlist.id, artistId);
      setItems((prev) => prev.filter((i) => i.artist_id !== artistId));
      router.refresh();
    } catch {
      // ignore
    }
  };

  if (items.length === 0) {
    return (
      <div className="bg-surface border border-white/[0.12] rounded-lg p-12 text-center relative overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
        <p className="text-white/60">No artists in this watchlist yet.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div
          key={item.artist_id}
          className="bg-surface border border-white/[0.12] rounded-lg p-5 relative overflow-hidden hover:border-primary/40 transition-all duration-200"
        >
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {item.image_url ? (
                <div className="w-10 h-10 rounded-full overflow-hidden border border-white/[0.12] flex-shrink-0">
                  <img src={item.image_url} alt={item.artist_name} className="w-full h-full object-cover" />
                </div>
              ) : (
                <div className="vinyl flex-shrink-0" style={{ width: 40, height: 40 }}>
                  <div className="rounded-full bg-[#0a0a0a] border border-white/[0.12] absolute" style={{ width: 8, height: 8 }} />
                </div>
              )}
              <div>
                <Link
                  href={`/artists/${item.artist_id}?label=${labelId}`}
                  className="font-display text-[16px] tracking-wide text-[#f5f5f0] hover:text-primary-light transition-colors"
                >
                  {item.artist_name}
                </Link>
                <div className="text-xs text-white/35 mt-1">
                  Added {new Date(item.added_at).toLocaleDateString()}
                  {item.stage && <span className="ml-2 tag text-[9px]">{item.stage}</span>}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Link
                href={`/artists/${item.artist_id}?label=${labelId}`}
                className="inline-flex items-center rounded-pill px-3 py-1 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200"
              >
                View &rarr;
              </Link>
              <button
                onClick={() => remove(item.artist_id)}
                className="inline-flex items-center rounded-pill px-3 py-1 text-xs bg-white/[0.03] border border-white/[0.12] text-white/40 hover:bg-white/[0.05] transition-all duration-200"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
