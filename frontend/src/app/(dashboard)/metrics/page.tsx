import Link from "next/link";

export const dynamic = "force-dynamic";

export default function MetricsPage() {
  return (
    <div>
      <div className="mb-6">
        <div className="flex items-center gap-2 text-xs text-white/35 mb-3">
          <Link href="/dashboard" className="hover:text-purple-300 transition-colors duration-200">Labels</Link>
          <span>/</span>
          <span className="text-white">Metrics</span>
        </div>
        <h1 className="text-2xl font-bold text-white">Scout Feed Metrics</h1>
        <p className="text-white/60 text-sm mt-1">
          How we compute Fit, Momentum, Risk, and the final ranking score.
        </p>
      </div>

      <div className="grid gap-4">
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
          <h2 className="text-lg font-bold mb-2 text-white">Fit Score</h2>
          <p className="text-white/60 text-sm">
            Measures similarity between a candidate artist and your label&apos;s roster clusters.
            We embed roster artists and candidates, cluster the roster, then compute cosine similarity
            to the nearest cluster centroid. Higher is better.
          </p>
        </div>

        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
          <h2 className="text-lg font-bold mb-2 text-white">Momentum Score</h2>
          <p className="text-white/60 text-sm">
            Captures recent growth and engagement. We compute 7d and 30d follower growth,
            view acceleration, and engagement rate from snapshots. The result is normalized
            to 0-1. If no metrics are available, we default to a neutral momentum value.
          </p>
        </div>

        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
          <h2 className="text-lg font-bold mb-2 text-white">Risk Score</h2>
          <p className="text-white/60 text-sm">
            Flags suspicious patterns such as extreme short-term growth or low engagement
            relative to followers. Higher risk reduces the final score.
          </p>
        </div>

        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
          <h2 className="text-lg font-bold mb-2 text-white">Final Score</h2>
          <p className="text-white/60 text-sm">
            We combine Fit, Momentum, and Risk with the formula:
          </p>
          <div className="mt-2 bg-white/[0.04] rounded-lg px-3 py-2 font-mono text-sm text-white/60">
            final = fit * momentum - risk
          </div>
          <p className="text-white/60 text-sm mt-2">
            When metrics are missing, we fall back to fit-only scoring and label the result
            so you know it was a fallback.
          </p>
        </div>

        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
          <h2 className="text-lg font-bold mb-2 text-white">Growth Metrics</h2>
          <p className="text-white/60 text-sm">
            We display 7d and 30d follower growth when available. These come from platform
            snapshots and are meant to indicate near-term trajectory.
          </p>
        </div>

        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
          <h2 className="text-lg font-bold mb-2 text-white">Volatility &amp; Spikes</h2>
          <p className="text-white/60 text-sm">
            Volatility measures how uneven daily growth is over the last 30 days.
            Sustained Growth shows how consistently the artist is growing day-to-day.
            Spike Ratio highlights whether a single surge dominates the 30-day trend.
          </p>
        </div>
      </div>
    </div>
  );
}
