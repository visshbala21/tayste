"use client";

import { createClient } from "@/lib/supabase/client";
import { useState } from "react";
import Link from "next/link";

/* -- Inline SVG doodles for the hero panel ----------------------------- */

function DoodleOverlay() {
  return (
    <svg
      className="absolute inset-0 w-full h-full pointer-events-none"
      viewBox="0 0 600 900"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      preserveAspectRatio="xMidYMid slice"
    >
      {/* X marks -- top-right cluster */}
      <g stroke="#8b5cf6" strokeWidth="3" strokeLinecap="round">
        <line x1="470" y1="80" x2="490" y2="100" />
        <line x1="490" y1="80" x2="470" y2="100" />
        <line x1="510" y1="60" x2="525" y2="75" />
        <line x1="525" y1="60" x2="510" y2="75" />
      </g>

      {/* Heart -- lower-right */}
      <path
        d="M480 680 C480 660, 510 640, 510 660 C510 640, 540 660, 540 680 C540 710, 510 730, 510 740 C510 730, 480 710, 480 680Z"
        stroke="#8b5cf6"
        strokeWidth="3"
        fill="none"
        strokeLinejoin="round"
      />

      {/* 4-point star -- middle-right */}
      <path
        d="M530 400 L540 370 L550 400 L580 410 L550 420 L540 450 L530 420 L500 410Z"
        stroke="#8b5cf6"
        strokeWidth="2.5"
        fill="none"
        strokeLinejoin="round"
      />

      {/* Small 4-point star */}
      <path
        d="M440 550 L445 535 L450 550 L465 555 L450 560 L445 575 L440 560 L425 555Z"
        stroke="#8b5cf6"
        strokeWidth="2"
        fill="none"
        strokeLinejoin="round"
      />

      {/* Another small star top area */}
      <path
        d="M380 150 L385 138 L390 150 L402 155 L390 160 L385 172 L380 160 L368 155Z"
        stroke="#8b5cf6"
        strokeWidth="2"
        fill="none"
        strokeLinejoin="round"
      />

      {/* Sparkle dots */}
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
      {/* Stacked bars icon */}
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

function GoogleIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 24 24">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 01-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        fill="#EA4335"
      />
    </svg>
  );
}

/* -- Main page --------------------------------------------------------- */

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const supabase = createClient();

  async function handleCredentialsLogin(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const { error: authError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (authError) {
        setError(authError.message);
      } else {
        window.location.href = "/dashboard";
      }
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogleLogin() {
    await supabase.auth.signInWithOAuth({
      provider: "google",
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    });
  }

  return (
    <div className="min-h-screen flex bg-white">
      {/* -- Left panel: form ----------------------------------------- */}
      <div className="w-full lg:w-[48%] flex flex-col justify-between px-8 sm:px-16 py-10">
        {/* Logo */}
        <Link href="/">
          <TaysteLogo />
        </Link>

        {/* Form area -- vertically centred */}
        <div className="max-w-sm w-full mx-auto flex flex-col gap-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Welcome back</h1>
            <p className="mt-2 text-sm text-gray-400">
              Please enter your details
            </p>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-2">
              {error}
            </div>
          )}

          <form
            onSubmit={handleCredentialsLogin}
            className="flex flex-col gap-5"
          >
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
                placeholder="--------"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-gray-900 placeholder-gray-400 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary transition-colors"
              />
            </div>

            {/* Remember / Forgot */}
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(e) => setRemember(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary/30 accent-primary"
                />
                <span className="text-sm text-gray-600">
                  Remember for 30 days
                </span>
              </label>
              <Link
                href="/forgot-password"
                className="text-sm font-medium text-primary hover:text-primary-light transition-colors"
              >
                Forgot password
              </Link>
            </div>

            {/* Sign in button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full bg-primary text-white font-semibold py-2.5 rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50 shadow-sm"
            >
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          {/* Google */}
          <button
            onClick={handleGoogleLogin}
            className="w-full flex items-center justify-center gap-3 border border-gray-300 text-gray-700 font-medium py-2.5 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <GoogleIcon />
            Sign in with Google
          </button>

          {/* Sign up link */}
          <p className="text-sm text-gray-500 text-center">
            Don&apos;t have an account?{" "}
            <Link
              href="/signup"
              className="font-medium text-primary hover:text-primary-light transition-colors"
            >
              Sign up
            </Link>
          </p>
        </div>

        {/* Spacer to keep form centred */}
        <div />
      </div>

      {/* -- Right panel: hero image area ----------------------------- */}
      <div className="hidden lg:block lg:w-[52%] relative overflow-hidden">
        {/* Dark gradient base */}
        <div className="absolute inset-0 bg-gradient-to-br from-gray-950 via-gray-900 to-black" />

        {/* Subtle texture overlay */}
        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "radial-gradient(circle at 1px 1px, white 1px, transparent 0)",
            backgroundSize: "32px 32px",
          }}
        />

        {/* Artistic silhouette -- gradient shape */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="relative w-[70%] h-[75%]">
            {/* Main figure silhouette using layered gradients */}
            <div
              className="absolute inset-0 rounded-2xl"
              style={{
                background:
                  "linear-gradient(160deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 40%, transparent 70%)",
              }}
            />
            {/* High-contrast artistic shapes mimicking portrait */}
            <div className="absolute top-[10%] left-[20%] w-[60%] h-[35%] rounded-full bg-gradient-to-b from-white/10 to-transparent blur-sm" />
            <div className="absolute top-[40%] left-[15%] w-[70%] h-[50%] bg-gradient-to-b from-white/5 to-transparent rounded-t-3xl" />
            {/* Chain/necklace detail */}
            <div
              className="absolute top-[42%] left-[25%] w-[50%] h-[15%] rounded-full border border-white/10"
              style={{
                borderRadius: "50%/30%",
              }}
            />
            <div
              className="absolute top-[45%] left-[22%] w-[56%] h-[15%] rounded-full border border-white/[0.06]"
              style={{
                borderRadius: "50%/30%",
              }}
            />
          </div>
        </div>

        {/* Purple glow accent */}
        <div className="absolute top-1/4 right-1/4 w-64 h-64 bg-primary/10 rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 left-1/3 w-48 h-48 bg-primary/5 rounded-full blur-3xl" />

        {/* SVG Doodles */}
        <DoodleOverlay />
      </div>
    </div>
  );
}
