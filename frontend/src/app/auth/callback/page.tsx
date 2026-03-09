"use client";

import { Suspense } from "react";
import { createClient } from "@/lib/supabase/client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function AuthCallbackInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get("next") || "/dashboard";

  useEffect(() => {
    const supabase = createClient();

    // Supabase automatically picks up the auth code/tokens from the URL
    // and exchanges them using the same browser client that initiated the OAuth flow
    supabase.auth.onAuthStateChange((event) => {
      if (event === "SIGNED_IN" || event === "TOKEN_REFRESHED") {
        router.replace(redirectTo);
      }
    });

    // Fallback: if no auth event fires within 5s, redirect to login
    const timeout = setTimeout(() => {
      router.replace("/login?error=auth_callback_timeout");
    }, 5000);

    return () => clearTimeout(timeout);
  }, [router, redirectTo]);

  return (
    <div className="min-h-screen bg-black flex items-center justify-center">
      <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-black flex items-center justify-center">
          <div className="w-8 h-8 border-2 border-purple-500 border-t-transparent rounded-full animate-spin" />
        </div>
      }
    >
      <AuthCallbackInner />
    </Suspense>
  );
}
