import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden grid-bg flex flex-col">
      {/* Ambient glow layers */}
      <div className="fixed inset-0 glow-top-left pointer-events-none" />
      <div className="fixed inset-0 glow-bottom-right pointer-events-none" />

      {/* Navbar */}
      <nav className="relative z-10 w-full px-8 py-5 flex items-center justify-between">
        <span className="text-2xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent animate-fade-in">
          Tayste
        </span>
        <div className="flex items-center gap-4 animate-fade-in delay-300">
          <Link
            href="/dashboard"
            className="text-sm text-muted hover:text-gray-200 transition-colors duration-300"
          >
            Dashboard
          </Link>
          <Link
            href="/import"
            className="text-sm text-muted hover:text-gray-200 transition-colors duration-300"
          >
            Import
          </Link>
          <Link
            href="/dashboard"
            className="btn-glow text-sm bg-primary/10 text-primary-light border border-primary/30 px-4 py-2 rounded-lg"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 flex flex-col items-center justify-center text-center px-6 pt-20 pb-32">
        {/* Badge */}
        <div className="animate-fade-in-up mb-6">
          <span className="inline-flex items-center gap-2 text-xs font-medium bg-primary/10 text-primary-light border border-primary/20 rounded-full px-4 py-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            AI-Powered A&amp;R Intelligence
          </span>
        </div>

        {/* Headline */}
        <h1 className="animate-fade-in-up delay-200 text-5xl md:text-7xl font-bold tracking-tight leading-[1.1] max-w-4xl">
          <span className="text-white">Discover your next</span>
          <br />
          <span className="bg-gradient-to-r from-primary via-primary-light to-accent bg-clip-text text-transparent animate-gradient">
            breakthrough artist
          </span>
        </h1>

        {/* Subtitle */}
        <p className="animate-fade-in-up delay-400 mt-6 text-lg md:text-xl text-muted max-w-2xl leading-relaxed">
          Tayste maps your label&apos;s taste DNA, discovers emerging artists across platforms,
          and ranks them with explainable scoring &mdash; so you never miss the signal in the noise.
        </p>

        {/* CTA Buttons */}
        <div className="animate-fade-in-up delay-600 mt-10 flex flex-col sm:flex-row gap-4">
          <Link
            href="/dashboard"
            className="btn-glow inline-flex items-center justify-center gap-2 bg-primary text-white font-semibold px-8 py-3.5 rounded-xl text-base"
          >
            Open Dashboard
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
            </svg>
          </Link>
          <Link
            href="/import"
            className="btn-outline-glow inline-flex items-center justify-center gap-2 border border-border text-gray-300 font-semibold px-8 py-3.5 rounded-xl text-base"
          >
            Import a Roster
          </Link>
        </div>
      </section>

      {/* Feature Cards */}
      <section className="relative z-10 max-w-6xl mx-auto px-6 pb-32">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <FeatureCard
            delay="delay-500"
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 14.25v2.25m3-4.5v4.5m3-6.75v6.75m3-9v9M6 20.25h12A2.25 2.25 0 0020.25 18V6A2.25 2.25 0 0018 3.75H6A2.25 2.25 0 003.75 6v12A2.25 2.25 0 006 20.25z" />
              </svg>
            }
            title="Label Taste Map"
            description="Build an embedding-based taste profile from your roster. Cluster your sound, name the clusters, and surface your label's musical thesis."
            color="primary"
          />
          <FeatureCard
            delay="delay-700"
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.042 21.672L13.684 16.6m0 0l-2.51 2.225.569-9.47 5.227 7.917-3.286-.672zM12 2.25V4.5m5.834.166l-1.591 1.591M20.25 10.5H18M7.757 14.743l-1.59 1.59M6 10.5H3.75m4.007-4.243l-1.59-1.59" />
              </svg>
            }
            title="Scout Feed"
            description="Ranked candidates scored on Fit, Momentum, and Risk. Explainable math, no black boxes. One-click shortlist or pass."
            color="accent"
          />
          <FeatureCard
            delay="delay-1000"
            icon={
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
              </svg>
            }
            title="AI Intelligence"
            description="LLM-generated scouting briefs, label DNA analysis, and discovery query expansion. Structured, cached, and safe to skip."
            color="primary"
          />
        </div>
      </section>

      {/* How It Works */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 pb-32">
        <h2 className="animate-fade-in-up text-3xl font-bold text-center mb-16">
          <span className="text-white">How it </span>
          <span className="bg-gradient-to-r from-accent to-primary bg-clip-text text-transparent">works</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {[
            { step: "01", title: "Import Roster", desc: "Paste your artist list or upload a file. We resolve YouTube channels automatically." },
            { step: "02", title: "Build Taste Map", desc: "Metric embeddings + clustering define your label's sonic fingerprint." },
            { step: "03", title: "Discover & Score", desc: "YouTube search discovers candidates. Fit x Momentum - Risk ranks them." },
            { step: "04", title: "Act & Feedback", desc: "Review briefs, shortlist or pass. Your feedback trains future rankings." },
          ].map((item, i) => (
            <div key={item.step} className={`animate-fade-in-up delay-${(i + 3) * 200} text-center`}>
              <div className="text-4xl font-bold text-primary/20 mb-3">{item.step}</div>
              <h3 className="text-white font-semibold mb-2">{item.title}</h3>
              <p className="text-sm text-muted leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Stats Bar */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 pb-32">
        <div className="animate-fade-in-up grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { value: "30 days", label: "of trend data per artist", color: "text-primary-light" },
            { value: "3-score", label: "Fit · Momentum · Risk", color: "text-accent" },
            { value: "100%", label: "explainable rankings", color: "text-primary-light" },
            { value: "Zero", label: "black-box decisions", color: "text-accent" },
          ].map((stat) => (
            <div key={stat.label} className="text-center py-6 px-4 bg-surface/40 border border-border/50 rounded-xl">
              <div className={`text-3xl font-bold ${stat.color} mb-1`}>{stat.value}</div>
              <div className="text-sm text-muted">{stat.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Product Preview */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 pb-32">
        <h2 className="animate-fade-in-up text-3xl font-bold text-center mb-4">
          <span className="text-white">See the </span>
          <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">Scout Feed</span>
        </h2>
        <p className="animate-fade-in-up delay-200 text-muted text-center max-w-2xl mx-auto mb-12">
          Every candidate is ranked with transparent math. No guesswork, no hidden weights &mdash; just signal.
        </p>
        <div className="animate-fade-in-up delay-400 bg-surface border border-border rounded-2xl p-6 overflow-hidden">
          {/* Mock Scout Feed rows */}
          <div className="flex items-center justify-between text-xs text-muted border-b border-border/50 pb-3 mb-4 px-2">
            <span className="w-8">#</span>
            <span className="flex-1">Artist</span>
            <span className="w-20 text-center">Fit</span>
            <span className="w-20 text-center">Momentum</span>
            <span className="w-20 text-center">Risk</span>
            <span className="w-24 text-right">Score</span>
          </div>
          {[
            { rank: 1, name: "Pale Waves", genre: "Dream Pop", fit: 92, momentum: 87, risk: 12, score: 92.4 },
            { rank: 2, name: "Lunar Vacancy", genre: "Shoegaze", fit: 88, momentum: 91, risk: 18, score: 86.1 },
            { rank: 3, name: "Dusk Protocol", genre: "Post-Punk", fit: 85, momentum: 78, risk: 8, score: 83.7 },
            { rank: 4, name: "Soft Regime", genre: "Indie Pop", fit: 79, momentum: 82, risk: 14, score: 78.2 },
            { rank: 5, name: "Violet Transmission", genre: "Synth-Pop", fit: 76, momentum: 70, risk: 10, score: 72.8 },
          ].map((row) => (
            <div
              key={row.rank}
              className="flex items-center justify-between py-3 px-2 rounded-lg hover:bg-white/[0.02] transition-colors group"
            >
              <span className="w-8 text-sm text-muted">{row.rank}</span>
              <div className="flex-1">
                <span className="text-white font-medium text-sm group-hover:text-primary-light transition-colors">{row.name}</span>
                <span className="ml-2 text-xs text-muted">{row.genre}</span>
              </div>
              <div className="w-20 text-center">
                <span className="text-sm text-green-400">{row.fit}</span>
              </div>
              <div className="w-20 text-center">
                <span className="text-sm text-accent">{row.momentum}</span>
              </div>
              <div className="w-20 text-center">
                <span className="text-sm text-red-400/80">{row.risk}</span>
              </div>
              <div className="w-24 text-right">
                <span className="text-sm font-semibold text-white">{row.score.toFixed(1)}</span>
              </div>
            </div>
          ))}
          <div className="mt-4 pt-4 border-t border-border/50 text-center">
            <span className="text-xs text-muted">Score = Fit × Momentum − Risk &nbsp;·&nbsp; Updated daily</span>
          </div>
        </div>
      </section>

      {/* Why Tayste */}
      <section className="relative z-10 max-w-5xl mx-auto px-6 pb-12">
        <h2 className="animate-fade-in-up text-3xl font-bold text-center mb-12">
          <span className="text-white">Why </span>
          <span className="bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">Tayste</span>
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Traditional */}
          <div className="animate-fade-in-up delay-200 bg-surface/40 border border-border/50 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-red-500/10 text-red-400 flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-muted">Traditional A&R</h3>
            </div>
            <ul className="space-y-3">
              {[
                "Hours scrolling playlists and socials",
                "Gut-feel decisions, hard to justify",
                "Slow to spot breakout trends",
                "Talent slips through the cracks",
                "No structured feedback loop",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-muted/70">
                  <svg className="w-4 h-4 mt-0.5 text-red-400/50 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
          </div>

          {/* Tayste */}
          <div className="animate-fade-in-up delay-400 bg-surface border border-primary/20 rounded-2xl p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-primary/10 text-primary flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z" />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-white">Scouting with Tayste</h3>
            </div>
            <ul className="space-y-3">
              {[
                "Automated discovery from YouTube and beyond",
                "Explainable Fit × Momentum − Risk scoring",
                "30-day trend snapshots catch breakouts early",
                "Every candidate ranked, none lost",
                "Feedback trains future recommendations",
              ].map((item) => (
                <li key={item} className="flex items-start gap-3 text-sm text-gray-300">
                  <svg className="w-4 h-4 mt-0.5 text-green-400 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="relative z-10 max-w-3xl mx-auto px-6 pb-12 text-center">
        <div className="animate-fade-in-up bg-surface border border-border rounded-2xl p-10 animate-pulse-glow">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
            Ready to find your next signing?
          </h2>
          <p className="text-muted mb-8 max-w-lg mx-auto">
            Import your roster and let Tayste surface the emerging artists that match your sound.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/dashboard"
              className="btn-glow inline-flex items-center justify-center gap-2 bg-primary text-white font-semibold px-8 py-3.5 rounded-xl text-base"
            >
              Open Dashboard
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 7l5 5m0 0l-5 5m5-5H6" />
              </svg>
            </Link>
            <Link
              href="/import"
              className="btn-outline-glow inline-flex items-center justify-center gap-2 border border-border text-gray-300 font-semibold px-8 py-3.5 rounded-xl text-base"
            >
              Import a Roster
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 mt-auto border-t border-border/50 py-6 text-center text-xs text-muted">
        Tayste &mdash; AI A&amp;R Intelligence Platform
      </footer>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
  color,
  delay,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  color: "primary" | "accent";
  delay: string;
}) {
  const borderHover = color === "primary" ? "hover:border-primary/40" : "hover:border-accent/40";
  const iconBg = color === "primary" ? "bg-primary/10 text-primary" : "bg-accent/10 text-accent";

  return (
    <div className={`animate-fade-in-up ${delay} group bg-surface/60 backdrop-blur-sm border border-border rounded-xl p-6 transition-all duration-300 ${borderHover} hover:-translate-y-1`}>
      <div className={`w-10 h-10 rounded-lg ${iconBg} flex items-center justify-center mb-4 transition-transform duration-300 group-hover:scale-110`}>
        {icon}
      </div>
      <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
      <p className="text-muted text-sm leading-relaxed">{description}</p>
    </div>
  );
}
