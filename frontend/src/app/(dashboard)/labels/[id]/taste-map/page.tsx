import Link from "next/link";
import { api } from "@/lib/api";

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
    <div>
      {/* Breadcrumb + header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-white/35 mb-3">
          <Link href="/dashboard" className="hover:text-purple-300 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <span className="text-white/35">{tasteMap.label_name}</span>
          <span>/</span>
          <span className="text-white">Taste Map</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-white">{tasteMap.label_name}</h1>
            <p className="text-white/60 text-sm mt-1">Taste Map &amp; Label DNA</p>
          </div>
          <div className="flex gap-3">
            <Link href={`/labels/${id}/scout-feed`} className="text-sm text-purple-300/80 hover:text-purple-200 px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 transition-all duration-200">
              Scout Feed
            </Link>
            <Link href={`/labels/${id}/watchlists`} className="text-sm text-white/40 hover:text-white/60 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-all duration-200">
              Watchlists
            </Link>
            <Link href="/dashboard" className="text-sm text-white/40 hover:text-white/60 px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05] transition-all duration-200">
              All Labels
            </Link>
          </div>
        </div>
      </div>

      {/* Label Thesis */}
      {thesis.length > 0 && (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6 mb-6">
          <h2 className="text-lg font-bold mb-3 text-white">Label Thesis</h2>
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
        <h2 className="text-lg font-bold text-white mb-3">Taste clusters</h2>
        {tasteMap.clusters.length === 0 ? (
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-8 text-center">
            <p className="text-white/60">No clusters yet. Import a roster and run the pipeline to generate taste clusters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {tasteMap.clusters.map((cluster) => (
              <Link
                key={cluster.cluster_id}
                href={`/labels/${id}/taste-map/cluster/${cluster.cluster_id}`}
                className="block bg-white/[0.02] border border-white/[0.06] rounded-xl p-5 hover:border-purple-500/20 hover:bg-white/[0.03] transition-all duration-200 cursor-pointer"
              >
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-3 h-3 rounded-full" style={{
                    backgroundColor: ["#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"][cluster.cluster_index % 5]
                  }} />
                  <h3 className="font-bold text-white">{cluster.cluster_name || `Cluster ${cluster.cluster_index + 1}`}</h3>
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
                          <span key={`${name}-${i}`} className="text-xs bg-white/[0.03] px-2 py-0.5 rounded border border-white/[0.06] text-white/35">
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
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
          <h2 className="text-lg font-bold mb-3 text-white">Discovery Seed Queries</h2>
          <div className="flex flex-wrap gap-2">
            {searchQueries.map((q: string, i: number) => (
              <span key={i} className="text-sm bg-cyan-500/[0.08] text-cyan-300/70 px-3 py-1 rounded border border-cyan-500/15">{q}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
