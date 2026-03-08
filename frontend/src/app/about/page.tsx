import Link from "next/link";

export default function AboutPage() {
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
          <Link href="/how-it-works" className="text-sm text-white/60 hover:text-white transition-colors">
            How it Works
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
          Our Story
        </p>
        <h1
          className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-[1.05] mb-6"
          style={{ fontFamily: "Verdana, Geneva, sans-serif" }}
        >
          About Tayste
        </h1>
        <p className="text-white/50 text-lg max-w-2xl leading-relaxed">
          Built for the people who find the music before anyone else hears it.
        </p>
      </section>

      {/* Content */}
      <section className="px-6 sm:px-12 pb-20 max-w-4xl">
        <div className="space-y-16">
          {/* Mission */}
          <div>
            <h2 className="text-2xl font-bold mb-4 text-white">The Mission</h2>
            <p className="text-white/50 leading-relaxed text-lg">
              A&R has always been part art, part instinct. But in a world where thousands of
              artists release music every day, instinct alone isn&apos;t enough. Tayste gives
              scouts the data layer they never had — without replacing the ear that makes
              them great.
            </p>
          </div>

          {/* What we believe */}
          <div>
            <h2 className="text-2xl font-bold mb-4 text-white">What We Believe</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              {[
                {
                  title: "Transparency over magic",
                  body: "Every score is explainable. Fit × Momentum − Risk. No hidden weights, no black-box recommendations.",
                },
                {
                  title: "AI augments, never decides",
                  body: "LLMs write the briefs and expand discovery queries. They never touch the ranking math. The human ear makes the final call.",
                },
                {
                  title: "Data should be append-only",
                  body: "Time-series snapshots capture 30 days of momentum. Nothing gets overwritten — you always see the full trajectory.",
                },
                {
                  title: "Feedback closes the loop",
                  body: "Every shortlist and pass you make trains future rankings. The system gets sharper the more you use it.",
                },
              ].map((item) => (
                <div key={item.title} className="border border-white/10 rounded-xl p-6 bg-white/[0.02]">
                  <h3 className="text-white font-semibold mb-2">{item.title}</h3>
                  <p className="text-white/40 text-sm leading-relaxed">{item.body}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Stack */}
          <div>
            <h2 className="text-2xl font-bold mb-4 text-white">The Stack</h2>
            <p className="text-white/50 leading-relaxed mb-6">
              Tayste is built with modern infrastructure designed for speed and reliability.
            </p>
            <div className="flex flex-wrap gap-3">
              {[
                "FastAPI",
                "Next.js 15",
                "PostgreSQL + pgvector",
                "Claude AI",
                "Soundcharts",
                "Spotify API",
                "Tailwind CSS",
                "Docker",
              ].map((tech) => (
                <span
                  key={tech}
                  className="px-4 py-1.5 rounded-full text-sm text-primary-light bg-primary/10 border border-primary/20"
                >
                  {tech}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Bottom CTA */}
      <section className="px-6 sm:px-12 pb-20 max-w-3xl">
        <div className="border border-primary/20 rounded-2xl p-10 bg-primary/[0.03]">
          <h2 className="text-2xl font-bold mb-3">Want to see how it works?</h2>
          <p className="text-white/50 mb-6">
            Walk through the pipeline from roster import to ranked scout feed.
          </p>
          <Link
            href="/how-it-works"
            className="inline-block px-8 py-3 rounded-lg bg-primary text-white font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
          >
            See the Pipeline
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
