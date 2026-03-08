"use client";

import Link from "next/link";
import { useEffect, useState, useRef } from "react";

/* ── Abstract orb art (SVG) ────────────────────────────────────── */

function AbstractOrb({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 500 500"
      className={className}
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <ellipse cx="250" cy="260" rx="200" ry="200" stroke="#a855f7" strokeWidth="18" opacity="0.7" />
      <ellipse cx="250" cy="260" rx="200" ry="200" stroke="#22d3ee" strokeWidth="12" opacity="0.3" strokeDasharray="60 80" />
      <ellipse cx="250" cy="260" rx="155" ry="155" stroke="#8b5cf6" strokeWidth="22" opacity="0.8" />
      <ellipse cx="250" cy="260" rx="155" ry="155" stroke="#c084fc" strokeWidth="8" opacity="0.4" strokeDasharray="40 50" />
      <ellipse cx="250" cy="260" rx="110" ry="110" stroke="#34d399" strokeWidth="16" opacity="0.6" />
      <ellipse cx="250" cy="260" rx="110" ry="108" stroke="#a78bfa" strokeWidth="10" opacity="0.5" strokeDasharray="30 40" />
      <ellipse cx="250" cy="260" rx="70" ry="70" stroke="#c084fc" strokeWidth="14" opacity="0.7" />
      <circle cx="250" cy="260" r="40" fill="url(#centerGrad)" />
      <ellipse cx="250" cy="65" rx="25" ry="12" fill="#22d3ee" opacity="0.7" />
      <ellipse cx="230" cy="78" rx="14" ry="8" fill="#a78bfa" opacity="0.6" />
      <ellipse cx="270" cy="78" rx="10" ry="6" fill="#34d399" opacity="0.5" />
      <ellipse cx="60" cy="280" rx="14" ry="30" fill="#ef4444" opacity="0.7" />
      <ellipse cx="80" cy="240" rx="10" ry="22" fill="#f97316" opacity="0.6" />
      <ellipse cx="440" cy="240" rx="12" ry="28" fill="#34d399" opacity="0.6" />
      <ellipse cx="420" cy="300" rx="10" ry="20" fill="#8b5cf6" opacity="0.5" />
      <ellipse cx="200" cy="450" rx="20" ry="14" fill="#ec4899" opacity="0.7" />
      <ellipse cx="250" cy="460" rx="16" ry="10" fill="#a855f7" opacity="0.6" />
      <ellipse cx="300" cy="448" rx="18" ry="12" fill="#c084fc" opacity="0.5" />
      <circle cx="180" cy="470" r="8" fill="#8b5cf6" opacity="0.5" />
      <circle cx="320" cy="465" r="6" fill="#22d3ee" opacity="0.4" />
      <circle cx="250" cy="480" r="10" fill="#a855f7" opacity="0.3" />
      <defs>
        <radialGradient id="centerGrad" cx="50%" cy="40%" r="50%">
          <stop offset="0%" stopColor="#34d399" />
          <stop offset="60%" stopColor="#22c55e" />
          <stop offset="100%" stopColor="#059669" />
        </radialGradient>
      </defs>
    </svg>
  );
}

/* ── Nav button style ──────────────────────────────────────────── */

const navBtnClass =
  "px-5 py-2 rounded-md bg-primary/20 border border-primary/40 text-white text-sm font-medium hover:bg-primary/30 transition-colors whitespace-nowrap";

/* ── Arrow between steps ───────────────────────────────────────── */

function StepArrow() {
  return (
    <svg className="w-10 h-5 text-white/40 shrink-0 hidden sm:block" viewBox="0 0 40 20" fill="none">
      <line x1="0" y1="10" x2="32" y2="10" stroke="currentColor" strokeWidth="2" />
      <path d="M30 4 L38 10 L30 16" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Main client component ─────────────────────────────────────── */

export default function LandingClient({ isLoggedIn }: { isLoggedIn: boolean }) {
  const [scrolled, setScrolled] = useState(false);
  const heroRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const threshold = 300;

    function onScroll() {
      setScrolled(window.scrollY > threshold);
    }

    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const verdana: React.CSSProperties = { fontFamily: "Verdana, Geneva, sans-serif" };

  return (
    <div className="bg-black text-white min-h-screen" style={verdana}>
      {/* ═══════════════════════════════════════════════════════════
          STICKY NAVBAR — appears when scrolled past hero
         ═══════════════════════════════════════════════════════════ */}
      <div
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-500 ${
          scrolled
            ? "translate-y-0 opacity-100"
            : "-translate-y-full opacity-0"
        }`}
      >
        <div className="bg-black/90 backdrop-blur-md border-b border-white/10">
          <div className="flex items-center justify-between px-6 sm:px-12 py-3">
            {/* Logo + nav */}
            <div className="flex items-center gap-6">
              <a
                href="#top"
                className="text-2xl font-extrabold tracking-tighter"
              >
                TAYSTE
              </a>
              <nav className="hidden sm:flex items-center gap-3">
                <a href="#how-it-works" className={navBtnClass}>How it Works</a>
                <a href="#about" className={navBtnClass}>About</a>
                <a href="#contact" className={navBtnClass}>Contact</a>
              </nav>
            </div>
            {/* Auth */}
            <div className="flex items-center gap-3">
              {isLoggedIn ? (
                <Link
                  href="/dashboard"
                  className="px-5 py-2 rounded-lg bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors"
                >
                  Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="px-5 py-2 rounded-lg bg-primary text-white text-sm font-semibold hover:bg-primary/90 transition-colors"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/signup"
                    className="hidden sm:inline-block px-5 py-2 rounded-lg border border-white/20 text-white text-sm font-semibold hover:bg-white/5 transition-colors"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════════════
          SECTION 1 — HERO
         ═══════════════════════════════════════════════════════════ */}
      <section id="top" ref={heroRef} className="relative min-h-screen flex flex-col px-6 sm:px-12">
        {/* Giant TAYSTE title */}
        <h1
          className={`pt-8 sm:pt-12 text-[clamp(4rem,14vw,12rem)] font-extrabold leading-[0.9] tracking-tighter text-white/90 select-none transition-all duration-500 ${
            scrolled ? "opacity-0 -translate-y-8" : "opacity-100 translate-y-0"
          }`}
        >
          TAYSTE
        </h1>

        {/* Orb + content row */}
        <div className="flex-1 flex flex-col lg:flex-row items-start pt-4 pb-16 gap-8 lg:gap-0">
          {/* Left: orb */}
          <div className="w-full lg:w-[45%] flex items-center justify-center lg:justify-start">
            <AbstractOrb className="w-[320px] h-[320px] sm:w-[400px] sm:h-[400px] lg:w-[440px] lg:h-[440px]" />
          </div>

          {/* Right: buttons + text */}
          <div className="w-full lg:w-[55%] flex flex-col gap-8 lg:pt-4">
            {/* Nav buttons (in-hero version) */}
            <div className="flex flex-wrap items-center gap-4">
              <a href="#how-it-works" className={navBtnClass}>How it Works</a>
              <a href="#about" className={navBtnClass}>About</a>
              <a href="#contact" className={navBtnClass}>Contact</a>
            </div>

            {/* Description */}
            <div className="max-w-lg flex flex-col gap-4">
              <p className="text-white text-lg leading-relaxed">
                White word. Verdana font.
              </p>
              <p className="text-white text-lg leading-relaxed">
                A poetic, yet brief description of tayste.
              </p>
              <p className="text-white text-lg leading-relaxed">
                Something in text describing what this product is.
              </p>
              <p className="text-white text-lg leading-relaxed">
                But not in a boring or bland way.
              </p>
              <div className="pt-2">
                <p className="text-white/60 text-sm italic">Signed,</p>
                <p className="text-white/60 text-sm italic">-tayste team...</p>
              </div>
            </div>

            {/* Auth buttons */}
            <div className="flex items-center gap-4">
              {isLoggedIn ? (
                <Link
                  href="/dashboard"
                  className="px-8 py-3 rounded-lg bg-primary text-white font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
                >
                  Go to Dashboard
                </Link>
              ) : (
                <>
                  <Link
                    href="/login"
                    className="px-8 py-3 rounded-lg bg-primary text-white font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/signup"
                    className="px-8 py-3 rounded-lg border border-white/20 text-white font-semibold hover:bg-white/5 transition-colors"
                  >
                    Sign Up
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* ── Dotted divider ──────────────────────────────────────── */}
      <div className="px-6 sm:px-12">
        <div className="border-t-2 border-dotted border-white/30" />
      </div>

      {/* ═══════════════════════════════════════════════════════════
          SECTION 2 — HOW IT WORKS
         ═══════════════════════════════════════════════════════════ */}
      <section id="how-it-works" className="px-6 sm:px-12 py-16">
        <h2 className="text-2xl font-bold mb-10">How it Works:</h2>

        {/* 3-step pipeline with arrows */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-start gap-4 sm:gap-0">
          {[
            { title: "Intake", desc: "Import your roster. We resolve artist profiles across Spotify, Soundcharts, and YouTube." },
            { title: "Search", desc: "Dual discovery: Soundcharts rising charts + Spotify related-artist graph surface candidates." },
            { title: "Refine", desc: "Score with Fit × Momentum − Risk. Review AI briefs. Shortlist or pass — feedback trains the system." },
          ].map((step, i) => (
            <div key={step.title} className="flex items-center gap-4">
              {i > 0 && <StepArrow />}
              <div className="bg-primary/30 border border-primary/50 rounded-lg px-6 py-4 min-w-[180px] text-center">
                <div className="text-white font-bold text-sm">{step.title}</div>
                <div className="text-white/50 text-xs mt-1 leading-relaxed">{step.desc}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          SECTION 3 — FEATURES BAR
         ═══════════════════════════════════════════════════════════ */}
      <section className="border-y border-white/10 bg-white/[0.03]">
        <div className="px-6 sm:px-12 py-5 overflow-x-auto">
          <p className="text-white/50 text-sm whitespace-nowrap">
            <span className="text-white/70 font-semibold">Features: </span>
            AI-powered discovery &nbsp;·&nbsp; Metric-based taste mapping &nbsp;·&nbsp;
            Explainable scoring &nbsp;·&nbsp; Scouting briefs &nbsp;·&nbsp;
            30-day trend snapshots &nbsp;·&nbsp; Feedback-driven ranking &nbsp;·&nbsp;
            Multi-platform data &nbsp;·&nbsp; Watchlists &nbsp;·&nbsp;
            Label DNA analysis
          </p>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          SECTION 4 — ABOUT (alternating cards)
         ═══════════════════════════════════════════════════════════ */}
      <section id="about" className="px-6 sm:px-12 py-16 space-y-12">
        {/* Card 1: text left, image right */}
        <div className="flex flex-col md:flex-row gap-8 items-stretch">
          <div className="md:w-1/2 flex flex-col justify-center">
            <h3 className="text-xl font-bold mb-3">Brief text outlining current stage... beta</h3>
            <p className="text-white/50 leading-relaxed">
              Tayste is currently in beta. We&apos;re working with a handful of independent
              labels to refine the scoring engine, expand discovery pipelines, and shape
              the product around real A&amp;R workflows. Early feedback is shaping everything.
            </p>
          </div>
          <div className="md:w-1/2 bg-white/[0.05] rounded-2xl overflow-hidden flex items-center justify-center min-h-[240px] border border-white/10">
            {/* Placeholder — swap for real image */}
            <div className="text-white/20 text-sm italic">-photo placeholder-</div>
          </div>
        </div>

        {/* Card 2: image left, text right */}
        <div className="flex flex-col md:flex-row-reverse gap-8 items-stretch">
          <div className="md:w-1/2 flex flex-col justify-center">
            <h3 className="text-xl font-bold mb-3">Brief text outlining us makers... cool</h3>
            <p className="text-white/50 leading-relaxed">
              We&apos;re a small team of music nerds and engineers who believe that the
              best A&amp;R is part taste, part data, and zero black boxes. Built with care,
              obsessed with transparency.
            </p>
          </div>
          <div className="md:w-1/2 bg-white/[0.05] rounded-2xl overflow-hidden flex items-center justify-center min-h-[240px] border border-white/10">
            {/* Placeholder — swap for real image */}
            <div className="text-white/20 text-sm italic">-photo placeholder-</div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          SECTION 5 — CONTACT BAR
         ═══════════════════════════════════════════════════════════ */}
      <section id="contact" className="border-y border-white/10 bg-white/[0.03]">
        <div className="px-6 sm:px-12 py-5 text-center">
          <p className="text-white/50 text-sm">
            <span className="text-white/70 font-semibold">Contact: </span>
            hello@tayste.ai &nbsp;·&nbsp; @tayste on Twitter
          </p>
        </div>
      </section>

      {/* ═══════════════════════════════════════════════════════════
          FOOTER — Upside-down TAYSTE
         ═══════════════════════════════════════════════════════════ */}
      <footer className="px-6 sm:px-12 pt-8 pb-6">
        {/* Inverted TAYSTE */}
        <div className="flex justify-center mb-6">
          <span
            className="text-[clamp(3rem,10vw,8rem)] font-extrabold tracking-tighter text-white/90 select-none"
            style={{ transform: "scaleY(-1)" }}
          >
            TAYSTE
          </span>
        </div>

        {/* Bottom bar */}
        <div className="flex items-center justify-between text-xs text-white/30 border-t border-white/10 pt-4">
          <span>Copyright &copy; {new Date().getFullYear()}</span>
          <span>PLTR Style Generic.</span>
        </div>
      </footer>
    </div>
  );
}
