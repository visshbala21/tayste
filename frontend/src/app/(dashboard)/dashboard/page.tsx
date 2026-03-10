import Link from "next/link";
import { api, Label, BatchInfo } from "@/lib/api";
import { PipelinePoller } from "@/components/pipeline-poller";
import { LabelCards } from "@/components/label-cards";
import { createClient } from "@/lib/supabase/server";

export default async function DashboardPage() {
  const supabase = await createClient();
  const { data: { session } } = await supabase.auth.getSession();
  const user = session?.user;
  const displayName = user?.user_metadata?.name || user?.user_metadata?.full_name || "there";

  let labels: Label[] = [];
  try {
    labels = await api.getLabels();
  } catch {
    // API not available yet
  }

  // Fetch latest batch info for each label (in parallel)
  const labelBatches: Record<string, BatchInfo | null> = {};
  if (labels.length > 0) {
    const batchResults = await Promise.all(
      labels.map((l) => api.getBatches(l.id).catch(() => []))
    );
    labels.forEach((l, i) => {
      labelBatches[l.id] = batchResults[i]?.[0] || null;
    });
  }

  const anyActive = labels.some(
    (l) => l.pipeline_status === "queued" || l.pipeline_status === "running"
  );

  const activeLabel = labels[0] || null;

  // Fetch scout feed top 6 for active label
  let topCandidates: any[] = [];
  let watchlistCount = 0;
  let savedArtistCount = 0;
  if (activeLabel) {
    try {
      const [feed, watchlists] = await Promise.all([
        api.getScoutFeed(activeLabel.id, 6),
        api.getWatchlists(activeLabel.id),
      ]);
      topCandidates = feed.items.slice(0, 6);
      watchlistCount = watchlists.length;
      savedArtistCount = watchlists.reduce((sum, w) => sum + (w.item_count || 0), 0);
    } catch {
      // ignore
    }
  }

  return (
    <div className="page-fade">
      <PipelinePoller status={anyActive ? "running" : undefined} />

      {/* Hero greeting */}
      <div className="border-b border-dashed border-white/[0.12] pb-6 mb-0">
        <div className="flex items-start justify-between flex-wrap gap-5">
          <div>
            <div className="text-[11px] text-white/35 tracking-[2px] uppercase mb-2">
              Welcome back,
            </div>
            <h1 className="font-display text-[clamp(48px,12vw,96px)] leading-none text-[#f5f5f0]">
              {displayName.toUpperCase()}
            </h1>
            <div className="text-white/45 mt-2 italic text-sm">
              A&R Intelligence Dashboard
            </div>
          </div>
          <div className="flex flex-col gap-3 min-w-[180px]">
            <Link
              href="/import"
              className="inline-flex items-center gap-2 rounded-pill px-5 py-2 text-xs bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200 hover:-translate-y-px"
            >
              + New Import
            </Link>
            {activeLabel && (
              <Link
                href={`/labels/${activeLabel.id}/taste-map`}
                className="inline-flex items-center gap-2 rounded-pill px-5 py-2 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200 hover:-translate-y-px"
              >
                View Taste Map
              </Link>
            )}
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-4 gap-px border-b border-white/[0.12]">
        {[
          [String(savedArtistCount), "Saved Artists"],
          [String(watchlistCount), "Active Lists"],
          [String(labels.length), "Labels"],
          [anyActive ? "Running" : activeLabel?.pipeline_status === "complete" ? "Ready" : "Idle", "Pipeline Status"],
        ].map(([value, label]) => (
          <div key={label} className="p-3 text-center bg-white/[0.03] border-r border-white/[0.12] last:border-r-0">
            <div className="font-display text-[32px] leading-none text-primary">{value}</div>
            <div className="text-[10px] text-white/40 tracking-wider uppercase mt-1">{label}</div>
          </div>
        ))}
      </div>

      {/* Labels section */}
      <div className="mt-6">
        <h2 className="font-display text-[22px] tracking-wide py-3.5 border-b border-dashed border-white/[0.12] text-[#f5f5f0] mb-4">
          Your Labels
        </h2>

        {labels.length === 0 ? (
          <div className="bg-surface border border-white/[0.12] rounded-lg p-12 text-center relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
            <p className="text-white/40">No labels yet. Import a roster to get started.</p>
          </div>
        ) : (
          <LabelCards labels={labels} labelBatches={labelBatches} />
        )}
      </div>

      {/* Top Candidates row */}
      {topCandidates.length > 0 && (
        <div className="mt-8">
          <h2 className="font-display text-[22px] tracking-wide py-3.5 border-b border-dashed border-white/[0.12] text-[#f5f5f0] mb-4">
            Top Candidates
          </h2>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {topCandidates.map((item: any) => (
              <Link
                key={item.artist_id}
                href={`/artists/${item.artist_id}?label=${activeLabel!.id}`}
                className="min-w-[180px] bg-surface border border-white/[0.12] rounded-lg overflow-hidden hover:border-primary/40 transition-all duration-200 hover:-translate-y-0.5 flex-shrink-0 relative group"
              >
                {/* Gradient header area */}
                <div className="h-[80px] bg-gradient-to-br from-[#2a1a4a] to-[#1a2a4a] relative flex items-center justify-center">
                  <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
                  {/* Vinyl avatar */}
                  <div className="vinyl" style={{ width: 50, height: 50 }}>
                    <div className="rounded-full bg-[#0a0a0a] border-2 border-white/[0.12] absolute" style={{ width: 10, height: 10 }} />
                  </div>
                  {/* Match score badge */}
                  <span className="absolute top-2 right-2 bg-primary text-[#f5f5f0] text-[11px] font-display px-2.5 py-0.5 rounded-full tracking-wide">
                    {(item.final_score * 100).toFixed(0)}
                  </span>
                </div>
                <div className="p-3">
                  <div className="font-display text-[18px] tracking-wide text-[#f5f5f0] truncate">
                    {item.artist_name}
                  </div>
                  {item.genre_tags && item.genre_tags.length > 0 && (
                    <div className="text-[10px] text-white/35 mt-1 truncate">
                      {item.genre_tags.slice(0, 2).join(" / ")}
                    </div>
                  )}
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

