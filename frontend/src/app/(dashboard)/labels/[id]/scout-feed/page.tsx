import Link from "next/link";
import { api } from "@/lib/api";
import { ScoutFeedClient } from "./client";

export const dynamic = "force-dynamic";

export default async function ScoutFeedPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ limit?: string }>;
}) {
  const { id } = await params;
  const resolvedSearch = searchParams ? await searchParams : undefined;
  const limit = Math.max(1, Math.min(parseInt(resolvedSearch?.limit || "50", 10) || 50, 200));
  const [feed, label] = await Promise.all([
    api.getScoutFeed(id, limit),
    api.getLabel(id),
  ]);

  return (
    <div>
      {/* Breadcrumb + header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-muted mb-3">
          <Link href="/dashboard" className="hover:text-gray-200 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <span className="text-gray-400">{label.name}</span>
          <span>/</span>
          <span className="text-gray-200">Scout Feed</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{label.name}</h1>
            <p className="text-muted text-sm mt-1">
              Scout Feed &middot; Showing top {feed.items.length} of {feed.total} candidates
            </p>
          </div>
          <div className="flex gap-3">
            <Link href="/metrics" className="text-sm bg-surface-light text-muted px-3 py-1.5 rounded-lg hover:text-gray-200 transition-all duration-200">
              Metrics
            </Link>
            <Link href={`/labels/${id}/taste-map`} className="text-sm bg-accent/10 text-accent px-3 py-1.5 rounded-lg hover:bg-accent/20 transition-all duration-200">
              Taste Map
            </Link>
            <Link href="/dashboard" className="text-sm bg-surface-light text-muted px-3 py-1.5 rounded-lg hover:text-gray-200 transition-all duration-200">
              All Labels
            </Link>
          </div>
        </div>
        <div className="mt-3 flex items-center gap-2 text-xs text-muted">
          <span>Show:</span>
          {[20, 50, 100].map((n) => (
            <Link
              key={n}
              href={`/labels/${id}/scout-feed?limit=${n}`}
              className={`px-2 py-1 rounded ${limit === n ? "bg-primary/10 text-primary-light" : "bg-surface-light hover:text-gray-200"}`}
            >
              Top {n}
            </Link>
          ))}
        </div>
      </div>

      <ScoutFeedClient items={feed.items} labelId={id} pipelineStatus={label.pipeline_status} />
    </div>
  );
}
