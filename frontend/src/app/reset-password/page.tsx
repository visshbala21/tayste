"use client";

import { useSearchParams } from "next/navigation";
import { useState, Suspense } from "react";
import Link from "next/link";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!token) {
    return (
      <div className="bg-surface border border-border rounded-2xl p-8 w-full max-w-sm flex flex-col items-center gap-6 text-center">
        <h1 className="text-xl font-semibold text-white">Invalid link</h1>
        <p className="text-sm text-muted">This password reset link is invalid or has expired.</p>
        <Link href="/forgot-password" className="text-sm text-primary-light hover:text-primary transition-colors">
          Request a new link
        </Link>
      </div>
    );
  }

  async function handleReset(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Reset failed");
      }

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  if (success) {
    return (
      <div className="bg-surface border border-border rounded-2xl p-8 w-full max-w-sm flex flex-col items-center gap-6 text-center">
        <div className="w-16 h-16 rounded-full bg-green-500/10 flex items-center justify-center">
          <svg className="w-8 h-8 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h1 className="text-xl font-semibold text-white">Password reset!</h1>
        <p className="text-sm text-muted">Your password has been reset successfully.</p>
        <Link
          href="/login"
          className="btn-glow bg-primary text-white font-medium px-6 py-3 rounded-xl hover:bg-primary/90 transition-colors"
        >
          Sign in
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-surface border border-border rounded-2xl p-8 w-full max-w-sm flex flex-col items-center gap-6">
      <h1 className="text-xl font-semibold text-white">Reset your password</h1>

      {error && (
        <div className="w-full text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-2">
          {error}
        </div>
      )}

      <form onSubmit={handleReset} className="w-full flex flex-col gap-4">
        <input
          type="password"
          placeholder="New password (min 8 characters)"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
          minLength={8}
          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-border text-white placeholder-muted text-sm focus:outline-none focus:border-primary/50"
        />
        <input
          type="password"
          placeholder="Confirm new password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          required
          className="w-full px-4 py-3 rounded-xl bg-white/5 border border-border text-white placeholder-muted text-sm focus:outline-none focus:border-primary/50"
        />
        <button
          type="submit"
          disabled={loading}
          className="w-full btn-glow bg-primary text-white font-medium px-6 py-3 rounded-xl hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {loading ? "Resetting..." : "Reset password"}
        </button>
      </form>
    </div>
  );
}

export default function ResetPasswordPage() {
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

        <Suspense fallback={
          <div className="w-8 h-8 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        }>
          <ResetPasswordContent />
        </Suspense>
      </div>
    </div>
  );
}
