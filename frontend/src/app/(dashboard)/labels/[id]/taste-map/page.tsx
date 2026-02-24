import Link from "next/link";
import { api } from "@/lib/api";

export const dynamic = "force-dynamic";

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
        <div className="flex items-center gap-2 text-xs text-muted mb-3">
          <Link href="/dashboard" className="hover:text-gray-200 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <span className="text-gray-400">{tasteMap.label_name}</span>
          <span>/</span>
          <span className="text-gray-200">Taste Map</span>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">{tasteMap.label_name}</h1>
            <p className="text-muted text-sm mt-1">Taste Map &amp; Label DNA</p>
          </div>
          <div className="flex gap-3">
            <Link href={`/labels/${id}/scout-feed`} className="text-sm bg-primary/10 text-primary px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-all duration-200">
              Scout Feed
            </Link>
            <Link href="/dashboard" className="text-sm bg-surface-light text-muted px-3 py-1.5 rounded-lg hover:text-gray-200 transition-all duration-200">
              All Labels
            </Link>
          </div>
        </div>
      </div>

      {/* Label Thesis */}
      {thesis.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-3 text-primary">Label Thesis</h2>
          <ul className="space-y-2">
            {thesis.map((bullet: string, i: number) => (
              <li key={i} className="text-gray-300 flex gap-2">
                <span className="text-primary">&#8226;</span>
                {bullet}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Clusters */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
        {tasteMap.clusters.map((cluster) => (
          <div key={cluster.cluster_id} className="bg-surface border border-border rounded-lg p-5">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-3 h-3 rounded-full" style={{
                backgroundColor: ["#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"][cluster.cluster_index % 5]
              }} />
              <h3 className="font-semibold">{cluster.cluster_name || `Cluster ${cluster.cluster_index + 1}`}</h3>
            </div>
            <p className="text-muted text-sm mb-2">{cluster.artist_ids.length} artists</p>
            <div className="flex flex-wrap gap-1">
              {cluster.artist_ids.slice(0, 5).map((aid) => (
                <span key={aid} className="text-xs bg-surface-light px-2 py-0.5 rounded text-gray-400">
                  {aid.slice(0, 8)}...
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Discovery Seeds */}
      {searchQueries.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-3 text-accent">Discovery Seed Queries</h2>
          <div className="flex flex-wrap gap-2">
            {searchQueries.map((q: string, i: number) => (
              <span key={i} className="text-sm bg-accent/10 text-accent-light px-3 py-1 rounded">{q}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
