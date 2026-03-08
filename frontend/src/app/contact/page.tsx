"use client";

import Link from "next/link";
import { useState } from "react";

export default function ContactPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    // For now, just show confirmation — wire to backend later
    setSubmitted(true);
  }

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
          <Link href="/about" className="text-sm text-white/60 hover:text-white transition-colors">
            About
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
          Get in Touch
        </p>
        <h1
          className="text-4xl sm:text-6xl font-extrabold tracking-tight leading-[1.05] mb-6"
          style={{ fontFamily: "Verdana, Geneva, sans-serif" }}
        >
          Contact
        </h1>
        <p className="text-white/50 text-lg max-w-2xl leading-relaxed">
          Questions, feedback, or partnership inquiries — we&apos;d love to hear from you.
        </p>
      </section>

      {/* Form + Info */}
      <section className="px-6 sm:px-12 pb-24 max-w-5xl">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
          {/* Contact form */}
          <div>
            {submitted ? (
              <div className="border border-primary/20 rounded-2xl p-10 bg-primary/[0.03]">
                <h2 className="text-2xl font-bold mb-3">Message sent</h2>
                <p className="text-white/50 mb-6">
                  Thanks for reaching out. We&apos;ll get back to you soon.
                </p>
                <button
                  onClick={() => {
                    setSubmitted(false);
                    setName("");
                    setEmail("");
                    setMessage("");
                  }}
                  className="text-sm text-primary hover:text-primary-light transition-colors"
                >
                  Send another message
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="flex flex-col gap-5">
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-white/60">Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    required
                    placeholder="Your name"
                    className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/30 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-white/60">Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    placeholder="you@example.com"
                    className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/30 text-sm focus:outline-none focus:border-primary/50 transition-colors"
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-white/60">Message</label>
                  <textarea
                    value={message}
                    onChange={(e) => setMessage(e.target.value)}
                    required
                    rows={5}
                    placeholder="How can we help?"
                    className="w-full px-4 py-3 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/30 text-sm focus:outline-none focus:border-primary/50 transition-colors resize-none"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full sm:w-auto px-8 py-3 rounded-lg bg-primary text-white font-semibold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20"
                >
                  Send Message
                </button>
              </form>
            )}
          </div>

          {/* Info cards */}
          <div className="flex flex-col gap-6 lg:pt-2">
            <div className="border border-white/10 rounded-xl p-6 bg-white/[0.02]">
              <h3 className="text-white font-semibold mb-2">General Inquiries</h3>
              <p className="text-white/40 text-sm leading-relaxed">
                For questions about the platform, features, or anything else — drop us a
                message through the form.
              </p>
            </div>
            <div className="border border-white/10 rounded-xl p-6 bg-white/[0.02]">
              <h3 className="text-white font-semibold mb-2">Partnerships</h3>
              <p className="text-white/40 text-sm leading-relaxed">
                Interested in integrating Tayste into your label&apos;s workflow? We work
                with labels of all sizes.
              </p>
            </div>
            <div className="border border-white/10 rounded-xl p-6 bg-white/[0.02]">
              <h3 className="text-white font-semibold mb-2">Support</h3>
              <p className="text-white/40 text-sm leading-relaxed">
                Having trouble with your account or the platform? We&apos;ll sort it out.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-white/10 py-6 px-6 sm:px-12 text-sm text-white/30">
        Tayste — AI A&R Intelligence
      </footer>
    </div>
  );
}
