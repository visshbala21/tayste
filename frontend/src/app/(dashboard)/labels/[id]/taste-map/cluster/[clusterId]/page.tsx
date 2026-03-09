import Link from "next/link";
import { api } from "@/lib/api";

export default async function TasteMapClusterPage({
  params,
}: {
  params: Promise<{ id: string; clusterId: string }>;
}) {
  const { id: labelId, clusterId } = await params;
  const tasteMap = await api.getTasteMap(labelId);
  const cluster = tasteMap.clusters.find((c) => c.cluster_id === clusterId);

  if (!cluster) {
    return (
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-white/50 mb-3">
          <Link href="/dashboard" className="hover:text-white transition-colors duration-200">Labels</Link>
          <span>/</span>
          <Link href={`/labels/${labelId}/taste-map`} className="hover:text-white transition-colors duration-200">{tasteMap.label_name}</Link>
          <span>/</span>
          <span className="text-white">Cluster</span>
        </div>
        <div className="rounded-lg border border-white/10 bg-white/[0.03] p-6 text-center">
          <p className="text-white/70">Cluster not found.</p>
          <Link href={`/labels/${labelId}/taste-map`} className="mt-3 inline-block text-sm text-white/70 hover:text-white">
            ← Back to Taste Map
          </Link>
        </div>
      </div>
    );
  }

  const clusterName = cluster.cluster_name || `Cluster ${cluster.cluster_index + 1}`;
  const names = cluster.artist_names?.length
    ? cluster.artist_names
    : cluster.artist_ids.map((aid) => `${aid.slice(0, 8)}...`);

  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-white/50 mb-3">
          <Link href="/dashboard" className="hover:text-white transition-colors duration-200">Labels</Link>
          <span>/</span>
          <span className="text-white/40">{tasteMap.label_name}</span>
          <span>/</span>
          <Link href={`/labels/${labelId}/taste-map`} className="hover:text-white transition-colors duration-200">Taste Map</Link>
          <span>/</span>
          <span className="text-white">{clusterName}</span>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{
                backgroundColor: ["#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"][cluster.cluster_index % 5],
              }}
            />
            <h1 className="text-2xl font-bold text-white">{clusterName}</h1>
          </div>
          <Link
            href={`/labels/${labelId}/taste-map`}
            className="text-sm text-white/70 hover:text-white px-3 py-1.5 rounded-lg bg-white/[0.05] border border-white/10 transition-all duration-200"
          >
            ← Back to Taste Map
          </Link>
        </div>
        <p className="text-white/50 text-sm mt-1">{cluster.artist_ids.length} artists in this cluster</p>
      </div>

      <div className="rounded-lg border border-white/10 bg-white/[0.03] p-6">
        <h2 className="text-lg font-semibold text-white mb-4">Artists</h2>
        <ul className="space-y-2">
          {cluster.artist_ids.map((artistId, i) => (
            <li key={artistId}>
              <Link
                href={`/artists/${artistId}?label=${labelId}`}
                className="block text-white/80 hover:text-white hover:bg-white/[0.05] rounded-lg px-3 py-2 transition-colors duration-200"
              >
                {names[i] ?? artistId.slice(0, 8) + "..."}
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
