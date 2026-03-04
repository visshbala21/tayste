"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";

export function ArtistWatchlistButton({ labelId, artistId }: { labelId: string; artistId: string }) {
  const router = useRouter();
  const [watchlistId, setWatchlistId] = useState<string | null>(null);
  const [added, setAdded] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await api.getWatchlists(labelId);
        if (data && data.length > 0) {
          setWatchlistId(data[0].id);
        }
      } catch {
        // ignore
      }
    };
    load();
  }, [labelId]);

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

  if (!watchlistId) return null;

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
