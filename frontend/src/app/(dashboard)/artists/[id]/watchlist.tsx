"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export function ArtistWatchlistButton({ labelId, artistId }: { labelId: string; artistId: string }) {
  const router = useRouter();
  const [watchlistId, setWatchlistId] = useState<string | null>(null);
  const [added, setAdded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const watchlists = await api.getWatchlists(labelId);
        if (watchlists && watchlists.length > 0) {
          const defaultWatchlistId = watchlists[0].id;
          setWatchlistId(defaultWatchlistId);
          
          // Check if artist is already in the watchlist
          try {
            const watchlistDetail = await api.getWatchlist(labelId, defaultWatchlistId);
            const isInWatchlist = watchlistDetail.items.some(item => item.artist_id === artistId);
            setAdded(isInWatchlist);
          } catch {
            // If we can't check, assume not added
            setAdded(false);
          }
        }
      } catch {
        // ignore
      } finally {
        setChecking(false);
      }
    };
    load();
  }, [labelId, artistId]);

  const add = async () => {
    if (!watchlistId || loading) return;
    setLoading(true);
    try {
      await api.addToWatchlist(labelId, watchlistId, { artist_id: artistId });
      setAdded(true);
      router.refresh();
    } finally {
      setLoading(false);
    }
  };

  if (!watchlistId || checking) return null;

  return (
    <button
      onClick={add}
      disabled={loading || added}
      className="text-xs bg-accent/10 text-accent px-3 py-1.5 rounded-lg hover:bg-accent/20 transition-all duration-200 disabled:opacity-60"
    >
      {added ? "Watching" : "Watch"}
    </button>
  );
}
