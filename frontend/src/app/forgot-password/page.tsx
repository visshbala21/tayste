"use client";

import { createClient } from "@/lib/supabase/client";
import { useState } from "react";
import Link from "next/link";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  const supabase = createClient();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);

    try {
      await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });
      setSent(true);
    } catch {
      // Always show success to prevent email enumeration
      setSent(true);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen grid-bg flex flex-col items-center justify-center relative">
      <div className="fixed inset-0 glow-top-left pointer-events-none" />
      <div className="fixed inset-0 glow-bottom-right pointer-events-none" />

      <div className="relative z-10 flex flex-col items-center gap-8">
        <Link href="/">
          <span className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Tayste
          </span>
        </Link>

        <div className="bg-surface border border-border rounded-2xl p-8 w-full max-w-sm flex flex-col items-center gap-6 text-center">
          {!sent ? (
            <>
              <h1 className="text-xl font-semibold text-white">Forgot password?</h1>
              <p className="text-sm text-muted">
                Enter your email and we&apos;ll send you a link to reset your password.
              </p>
              <form onSubmit={handleSubmit} className="w-full flex flex-col gap-4">
                <input
                  type="email"
                  placeholder="Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full px-4 py-3 rounded-xl bg-white/5 border border-border text-white placeholder-muted text-sm focus:outline-none focus:border-primary/50"
                />
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full btn-glow bg-primary text-white font-medium px-6 py-3 rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50"
                >
                  {loading ? "Sending..." : "Send reset link"}
                </button>
              </form>
            </>
          ) : (
            <>
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center">
                <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
                </svg>
              </div>
              <h1 className="text-xl font-semibold text-white">Check your email</h1>
              <p className="text-sm text-muted">
                If an account exists for <span className="text-white">{email}</span>, we&apos;ve sent a password reset link.
              </p>
            </>
          )}

          <Link href="/login" className="text-sm text-primary-light hover:text-primary transition-colors">
            Back to sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
