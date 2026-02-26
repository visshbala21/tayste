"use client";

import { useEffect, useState } from "react";

export function ArtistWatchlistButton({ labelId, artistId }: { labelId: string; artistId: string }) {
  const [watchlistId, setWatchlistId] = useState<string | null>(null);
  const [added, setAdded] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
        const res = await fetch(`${API_BASE}/api/labels/${labelId}/watchlists`, { cache: "no-store" });
        if (!res.ok) return;
        const data = await res.json();
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
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";
      const res = await fetch(`${API_BASE}/api/labels/${labelId}/watchlists/${watchlistId}/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ artist_id: artistId }),
      });
      if (res.ok) {
        setAdded(true);
      }
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
