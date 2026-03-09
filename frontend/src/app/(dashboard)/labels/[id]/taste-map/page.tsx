import Link from "next/link";
import { api } from "@/lib/api";
import { PipelinePoller } from "@/components/pipeline-poller";

export default async function TasteMapPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const [tasteMap, label] = await Promise.all([
    api.getTasteMap(id),
    api.getLabel(id),
  ]);

  const dna = label.label_dna || {};
  const thesis = (dna as any).label_thesis_bullets || [];
  const searchQueries = (dna as any).search_seed_queries || [];

  return (
    <div className="page-fade">
      <PipelinePoller status={label.pipeline_status} />

      {/* Header */}
      <div className="mb-6">
        <Link
          href="/dashboard"
          className="text-xs text-white/35 hover:text-primary-light transition-colors inline-flex items-center gap-1 mb-3"
        >
          &larr; Back to Home
        </Link>
        <h1 className="font-display text-[clamp(36px,8vw,72px)] leading-none tracking-wide text-[#f5f5f0]">
          TASTE MAP
        </h1>
        <p className="text-white/45 mt-2 italic text-sm">
          {tasteMap.label_name} &middot; Label DNA &amp; Clusters
        </p>

        <div className="flex gap-2 mt-4">
          <Link
            href={`/labels/${id}/scout-feed`}
            className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200 hover:-translate-y-px"
          >
            Scout Feed
          </Link>
          <Link
            href={`/labels/${id}/watchlists`}
            className="inline-flex items-center rounded-pill px-4 py-1.5 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200 hover:-translate-y-px"
          >
            Collections
          </Link>
        </div>
      </div>

      {/* Label Thesis */}
      {thesis.length > 0 && (
        <div className="bg-surface border border-white/[0.12] rounded-lg p-6 mb-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
          <h2 className="font-display text-[22px] tracking-wide mb-3 text-[#f5f5f0]">Label Thesis</h2>
          <ul className="space-y-2">
            {thesis.map((bullet: string, i: number) => (
              <li key={i} className="text-white/60 flex gap-2">
                <span className="text-white/35">&#8226;</span>
                {bullet}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Clusters */}
      <div className="mb-6">
        <h2 className="font-display text-[22px] tracking-wide py-3.5 border-b border-dashed border-white/[0.12] text-[#f5f5f0] mb-4">
          Taste Clusters
        </h2>
        {tasteMap.clusters.length === 0 ? (
          <div className="bg-surface border border-white/[0.12] rounded-lg p-8 text-center relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
            <p className="text-white/60">No clusters yet. Import a roster and run the pipeline to generate taste clusters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tasteMap.clusters.map((cluster) => (
              <Link
                key={cluster.cluster_id}
                href={`/labels/${id}/taste-map/cluster/${cluster.cluster_id}`}
                className="block bg-surface border border-white/[0.12] rounded-lg p-5 relative overflow-hidden hover:border-primary/40 transition-all duration-200 cursor-pointer"
              >
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-3 h-3 rounded-full" style={{
                    backgroundColor: ["#7c5cfc", "#c45cfc", "#10b981", "#f59e0b", "#ef4444"][cluster.cluster_index % 5]
                  }} />
                  <h3 className="font-display text-[18px] tracking-wide text-[#f5f5f0]">
                    {cluster.cluster_name || `Cluster ${cluster.cluster_index + 1}`}
                  </h3>
                </div>
                <p className="text-white/60 text-sm mb-2">{cluster.artist_ids.length} artists</p>
                <div className="flex flex-wrap gap-1">
                  {(() => {
                    const names = cluster.artist_names && cluster.artist_names.length > 0
                      ? cluster.artist_names
                      : cluster.artist_ids.map((aid) => `${aid.slice(0, 8)}...`);
                    const preview = names.slice(0, 6);
                    const extra = names.length - preview.length;
                    return (
                      <>
                        {preview.map((name, i) => (
                          <span key={`${name}-${i}`} className="tag text-[9px]">
                            {name}
                          </span>
                        ))}
                        {extra > 0 && (
                          <span className="text-xs text-white/35 px-2 py-0.5">+{extra} more</span>
                        )}
                      </>
                    );
                  })()}
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Discovery Seeds */}
      {searchQueries.length > 0 && (
        <div className="bg-surface border border-white/[0.12] rounded-lg p-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
          <h2 className="font-display text-[22px] tracking-wide mb-3 text-[#f5f5f0]">Discovery Seed Queries</h2>
          <div className="flex flex-wrap gap-2">
            {searchQueries.map((q: string, i: number) => (
              <span
                key={i}
                className="inline-flex items-center rounded-pill px-4 py-1.5 text-sm bg-transparent border border-primary text-primary cursor-default"
              >
                {q}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
