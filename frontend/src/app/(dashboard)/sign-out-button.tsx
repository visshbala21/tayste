"use client";

import { createClient } from "@/lib/supabase/client";
import { useRouter } from "next/navigation";

export function SignOutButton() {
  const router = useRouter();
  const supabase = createClient();

  async function handleSignOut() {
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  }

  return (
    <button
      onClick={handleSignOut}
      className="text-xs text-white/40 hover:text-white/70 border border-white/[0.08] px-3 py-1.5 rounded-md transition-all duration-200 hover:border-white/15"
    >
      Sign out
    </button>
  );
}
