import Link from "next/link";
import { api } from "@/lib/api";
import { formatNumber, formatPercent, scoreColor } from "@/lib/utils";
import { ArtistCharts } from "./charts";
import { ArtistFeedback } from "./feedback";
import { ArtistWatchlistButton } from "./watchlist";

export default async function ArtistDetailPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams?: Promise<{ label?: string }>;
}) {
  const { id } = await params;
  const resolvedSearch = searchParams ? await searchParams : undefined;
  const labelId = resolvedSearch?.label;
  const artist = await api.getArtist(id, labelId);
  const trendExtra = artist.latest_features?.extra as Record<string, unknown> | undefined;
  const volatility = typeof trendExtra?.volatility_30d === "number"
    ? (trendExtra.volatility_30d as number)
    : undefined;
  const sustainedRatio = typeof trendExtra?.sustained_ratio_30d === "number"
    ? (trendExtra.sustained_ratio_30d as number)
    : undefined;
  const spikeRatio = typeof trendExtra?.spike_ratio_30d === "number"
    ? (trendExtra.spike_ratio_30d as number)
    : undefined;

  return (
    <div>
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-xs text-muted mb-6">
        <Link href="/dashboard" className="hover:text-gray-200 transition-colors duration-200">Labels</Link>
        {labelId && (
          <>
            <span>/</span>
            <Link href={`/labels/${labelId}/scout-feed`} className="hover:text-gray-200 transition-colors duration-200">Scout Feed</Link>
          </>
        )}
        <span>/</span>
        <span className="text-gray-200">{artist.name}</span>
      </div>

      {/* Header */}
      <div className="bg-surface border border-border rounded-lg p-6 mb-6">
        <div className="flex items-start gap-6">
          {artist.image_url && (
            <img src={artist.image_url} alt={artist.name} className="w-20 h-20 rounded-lg object-cover" />
          )}
          <div className="flex-1">
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold">{artist.name}</h1>
              {artist.is_candidate && (
                <span className="text-xs bg-primary/10 text-primary px-2 py-0.5 rounded">Candidate</span>
              )}
              {artist.label_stage && (
                <span className="text-xs bg-surface-light text-muted px-2 py-0.5 rounded">
                  {artist.label_stage}
                </span>
              )}
            </div>
            {artist.bio && <p className="text-muted text-sm mb-2">{artist.bio}</p>}
            {artist.genre_tags && (
              <div className="flex flex-wrap gap-2 mb-3">
                {artist.genre_tags.map((g) => (
                  <span key={g} className="text-xs bg-surface-light text-gray-400 px-2 py-0.5 rounded">{g}</span>
                ))}
              </div>
            )}
            <div className="flex gap-3">
              {artist.platform_accounts
                .filter((acc) => acc.platform_url && ["spotify", "youtube", "tiktok", "instagram"].includes(acc.platform))
                .map((acc) => (
                <a key={acc.platform_id} href={acc.platform_url} target="_blank" rel="noopener"
                  className="text-xs text-accent hover:text-accent-light transition-colors duration-200">
                  {acc.platform}
                </a>
              ))}
            </div>
          </div>
          {/* Quick nav buttons */}
          <div className="flex flex-col gap-2 shrink-0">
            {labelId && (
              <Link href={`/labels/${labelId}/scout-feed`}
                className="text-xs bg-primary/10 text-primary px-3 py-1.5 rounded-lg hover:bg-primary/20 transition-all duration-200">
                Back to Feed
              </Link>
            )}
            {labelId && (
              <ArtistWatchlistButton labelId={labelId} artistId={artist.id} />
            )}
            {labelId && (
              <Link href={`/labels/${labelId}/taste-map`}
                className="text-xs bg-accent/10 text-accent px-3 py-1.5 rounded-lg hover:bg-accent/20 transition-all duration-200">
                Taste Map
              </Link>
            )}
            <Link href="/dashboard"
              className="text-xs bg-surface-light text-muted px-3 py-1.5 rounded-lg hover:text-gray-200 transition-all duration-200">
              All Labels
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Grid */}
      {artist.latest_features && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard label="Momentum" value={formatPercent(artist.latest_features.momentum_score || 0)}
            color={scoreColor(artist.latest_features.momentum_score || 0)} />
          <MetricCard label="7d Growth" value={formatPercent(artist.latest_features.growth_7d || 0)}
            color={(artist.latest_features.growth_7d || 0) > 0 ? "text-success" : "text-danger"} />
          <MetricCard label="30d Growth" value={formatPercent(artist.latest_features.growth_30d || 0)}
            color={(artist.latest_features.growth_30d || 0) > 0 ? "text-success" : "text-danger"} />
          <MetricCard label="Risk" value={formatPercent(artist.latest_features.risk_score || 0)}
            color={scoreColor(1 - (artist.latest_features.risk_score || 0))} />
        </div>
      )}

      {(volatility != null || sustainedRatio != null || spikeRatio != null) && (
        <div className="bg-surface border border-border rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">Trend Quality (30d)</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {volatility != null && (
              <MetricCard
                label="Volatility"
                value={formatPercent(volatility)}
                color={scoreColor(1 - Math.min(volatility / 0.3, 1))}
              />
            )}
            {sustainedRatio != null && (
              <MetricCard
                label="Sustained Growth"
                value={formatPercent(sustainedRatio)}
                color={scoreColor(Math.min(sustainedRatio, 1))}
              />
            )}
            {spikeRatio != null && (
              <MetricCard
                label="Spike Ratio"
                value={`${spikeRatio.toFixed(1)}x`}
                color={scoreColor(1 - Math.min(spikeRatio / 5, 1))}
              />
            )}
          </div>
        </div>
      )}

      {/* Risk Flags */}
      {artist.latest_features?.risk_flags && artist.latest_features.risk_flags.length > 0 && (
        <div className="bg-danger/5 border border-danger/20 rounded-lg p-4 mb-6">
          <h3 className="text-danger font-semibold text-sm mb-2">Risk Indicators</h3>
          <div className="flex flex-wrap gap-2">
            {artist.latest_features.risk_flags.map((flag) => (
              <span key={flag} className="text-xs bg-danger/10 text-danger px-2 py-1 rounded">{flag}</span>
            ))}
          </div>
        </div>
      )}

      {/* Cultural Profile */}
      {artist.cultural_profile && (
        <div className="bg-surface border border-violet-500/20 rounded-lg p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-semibold text-violet-400">Cultural Profile</h2>
            {artist.cultural_profile.breakout_signals?.is_breakout_candidate && (
              <span className="text-xs bg-violet-500/15 text-violet-400 px-2 py-0.5 rounded font-medium">
                Breakout Signal
              </span>
            )}
          </div>

          {/* Cultural Energy + Sub-scores */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
            <div className="bg-surface-light rounded-lg p-3">
              <p className="text-xs text-muted mb-1">Cultural Energy</p>
              <p className="text-xl font-bold font-mono text-violet-400">
                {((artist.cultural_profile.scores?.cultural_energy ?? 0) * 100).toFixed(0)}
              </p>
            </div>
            {artist.cultural_profile.scores?.sub_scores && (
              <>
                {artist.cultural_profile.scores.sub_scores.sentiment_strength != null && (
                  <div className="bg-surface-light rounded-lg p-3">
                    <p className="text-xs text-muted mb-1">Sentiment</p>
                    <p className="text-lg font-bold font-mono text-gray-200">
                      {(artist.cultural_profile.scores.sub_scores.sentiment_strength * 100).toFixed(0)}
                    </p>
                  </div>
                )}
                {artist.cultural_profile.scores.sub_scores.engagement_density != null && (
                  <div className="bg-surface-light rounded-lg p-3">
                    <p className="text-xs text-muted mb-1">Engagement</p>
                    <p className="text-lg font-bold font-mono text-gray-200">
                      {(artist.cultural_profile.scores.sub_scores.engagement_density * 100).toFixed(0)}
                    </p>
                  </div>
                )}
                {artist.cultural_profile.scores.sub_scores.superfan_density != null && (
                  <div className="bg-surface-light rounded-lg p-3">
                    <p className="text-xs text-muted mb-1">Superfans</p>
                    <p className="text-lg font-bold font-mono text-gray-200">
                      {(artist.cultural_profile.scores.sub_scores.superfan_density * 100).toFixed(0)}
                    </p>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Cultural Themes */}
          {artist.cultural_profile.cultural_identity?.themes && artist.cultural_profile.cultural_identity.themes.length > 0 && (
            <div className="mb-5">
              <h3 className="text-sm font-semibold text-muted mb-2">Cultural Themes</h3>
              <div className="space-y-2">
                {artist.cultural_profile.cultural_identity.themes.map((theme) => (
                  <div key={theme.label} className="flex items-center gap-3">
                    <span className="text-xs bg-violet-500/10 text-violet-400 px-2 py-0.5 rounded min-w-fit">
                      {theme.label}
                    </span>
                    <div className="flex-1 h-1.5 bg-surface-light rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-violet-500" style={{ width: `${theme.confidence * 100}%` }} />
                    </div>
                    <span className="text-xs text-muted italic truncate max-w-[200px]">&ldquo;{theme.sample_evidence}&rdquo;</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fan Community + Persona */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
            {artist.cultural_profile.fan_community && (
              <div>
                <h3 className="text-sm font-semibold text-muted mb-1">Fan Community</h3>
                <p className="text-gray-300 text-sm">{artist.cultural_profile.fan_community}</p>
              </div>
            )}
            {artist.cultural_profile.persona?.summary && (
              <div>
                <h3 className="text-sm font-semibold text-muted mb-1">Artist Persona</h3>
                <p className="text-gray-300 text-sm">{artist.cultural_profile.persona.summary}</p>
              </div>
            )}
          </div>

          {/* Evidence Snippets */}
          {artist.cultural_profile.evidence_snippets && artist.cultural_profile.evidence_snippets.length > 0 && (
            <div>
              <h3 className="text-sm font-semibold text-muted mb-2">Fan Voices</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {artist.cultural_profile.evidence_snippets.slice(0, 6).map((snippet, i) => (
                  <div key={i} className="bg-surface-light rounded p-3 text-sm">
                    <p className="text-gray-300 italic">&ldquo;{snippet.text}&rdquo;</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted">{snippet.platform}</span>
                      <span className={`text-xs ${
                        snippet.sentiment === "very_positive" ? "text-success" :
                        snippet.sentiment === "positive" ? "text-success/70" :
                        snippet.sentiment === "critical" ? "text-warning" :
                        snippet.sentiment === "negative" ? "text-danger" : "text-muted"
                      }`}>
                        {snippet.sentiment}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Breakout Reasons */}
          {artist.cultural_profile.breakout_signals?.is_breakout_candidate &&
           artist.cultural_profile.breakout_signals.reasons &&
           artist.cultural_profile.breakout_signals.reasons.length > 0 && (
            <div className="mt-4 bg-violet-500/5 border border-violet-500/20 rounded-lg p-4">
              <h3 className="text-sm font-semibold text-violet-400 mb-2">Breakout Indicators</h3>
              <ul className="space-y-1">
                {artist.cultural_profile.breakout_signals.reasons.map((reason, i) => (
                  <li key={i} className="text-sm text-gray-300 flex gap-2">
                    <span className="text-violet-400">&#8594;</span> {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Charts */}
      {artist.snapshots.length > 0 && (
        <div className="bg-surface border border-border rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">30-Day Trends</h2>
          <ArtistCharts snapshots={artist.snapshots} />
        </div>
      )}

      {/* LLM Brief */}
      {artist.llm_brief && (
        <div className="bg-surface border border-border rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4 text-primary">AI Scouting Brief</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-semibold text-muted mb-1">What&apos;s Happening</h3>
              <p className="text-gray-300">{artist.llm_brief.what_is_happening}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-muted mb-1">Why They Fit</h3>
              <p className="text-gray-300">{artist.llm_brief.why_fit}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-muted mb-1">Risks &amp; Unknowns</h3>
              <p className="text-gray-300">{artist.llm_brief.risks_unknowns}</p>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-muted mb-1">Next Actions</h3>
              <ul className="space-y-1">
                {artist.llm_brief.next_actions.map((action, i) => (
                  <li key={i} className="text-gray-300 flex gap-2 text-sm">
                    <span className="text-primary">&#8594;</span> {action}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Feedback */}
      {labelId && <ArtistFeedback artistId={artist.id} labelId={labelId} history={artist.feedback_history || []} />}
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <p className="text-xs text-muted mb-1">{label}</p>
      <p className={`text-xl font-bold font-mono ${color}`}>{value}</p>
    </div>
  );
}
