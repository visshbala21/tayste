export default function DashboardLoading() {
  return (
    <div className="page-fade animate-pulse">
      <div className="mb-6">
        <div className="h-16 w-64 max-w-full rounded bg-white/[0.08]" />
        <div className="mt-3 h-4 w-80 max-w-full rounded bg-white/[0.06]" />
      </div>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="h-40 rounded-lg border border-white/[0.12] bg-white/[0.04]" />
        <div className="h-40 rounded-lg border border-white/[0.12] bg-white/[0.04]" />
      </div>
    </div>
  );
}
