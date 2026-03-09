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

  const spotifyAcc = artist.platform_accounts.find((a) => a.platform === "spotify" && a.platform_url);
  const youtubeAcc = artist.platform_accounts.find((a) => a.platform === "youtube" && a.platform_url);

  return (
    <div className="page-fade">
      {/* Hero section with gradient background */}
      <div className="relative rounded-lg overflow-hidden mb-6" style={{
        background: "linear-gradient(160deg, #1a1028, #0f1a28, #0a0a0a)",
      }}>
        {/* Radial purple glow */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_30%_50%,rgba(124,92,252,0.12),transparent_70%)]" />
        {/* Gradient top bar */}
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />

        <div className="relative p-8 flex items-center gap-8">
          {/* Vinyl / Image */}
          {artist.image_url ? (
            <div className="rounded-full flex-shrink-0 overflow-hidden border-2 border-white/[0.12] shadow-[0_0_30px_rgba(124,92,252,0.25)]" style={{ width: 110, height: 110 }}>
              <img src={artist.image_url} alt={artist.name} className="w-full h-full object-cover" />
            </div>
          ) : (
            <div className="vinyl flex-shrink-0" style={{ width: 110, height: 110 }}>
              <div className="rounded-full bg-[#0a0a0a] border-2 border-white/[0.12] absolute" style={{ width: 22, height: 22 }} />
            </div>
          )}

          {/* Name and details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-3 mb-1">
              {artist.is_candidate && (
                <span className="tag text-[10px]">Candidate</span>
              )}
              {artist.label_stage && (
                <span className="text-xs bg-white/[0.03] text-white/35 px-2 py-0.5 rounded-full border border-white/[0.06]">
                  {artist.label_stage}
                </span>
              )}
            </div>
            <h1 className="font-display text-[clamp(48px,10vw,96px)] leading-none tracking-wide text-[#f5f5f0]">
              {artist.name}
            </h1>
            {artist.bio && <p className="text-white/60 text-sm mt-2 max-w-xl">{artist.bio}</p>}
            {artist.genre_tags && (
              <div className="flex flex-wrap gap-1 mt-3">
                {artist.genre_tags.map((g) => (
                  <span key={g} className="tag">{g}</span>
                ))}
              </div>
            )}
          </div>

          {/* Match score (right side) */}
          {artist.latest_features && (
            <div className="text-center shrink-0">
              <div className="font-display text-[52px] leading-none text-primary">
                {((artist.latest_features.momentum_score || 0) * 100).toFixed(0)}
              </div>
              <div className="text-[10px] text-white/40 tracking-wider uppercase mt-1">
                Momentum
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Action bar */}
      <div className="flex flex-wrap gap-2 mb-6">
        {labelId && (
          <ArtistWatchlistButton labelId={labelId} artistId={artist.id} />
        )}
        {spotifyAcc && (
          <a
            href={spotifyAcc.platform_url!}
            target="_blank"
            rel="noopener"
            className="inline-flex items-center rounded-pill px-5 py-2 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200 hover:-translate-y-px"
          >
            Open Spotify
          </a>
        )}
        {youtubeAcc && (
          <a
            href={youtubeAcc.platform_url!}
            target="_blank"
            rel="noopener"
            className="inline-flex items-center rounded-pill px-5 py-2 text-xs bg-transparent border border-primary text-primary hover:bg-primary hover:text-[#f5f5f0] transition-all duration-200 hover:-translate-y-px"
          >
            Open YouTube
          </a>
        )}
        {labelId && (
          <Link
            href={`/labels/${labelId}/scout-feed`}
            className="inline-flex items-center rounded-pill px-5 py-2 text-xs bg-transparent border border-white/[0.12] text-white/40 hover:border-primary hover:text-primary transition-all duration-200 hover:-translate-y-px"
          >
            Back to Feed
          </Link>
        )}
        <Link
          href="/dashboard"
          className="inline-flex items-center rounded-pill px-5 py-2 text-xs bg-transparent border border-white/[0.12] text-white/40 hover:border-primary hover:text-primary transition-all duration-200 hover:-translate-y-px"
        >
          Home
        </Link>
      </div>

      {/* Stats grid */}
      {artist.latest_features && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <StatBadge
            label="Momentum"
            value={formatPercent(artist.latest_features.momentum_score || 0)}
            color={scoreColor(artist.latest_features.momentum_score || 0)}
          />
          <StatBadge
            label="7d Growth"
            value={formatPercent(artist.latest_features.growth_7d || 0)}
            color={(artist.latest_features.growth_7d || 0) > 0 ? "text-emerald-400" : "text-red-400"}
          />
          <StatBadge
            label="30d Growth"
            value={formatPercent(artist.latest_features.growth_30d || 0)}
            color={(artist.latest_features.growth_30d || 0) > 0 ? "text-emerald-400" : "text-red-400"}
          />
          <StatBadge
            label="Risk"
            value={formatPercent(artist.latest_features.risk_score || 0)}
            color={scoreColor(1 - (artist.latest_features.risk_score || 0))}
          />
        </div>
      )}

      {/* Trend Quality */}
      {(volatility != null || sustainedRatio != null || spikeRatio != null) && (
        <div className="bg-surface border border-white/[0.12] rounded-lg p-6 mb-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
          <h2 className="font-display text-[22px] tracking-wide mb-4 text-[#f5f5f0]">Trend Quality (30d)</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {volatility != null && (
              <StatBadge
                label="Volatility"
                value={formatPercent(volatility)}
                color={scoreColor(1 - Math.min(volatility / 0.3, 1))}
              />
            )}
            {sustainedRatio != null && (
              <StatBadge
                label="Sustained Growth"
                value={formatPercent(sustainedRatio)}
                color={scoreColor(Math.min(sustainedRatio, 1))}
              />
            )}
            {spikeRatio != null && (
              <StatBadge
                label="Spike Ratio"
                value={`${spikeRatio.toFixed(1)}x`}
                color={scoreColor(1 - Math.min(spikeRatio / 5, 1))}
              />
            )}
          </div>
        </div>
      )}

      {/* AI Scouting Brief */}
      {artist.llm_brief && (
        <div className="bg-surface border border-white/[0.12] rounded-lg p-6 mb-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
          <h2 className="font-display text-[22px] tracking-wide mb-4 text-[#f5f5f0]">TAYSTE Analysis</h2>
          <div className="space-y-4">
            <div>
              <h3 className="text-sm font-bold text-white/35 mb-1">What&apos;s Happening</h3>
              <p className="text-white/60">{artist.llm_brief.what_is_happening}</p>
            </div>
            <div>
              <h3 className="text-sm font-bold text-white/35 mb-1">Why They Fit</h3>
              <p className="text-white/60">{artist.llm_brief.why_fit}</p>
            </div>
            <div>
              <h3 className="text-sm font-bold text-white/35 mb-1">Risks &amp; Unknowns</h3>
              <p className="text-white/60">{artist.llm_brief.risks_unknowns}</p>
            </div>
            <div>
              <h3 className="text-sm font-bold text-white/35 mb-1">Next Actions</h3>
              <ul className="space-y-1">
                {artist.llm_brief.next_actions.map((action, i) => (
                  <li key={i} className="text-white/60 flex gap-2 text-sm">
                    <span className="text-white/35">&#8594;</span> {action}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* Cultural Profile */}
      {artist.cultural_profile && (
        <div className="bg-surface border border-white/[0.12] rounded-lg p-6 mb-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
          <div className="flex items-center gap-3 mb-4">
            <h2 className="font-display text-[22px] tracking-wide text-[#f5f5f0]">Cultural Profile</h2>
            {artist.cultural_profile.breakout_signals?.is_breakout_candidate && (
              <span className="tag text-[10px]">Breakout Signal</span>
            )}
          </div>

          {/* Cultural Energy + Sub-scores */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-5">
            <div className="bg-white/[0.04] rounded-lg p-3">
              <p className="text-xs text-white/35 mb-1">Cultural Energy</p>
              <p className="text-xl font-bold font-mono text-white">
                {((artist.cultural_profile.scores?.cultural_energy ?? 0) * 100).toFixed(0)}
              </p>
            </div>
            {artist.cultural_profile.scores?.sub_scores && (
              <>
                {artist.cultural_profile.scores.sub_scores.sentiment_strength != null && (
                  <div className="bg-white/[0.04] rounded-lg p-3">
                    <p className="text-xs text-white/35 mb-1">Sentiment</p>
                    <p className="text-lg font-bold font-mono text-white/60">
                      {(artist.cultural_profile.scores.sub_scores.sentiment_strength * 100).toFixed(0)}
                    </p>
                  </div>
                )}
                {artist.cultural_profile.scores.sub_scores.engagement_density != null && (
                  <div className="bg-white/[0.04] rounded-lg p-3">
                    <p className="text-xs text-white/35 mb-1">Engagement</p>
                    <p className="text-lg font-bold font-mono text-white/60">
                      {(artist.cultural_profile.scores.sub_scores.engagement_density * 100).toFixed(0)}
                    </p>
                  </div>
                )}
                {artist.cultural_profile.scores.sub_scores.superfan_density != null && (
                  <div className="bg-white/[0.04] rounded-lg p-3">
                    <p className="text-xs text-white/35 mb-1">Superfans</p>
                    <p className="text-lg font-bold font-mono text-white/60">
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
              <h3 className="text-sm font-bold text-white/35 mb-2">Cultural Themes</h3>
              <div className="space-y-2">
                {artist.cultural_profile.cultural_identity.themes.map((theme) => (
                  <div key={theme.label} className="flex items-center gap-3">
                    <span className="text-xs bg-white/[0.04] text-white/60 px-2 py-0.5 rounded border border-white/[0.06] min-w-fit">
                      {theme.label}
                    </span>
                    <div className="flex-1 h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                      <div className="h-full rounded-full bg-primary" style={{ width: `${theme.confidence * 100}%` }} />
                    </div>
                    <span className="text-xs text-white/35 italic truncate max-w-[200px]">&ldquo;{theme.sample_evidence}&rdquo;</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Fan Community + Persona */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5">
            {artist.cultural_profile.fan_community && (
              <div>
                <h3 className="text-sm font-bold text-white/35 mb-1">Fan Community</h3>
                <p className="text-white/60 text-sm">{artist.cultural_profile.fan_community}</p>
              </div>
            )}
            {artist.cultural_profile.persona?.summary && (
              <div>
                <h3 className="text-sm font-bold text-white/35 mb-1">Artist Persona</h3>
                <p className="text-white/60 text-sm">{artist.cultural_profile.persona.summary}</p>
              </div>
            )}
          </div>

          {/* Evidence Snippets */}
          {artist.cultural_profile.evidence_snippets && artist.cultural_profile.evidence_snippets.length > 0 && (
            <div>
              <h3 className="text-sm font-bold text-white/35 mb-2">Fan Voices</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {artist.cultural_profile.evidence_snippets.slice(0, 6).map((snippet, i) => (
                  <div key={i} className="bg-white/[0.04] rounded-lg p-3 text-sm">
                    <p className="text-white/60 italic">&ldquo;{snippet.text}&rdquo;</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-white/35">{snippet.platform}</span>
                      <span className={`text-xs ${
                        snippet.sentiment === "very_positive" ? "text-emerald-400" :
                        snippet.sentiment === "positive" ? "text-emerald-400/70" :
                        snippet.sentiment === "critical" ? "text-amber-400" :
                        snippet.sentiment === "negative" ? "text-red-400" : "text-white/35"
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
            <div className="mt-4 bg-white/[0.02] border border-white/[0.06] rounded-lg p-4">
              <h3 className="text-sm font-bold text-white/60 mb-2">Breakout Indicators</h3>
              <ul className="space-y-1">
                {artist.cultural_profile.breakout_signals.reasons.map((reason, i) => (
                  <li key={i} className="text-sm text-white/60 flex gap-2">
                    <span className="text-white/35">&#8594;</span> {reason}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Risk Flags */}
      {artist.latest_features?.risk_flags && artist.latest_features.risk_flags.length > 0 && (
        <div className="bg-surface border border-white/[0.12] rounded-lg p-5 mb-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-danger to-warning" />
          <h3 className="font-display text-[18px] tracking-wide text-red-400 mb-2">Risk Indicators</h3>
          <div className="flex flex-wrap gap-2">
            {artist.latest_features.risk_flags.map((flag) => (
              <span key={flag} className="text-xs bg-red-500/10 text-red-400 px-2 py-1 rounded-pill border border-red-500/20">{flag}</span>
            ))}
          </div>
        </div>
      )}

      {/* Charts */}
      {artist.snapshots.length > 0 && (
        <div className="bg-surface border border-white/[0.12] rounded-lg p-6 mb-6 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
          <h2 className="font-display text-[22px] tracking-wide mb-4 text-[#f5f5f0]">30-Day Trends</h2>
          <ArtistCharts snapshots={artist.snapshots} />
        </div>
      )}

      {/* Feedback */}
      {labelId && <ArtistFeedback artistId={artist.id} labelId={labelId} history={artist.feedback_history || []} />}
    </div>
  );
}

function StatBadge({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div className="bg-surface border border-white/[0.12] rounded-lg p-4 relative overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
      <p className="text-[10px] text-white/40 tracking-wider uppercase mb-1">{label}</p>
      <p className={`font-display text-[28px] leading-none ${color}`}>{value}</p>
    </div>
  );
}
