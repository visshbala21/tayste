import Link from "next/link";
import { api, Label } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let labels: Label[] = [];
  try {
    labels = await api.getLabels();
  } catch {
    // API not available yet
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-extrabold mb-2 text-white tracking-tight">Labels</h1>
        <p className="text-white/40">Select a label to view its taste map and scout feed.</p>
        <div className="mt-4">
          <Link
            href="/import"
            className="inline-flex items-center text-sm text-purple-300 hover:text-purple-200 transition px-4 py-2 rounded-md bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/15"
          >
            + Import Roster
          </Link>
        </div>
      </div>

      {labels.length === 0 ? (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-12 text-center">
          <p className="text-white/40">No labels yet. Import a roster to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {labels.map((label) => (
            <div
              key={label.id}
              className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6 hover:border-purple-500/20 hover:bg-white/[0.03] transition-all duration-300 group"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-bold text-white group-hover:text-purple-200 transition">{label.name}</h2>
                    {label.pipeline_status === "queued" && (
                      <span className="text-[11px] bg-amber-500/10 text-amber-300/80 px-2 py-0.5 rounded-full border border-amber-500/20">
                        Queued
                      </span>
                    )}
                    {label.pipeline_status === "running" && (
                      <span className="text-[11px] bg-purple-500/10 text-purple-300/80 px-2 py-0.5 rounded-full border border-purple-500/20">
                        Running
                      </span>
                    )}
                    {label.pipeline_status === "complete" && (
                      <span className="text-[11px] bg-emerald-500/10 text-emerald-300/80 px-2 py-0.5 rounded-full border border-emerald-500/20">
                        Ready
                      </span>
                    )}
                    {!label.pipeline_status || label.pipeline_status === "idle" ? (
                      <span className="text-[11px] bg-white/[0.04] text-white/30 px-2 py-0.5 rounded-full border border-white/[0.06]">
                        Not run
                      </span>
                    ) : null}
                    {label.pipeline_status === "canceled" && (
                      <span className="text-[11px] bg-white/[0.04] text-white/30 px-2 py-0.5 rounded-full border border-white/[0.06]">
                        Canceled
                      </span>
                    )}
                    {label.pipeline_status === "error" && (
                      <span className="text-[11px] bg-red-500/10 text-red-300/80 px-2 py-0.5 rounded-full border border-red-500/20">
                        Error
                      </span>
                    )}
                  </div>
                  <p className="text-white/35 text-sm mt-1">{label.description}</p>
                  {label.genre_tags && (
                    <div className="flex gap-2 mt-3">
                      {(label.genre_tags as any).primary?.map((g: string) => (
                        <span key={g} className="text-[11px] bg-purple-500/8 text-purple-300/60 px-2.5 py-0.5 rounded-full border border-purple-500/15">{g}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  <Link
                    href={`/labels/${label.id}/taste-map`}
                    className="text-xs text-cyan-300/70 hover:text-cyan-200 transition px-3 py-1.5 rounded-md bg-cyan-500/8 border border-cyan-500/15 hover:bg-cyan-500/12"
                  >
                    Taste Map
                  </Link>
                  <Link
                    href={`/labels/${label.id}/watchlists`}
                    className="text-xs text-white/40 hover:text-white/60 transition px-3 py-1.5 rounded-md bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05]"
                  >
                    Watchlists
                  </Link>
                  <Link
                    href={`/labels/${label.id}/scout-feed`}
                    className="text-xs text-purple-300/80 hover:text-purple-200 transition px-3 py-1.5 rounded-md bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/15"
                  >
                    Scout Feed
                  </Link>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
