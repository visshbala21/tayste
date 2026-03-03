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
        <h1 className="text-3xl font-bold mb-2">Labels</h1>
        <p className="text-muted">Select a label to view its taste map and scout feed.</p>
        <div className="mt-4">
          <Link
            href="/import"
            className="inline-flex items-center text-sm text-primary hover:text-primary-light transition px-3 py-1.5 rounded bg-primary/10"
          >
            Import Roster
          </Link>
        </div>
      </div>

      {labels.length === 0 ? (
        <div className="bg-surface border border-border rounded-lg p-12 text-center">
          <p className="text-muted">No labels yet. Import a roster to get started.</p>
        </div>
      ) : (
        <div className="grid gap-4">
          {labels.map((label) => (
            <div
              key={label.id}
              className="bg-surface border border-border rounded-lg p-6 hover:border-primary/50 transition group"
            >
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center gap-3">
                    <h2 className="text-xl font-semibold group-hover:text-primary transition">{label.name}</h2>
                    {label.pipeline_status === "queued" && (
                      <span className="text-xs bg-surface-light text-muted px-2 py-0.5 rounded">
                        Queued
                      </span>
                    )}
                    {label.pipeline_status === "running" && (
                      <span className="text-xs bg-accent/10 text-accent-light px-2 py-0.5 rounded">
                        Pipeline running
                      </span>
                    )}
                    {label.pipeline_status === "complete" && (
                      <span className="text-xs bg-primary/10 text-primary-light px-2 py-0.5 rounded">
                        Ready
                      </span>
                    )}
                    {!label.pipeline_status || label.pipeline_status === "idle" ? (
                      <span className="text-xs bg-surface-light text-muted px-2 py-0.5 rounded">
                        Not run
                      </span>
                    ) : null}
                    {label.pipeline_status === "canceled" && (
                      <span className="text-xs bg-surface-light text-muted px-2 py-0.5 rounded">
                        Canceled
                      </span>
                    )}
                    {label.pipeline_status === "error" && (
                      <span className="text-xs bg-red-500/10 text-red-300 px-2 py-0.5 rounded">
                        Error
                      </span>
                    )}
                  </div>
                  <p className="text-muted text-sm mt-1">{label.description}</p>
                  {label.genre_tags && (
                    <div className="flex gap-2 mt-3">
                      {(label.genre_tags as any).primary?.map((g: string) => (
                        <span key={g} className="text-xs bg-primary/10 text-primary-light px-2 py-0.5 rounded">{g}</span>
                      ))}
                    </div>
                  )}
                </div>
                <div className="flex gap-3">
                  <Link
                    href={`/labels/${label.id}/taste-map`}
                    className="text-sm text-accent hover:text-accent-light transition px-3 py-1.5 rounded bg-accent/10"
                  >
                    Taste Map
                  </Link>
                  <Link
                    href={`/labels/${label.id}/watchlists`}
                    className="text-sm text-muted hover:text-gray-200 transition px-3 py-1.5 rounded bg-surface-light"
                  >
                    Watchlists
                  </Link>
                  <Link
                    href={`/labels/${label.id}/scout-feed`}
                    className="text-sm text-primary hover:text-primary-light transition px-3 py-1.5 rounded bg-primary/10"
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
