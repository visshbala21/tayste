"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSignup(e: React.FormEvent) {
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
      const res = await fetch(`${API_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Signup failed");
      }

      router.push(`/verify-email?email=${encodeURIComponent(email)}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
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
        <p className="text-muted text-sm">AI-Powered A&R Intelligence</p>

        <div className="bg-surface border border-border rounded-2xl p-8 w-full max-w-sm flex flex-col items-center gap-6">
          <h1 className="text-xl font-semibold text-white">Create your account</h1>

          {error && (
            <div className="w-full text-sm text-red-400 bg-red-400/10 border border-red-400/20 rounded-lg px-4 py-2">
              {error}
            </div>
          )}

          <form onSubmit={handleSignup} className="w-full flex flex-col gap-4">
            <input
              type="text"
              placeholder="Full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-border text-white placeholder-muted text-sm focus:outline-none focus:border-primary/50"
            />
            <input
              type="email"
              placeholder="Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-border text-white placeholder-muted text-sm focus:outline-none focus:border-primary/50"
            />
            <input
              type="password"
              placeholder="Password (min 8 characters)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
              className="w-full px-4 py-3 rounded-xl bg-white/5 border border-border text-white placeholder-muted text-sm focus:outline-none focus:border-primary/50"
            />
            <input
              type="password"
              placeholder="Confirm password"
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
              {loading ? "Creating account..." : "Sign up"}
            </button>
          </form>

          <p className="text-sm text-muted">
            Already have an account?{" "}
            <Link href="/login" className="text-primary-light hover:text-primary transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
