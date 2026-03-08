import Link from "next/link";

const steps = [
  {
    number: "01",
    title: "Import Your Roster",
    description:
      "Paste your artist list or upload a file. We resolve Spotify, YouTube, and Soundcharts profiles automatically — no manual lookups needed.",
  },
  {
    number: "02",
    title: "Build Your Taste Map",
    description:
      "Metric-based embeddings and KMeans clustering define your label's sonic fingerprint. See your sound in clusters, named and mapped visually.",
  },
  {
    number: "03",
    title: "Discover Emerging Artists",
    description:
      "Soundcharts rising charts and Spotify's related-artist graph surface fresh candidates. Dual discovery pipelines mean nothing slips through.",
  },
  {
    number: "04",
    title: "Score & Rank",
    description:
      "Every candidate gets a transparent score: Fit × Momentum − Risk. No black boxes, no hidden weights — just signal you can explain to your team.",
  },
  {
    number: "05",
    title: "Review AI Briefs",
    description:
      "Claude-powered scouting briefs give you context at a glance — genre positioning, growth narrative, and risk factors. Structured, cached, and optional.",
  },
  {
    number: "06",
    title: "Act & Feedback",
    description:
      "Shortlist or pass with one click. Your feedback trains future rankings, making every scouting session sharper than the last.",
  },
];

export default function HowItWorksPage() {
  return (
    <div className="min-h-screen bg-black text-white">
      {/* Nav */}
      <nav className="px-6 sm:px-12 py-6 flex items-center justify-between">
        <Link
          href="/"
          className="text-2xl font-extrabold tracking-tighter"
          style={{ fontFamily: "Verdana, Geneva, sans-serif" }}
        >
          TAYSTE
        </Link>
        <div className="flex items-center gap-4">
          <Link href="/about" className="text-sm text-white/60 hover:text-white transition-colors">
            About
          </Link>
          <Link href="/contact" className="text-sm text-white/60 hover:text-white transition-colors">
            Contact
          </Link>
          <Link
            href="/login"
            className="px-5 py-2 rounded-md bg-primary/20 border border-primary/40 text-white text-sm font-medium hover:bg-primary/30 transition-colors"
          >
            Sign In
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 sm:px-12 pt-16 pb-12 max-w-4xl">
        <p className="text-primary text-sm font-medium tracking-widest uppercase mb-4">
          The Pipeline
        </p>
        <h1
          className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-[1.05] mb-6"
          style={{ fontFamily: "Verdana, Geneva, sans-serif" }}
        >
          How it Works
        </h1>
        <p className="text-white/50 text-lg max-w-2xl leading-relaxed">
          From roster import to ranked scout feed — six steps, fully transparent,
          no black boxes.
        </p>
      </section>

      {/* Steps */}
      <section className="px-6 sm:px-12 pb-24 max-w-5xl">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-14">
          {steps.map((step) => (
            <div key={step.number} className="group">
              <div className="flex items-baseline gap-4 mb-3">
                <span className="text-5xl font-extrabold text-primary/20 group-hover:text-primary/40 transition-colors">
                  {step.number}
                </span>
                <h2 className="text-xl font-bold text-white">{step.title}</h2>
              </div>
              <p className="text-white/50 leading-relaxed pl-[4.5rem]">
                {step.description}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="px-6 sm:px-12 pb-20 max-w-3xl">
        <div className="border border-primary/20 rounded-2xl p-10 bg-primary/[0.03]">
          <h2 className="text-2xl font-bold mb-3">Ready to see it in action?</h2>
          <p className="text-white/50 mb-6">
            Import your roster and watch the scout feed populate in minutes.
          </p>
          <Link
            href="/login"
            className="inline-block px-8 py-3 rounded-lg bg-primary text-white font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
          >
            Get Started
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-6 px-6 sm:px-12 text-sm text-white/30">
        Tayste — AI A&R Intelligence
      </footer>
    </div>
  );
}
