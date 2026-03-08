"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* ── Shared components matching login page ─────────────────────── */

function DoodleOverlay() {
  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox="0 0 600 900"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="xMidYMid slice"
    >
      <g stroke="#8b5cf6" strokeWidth="3" strokeLinecap="round">
        <line x1="470" y1="80" x2="490" y2="100" />
        <line x1="490" y1="80" x2="470" y2="100" />
        <line x1="510" y1="60" x2="525" y2="75" />
        <line x1="525" y1="60" x2="510" y2="75" />
      </g>
      <path
        d="M480 680 C480 660, 510 640, 510 660 C510 640, 540 660, 540 680 C540 710, 510 730, 510 740 C510 730, 480 710, 480 680Z"
        stroke="#8b5cf6" strokeWidth="3" fill="none" strokeLinejoin="round"
      />
      <path
        d="M530 400 L540 370 L550 400 L580 410 L550 420 L540 450 L530 420 L500 410Z"
        stroke="#8b5cf6" strokeWidth="2.5" fill="none" strokeLinejoin="round"
      />
      <path
        d="M440 550 L445 535 L450 550 L465 555 L450 560 L445 575 L440 560 L425 555Z"
        stroke="#8b5cf6" strokeWidth="2" fill="none" strokeLinejoin="round"
      />
      <path
        d="M380 150 L385 138 L390 150 L402 155 L390 160 L385 172 L380 160 L368 155Z"
        stroke="#8b5cf6" strokeWidth="2" fill="none" strokeLinejoin="round"
      />
      <circle cx="350" cy="300" r="2" fill="#8b5cf6" opacity="0.7" />
      <circle cx="560" cy="250" r="2" fill="#8b5cf6" opacity="0.5" />
      <circle cx="420" cy="750" r="2.5" fill="#8b5cf6" opacity="0.6" />
      <circle cx="500" cy="500" r="1.5" fill="#8b5cf6" opacity="0.4" />
    </svg>
  );
}

function TaysteLogo() {
  return (
    <div className="flex items-center gap-2.5">
      <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
        <rect x="2" y="4" width="24" height="3.5" rx="1.5" fill="#8b5cf6" />
        <rect x="2" y="12" width="18" height="3.5" rx="1.5" fill="#8b5cf6" />
        <rect x="2" y="20" width="24" height="3.5" rx="1.5" fill="#8b5cf6" />
      </svg>
      <span className="text-[22px] font-extrabold tracking-tight text-gray-900">
        TAYSTE.
      </span>
    </div>
  );
}

/* ── Main page ─────────────────────────────────────────────────── */

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
    <div className="min-h-screen flex bg-white">
      {/* ── Left panel: form ─────────────────────────────────── */}
      <div className="w-full lg:w-[48%] flex flex-col justify-between px-8 sm:px-16 py-10">
        {/* Logo */}
        <Link href="/">
          <TaysteLogo />
        </Link>

        {/* Form area – vertically centred */}
        <div className="max-w-sm w-full mx-auto flex flex-col gap-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Create your account</h1>
            <p className="mt-2 text-sm text-gray-400">
              Start discovering your next signing
            </p>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
              {error}
            </div>
          )}

          <form onSubmit={handleSignup} className="flex flex-col gap-5">
            {/* Name */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700">
                Full name
              </label>
              <input
                type="text"
                placeholder="Enter your name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
              />
            </div>

            {/* Email */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700">
                Email address
              </label>
              <input
                type="email"
                placeholder="Enter your email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
              />
            </div>

            {/* Password */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700">
                Password
              </label>
              <input
                type="password"
                placeholder="Min 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
              />
            </div>

            {/* Confirm password */}
            <div className="flex flex-col gap-1.5">
              <label className="text-sm font-medium text-gray-700">
                Confirm password
              </label>
              <input
                type="password"
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
              />
            </div>

            {/* Sign up button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary text-white font-semibold py-2.5 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 shadow-sm"
            >
              {loading ? "Creating account..." : "Sign up"}
            </button>
          </form>

          {/* Sign in link */}
          <p className="text-sm text-gray-500 text-center">
            Already have an account?{" "}
            <Link
              href="/login"
              className="font-medium text-primary hover:text-primary-light transition-colors"
            >
              Sign in
            </Link>
          </p>
        </div>

        {/* Spacer to keep form centred */}
        <div />
      </div>

      {/* ── Right panel: hero image area ─────────────────────── */}
      <div className="hidden lg:block lg:w-[52%] relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-gray-950 via-gray-900 to-black" />
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-[70%] h-[75%]">
            <div
              className="absolute inset-0 rounded-2xl"
              style={{
                background:
                  "linear-gradient(160deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 40%, transparent 70%)",
              }}
            />
            <div className="absolute top-[10%] left-[20%] w-[60%] h-[35%] rounded-full bg-gradient-to-b from-white/10 to-transparent blur-sm" />
            <div className="absolute top-[40%] left-[15%] w-[70%] h-[50%] bg-gradient-to-b from-white/5 to-transparent rounded-t-3xl" />
            <div
              className="absolute top-[42%] left-[25%] w-[50%] h-[15%] rounded-full border border-white/10"
              style={{ borderRadius: "50%/30%" }}
            />
            <div
              className="absolute top-[45%] left-[22%] w-[56%] h-[15%] rounded-full border border-white/[0.06]"
              style={{ borderRadius: "50%/30%" }}
            />
          </div>
        </div>
        <div className="absolute top-1/4 right-1/4 w-64 h-64 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 left-1/3 w-48 h-48 bg-primary/5 rounded-full blur-3xl" />
        <DoodleOverlay />
      </div>
    </div>
  );
}
