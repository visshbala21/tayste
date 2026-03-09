"use client";

import { WatchlistPickerButton } from "@/components/watchlist-picker-button";

export function ArtistWatchlistButton({ labelId, artistId }: { labelId: string; artistId: string }) {
  return (
    <WatchlistPickerButton
      labelId={labelId}
      artistId={artistId}
      buttonClassName="text-xs bg-white/[0.03] text-white/40 px-3 py-1.5 rounded-lg border border-white/[0.06] hover:bg-white/[0.05] transition-all duration-200"
      buttonLabel="Watch"
    />
  );
}
