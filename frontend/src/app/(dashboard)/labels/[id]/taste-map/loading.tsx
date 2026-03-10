export default function TasteMapLoading() {
  return (
    <div className="page-fade animate-pulse">
      <div className="mb-6">
        <div className="h-4 w-20 rounded bg-white/[0.06] mb-3" />
        <div className="h-16 w-64 max-w-full rounded bg-white/[0.08]" />
        <div className="mt-3 h-4 w-48 rounded bg-white/[0.06]" />
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <div
            key={i}
            className="h-48 rounded-lg border border-white/[0.12] bg-white/[0.04]"
          />
        ))}
      </div>
    </div>
  );
}
