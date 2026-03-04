"use client";

import { WatchlistPickerButton } from "@/components/watchlist-picker-button";

export function ArtistWatchlistButton({ labelId, artistId }: { labelId: string; artistId: string }) {
  return (
    <WatchlistPickerButton
      labelId={labelId}
      artistId={artistId}
      buttonClassName="text-xs bg-accent/10 text-accent px-3 py-1.5 rounded-lg hover:bg-accent/20 transition-all duration-200"
      buttonLabel="Watch"
    />
  );
}
