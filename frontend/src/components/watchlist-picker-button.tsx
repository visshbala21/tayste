"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { api, type Watchlist } from "@/lib/api";

type WatchlistPickerButtonProps = {
  labelId: string;
  artistId: string;
  watchlists?: Watchlist[];
  defaultWatchlistId?: string;
  buttonClassName?: string;
  buttonLabel?: string;
  onAdded?: (watchlistId: string) => void;
};

export function WatchlistPickerButton({
  labelId,
  artistId,
  watchlists,
  defaultWatchlistId,
  buttonClassName,
  buttonLabel = "Watch",
  onAdded,
}: WatchlistPickerButtonProps) {
  const rootRef = useRef<HTMLDivElement | null>(null);
  const [listOptions, setListOptions] = useState<Watchlist[]>(watchlists || []);
  const [selectedWatchlistId, setSelectedWatchlistId] = useState<string>(defaultWatchlistId || "");
  const [loadingLists, setLoadingLists] = useState(false);
  const [saving, setSaving] = useState(false);
  const [open, setOpen] = useState(false);
  const [added, setAdded] = useState(false);
  const [checkingAdded, setCheckingAdded] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setListOptions(watchlists || []);
  }, [watchlists]);

  useEffect(() => {
    if (!selectedWatchlistId) {
      const fallback = defaultWatchlistId || listOptions[0]?.id || "";
      if (fallback) {
        setSelectedWatchlistId(fallback);
      }
    }
  }, [defaultWatchlistId, listOptions, selectedWatchlistId]);

  useEffect(() => {
    if (watchlists && watchlists.length > 0) {
      return;
    }

    let active = true;
    const loadWatchlists = async () => {
      setLoadingLists(true);
      try {
        const data = await api.getWatchlists(labelId);
        if (!active) return;
        setListOptions(data);
        if (!selectedWatchlistId && data.length > 0) {
          setSelectedWatchlistId(defaultWatchlistId || data[0].id);
        }
      } finally {
        if (active) {
          setLoadingLists(false);
        }
      }
    };

    loadWatchlists();
    return () => {
      active = false;
    };
  }, [defaultWatchlistId, labelId, selectedWatchlistId, watchlists]);

  // Check if artist is already in any watchlist
  useEffect(() => {
    // Only run on client side
    if (typeof window === "undefined") {
      setCheckingAdded(false);
      return;
    }

    const checkIfAdded = async () => {
      const watchlistsToCheck = watchlists && watchlists.length > 0 ? watchlists : listOptions;
      if (watchlistsToCheck.length === 0) {
        setCheckingAdded(false);
        return;
      }

      try {
        // Check all watchlists to see if artist is in any of them
        for (const watchlist of watchlistsToCheck) {
          try {
            const detail = await api.getWatchlist(labelId, watchlist.id);
            if (detail.items.some((item) => item.artist_id === artistId)) {
              setAdded(true);
              setCheckingAdded(false);
              return;
            }
          } catch (e) {
            // Continue checking other watchlists
            console.error(`Failed to check watchlist ${watchlist.id}:`, e);
          }
        }
      } catch (e) {
        // If checking fails, assume not added
        console.error("Failed to check if artist is in watchlist:", e);
      } finally {
        setCheckingAdded(false);
      }
    };

    // Only check if we have watchlists and haven't already set added
    if (!added && (watchlists?.length > 0 || listOptions.length > 0)) {
      checkIfAdded();
    } else {
      setCheckingAdded(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [labelId, artistId]); // Only depend on labelId and artistId to avoid infinite loops

  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (!rootRef.current) return;
      if (rootRef.current.contains(event.target as Node)) return;
      setOpen(false);
      setError(null);
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, []);

  const selectedWatchlist = useMemo(
    () => listOptions.find((w) => w.id === selectedWatchlistId),
    [listOptions, selectedWatchlistId],
  );

  const addToWatchlist = async () => {
    if (!selectedWatchlistId || saving) return;
    setSaving(true);
    setError(null);
    try {
      await api.addToWatchlist(labelId, selectedWatchlistId, { artist_id: artistId });
      setAdded(true);
      setOpen(false);
      onAdded?.(selectedWatchlistId);
    } catch {
      setError("Could not add to watchlist.");
    } finally {
      setSaving(false);
    }
  };

  if (added) {
    return <span className="text-xs text-accent px-3 py-1">Watching</span>;
  }

  if (checkingAdded || (loadingLists && listOptions.length === 0)) {
    return (
      <button
        type="button"
        disabled
        className={buttonClassName || "text-xs bg-surface-light text-muted px-3 py-1 rounded"}
      >
        Loading...
      </button>
    );
  }

  if (listOptions.length === 0) {
    return (
      <Link
        href={`/labels/${labelId}/watchlists`}
        className="text-xs bg-surface-light text-muted px-3 py-1 rounded hover:bg-border transition-all duration-200"
      >
        Create Watchlist
      </Link>
    );
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={
          buttonClassName ||
          "text-xs bg-accent/10 text-accent px-3 py-1 rounded hover:bg-accent/20 transition-all duration-200"
        }
      >
        {buttonLabel}
      </button>

      {open && (
        <div className="absolute right-0 z-20 mt-2 w-64 rounded-lg border border-border bg-surface p-3 shadow-xl">
          <p className="mb-2 text-xs text-muted">Add to watchlist</p>
          <select
            value={selectedWatchlistId}
            onChange={(e) => setSelectedWatchlistId(e.target.value)}
            className="w-full rounded border border-border bg-surface-light px-2 py-1.5 text-xs text-gray-200"
          >
            {listOptions.map((watchlist) => (
              <option key={watchlist.id} value={watchlist.id}>
                {watchlist.name}
              </option>
            ))}
          </select>

          {selectedWatchlist && (
            <p className="mt-1 text-[11px] text-muted">
              {selectedWatchlist.item_count} artists
            </p>
          )}

          {error && <p className="mt-2 text-xs text-danger">{error}</p>}

          <div className="mt-3 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-xs bg-surface-light text-muted px-2.5 py-1 rounded hover:bg-border transition-all duration-200"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={addToWatchlist}
              disabled={!selectedWatchlistId || saving}
              className="text-xs bg-accent/10 text-accent px-2.5 py-1 rounded hover:bg-accent/20 transition-all duration-200 disabled:opacity-60"
            >
              {saving ? "Adding..." : "Add"}
            </button>
          </div>

          <Link
            href={`/labels/${labelId}/watchlists`}
            className="mt-3 block text-[11px] text-muted hover:text-gray-300 transition-colors"
          >
            Manage watchlists
          </Link>
        </div>
      )}
    </div>
  );
}
