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
    setSubmitted(true);
  }

  return (
    <div className="min-h-screen bg-background text-[#f5f5f0] font-body">
      {/* Nav */}
      <nav className="px-6 sm:px-12 py-6 flex items-center justify-between">
        <Link href="/" className="font-display text-[28px] tracking-[2px] text-[#f5f5f0]">
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
            className="inline-flex items-center rounded-pill px-5 py-2 text-xs bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200"
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
        <h1 className="font-display text-[clamp(48px,12vw,96px)] leading-none tracking-wide mb-6">
          REACH OUT
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
              <div className="border border-primary/20 rounded-lg p-10 bg-primary/[0.03] relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
                <h2 className="font-display text-[28px] tracking-wide mb-3">Message Sent</h2>
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
                  <input type="text" value={name} onChange={(e) => setName(e.target.value)} required placeholder="Your name" className="inp" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-white/60">Email</label>
                  <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com" className="inp" />
                </div>
                <div className="flex flex-col gap-1.5">
                  <label className="text-sm font-medium text-white/60">Message</label>
                  <textarea value={message} onChange={(e) => setMessage(e.target.value)} required rows={5} placeholder="How can we help?" className="inp resize-none min-h-[120px]" />
                </div>
                <button
                  type="submit"
                  className="w-full sm:w-auto inline-flex items-center justify-center rounded-pill px-8 py-3 text-sm bg-primary text-[#f5f5f0] hover:bg-accent2 transition-all duration-200 hover:-translate-y-px shadow-lg shadow-primary/20"
                >
                  Send Message
                </button>
              </form>
            )}
          </div>

          {/* Info cards */}
          <div className="flex flex-col gap-6 lg:pt-2">
            {[
              { title: "General Inquiries", desc: "For questions about the platform, features, or anything else \u2014 drop us a message through the form." },
              { title: "Partnerships", desc: "Interested in integrating Tayste into your label\u2019s workflow? We work with labels of all sizes." },
              { title: "Support", desc: "Having trouble with your account or the platform? We\u2019ll sort it out." },
            ].map((card) => (
              <div key={card.title} className="bg-surface border border-white/[0.12] rounded-lg p-6 relative overflow-hidden">
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-primary to-accent2" />
                <h3 className="font-display text-[18px] tracking-wide text-[#f5f5f0] mb-2">{card.title}</h3>
                <p className="text-white/40 text-sm leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-dashed border-white/[0.12] py-4 px-6 sm:px-12 flex justify-between text-[10px] text-white/30">
        <span>Copyright &copy; {new Date().getFullYear()}</span>
        <span>Tayste — AI A&R Intelligence</span>
      </footer>
    </div>
  );
}
