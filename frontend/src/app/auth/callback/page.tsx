"use client";

import { createClient } from "@/lib/supabase/client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const supabase = createClient();

    // Supabase automatically picks up the auth code/tokens from the URL
    // and exchanges them using the same browser client that initiated the OAuth flow
    supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
        router.replace("/dashboard");
      }
    });

    // Fallback: if no auth event fires within 5s, redirect to login
    const timeout = setTimeout(() => {
      router.replace("/login?error=auth_callback_timeout");
    }, 5000);

    return () => clearTimeout(timeout);
  }, [router]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}
