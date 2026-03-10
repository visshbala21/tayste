export default function DashboardHomeLoading() {
  return (
    <div className="page-fade animate-pulse">
      <div className="border-b border-dashed border-white/[0.12] pb-6 mb-0">
        <div className="h-4 w-24 rounded bg-white/[0.06] mb-2" />
        <div className="h-20 w-72 max-w-full rounded bg-white/[0.08]" />
        <div className="mt-2 h-4 w-48 rounded bg-white/[0.06]" />
      </div>
      <div className="grid grid-cols-4 gap-px border-b border-white/[0.12] mt-0">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="p-3 text-center bg-white/[0.03] border-r border-white/[0.12] last:border-r-0">
            <div className="h-8 w-12 mx-auto rounded bg-white/[0.08]" />
            <div className="h-3 w-16 mx-auto mt-2 rounded bg-white/[0.06]" />
          </div>
        ))}
      </div>
      <div className="mt-6 space-y-4">
        <div className="h-6 w-32 rounded bg-white/[0.08]" />
        {Array.from({ length: 2 }).map((_, i) => (
          <div
            key={i}
            className="h-32 rounded-lg border border-white/[0.12] bg-white/[0.04]"
          />
        ))}
      </div>
    </div>
  );
}
