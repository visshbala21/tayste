import "server-only";
import { createClient } from "@/lib/supabase/server";
import { _registerServerAuth } from "./api";

// Register server-side auth so api.ts can get tokens without importing next/headers
_registerServerAuth(async () => {
  try {
    const supabase = await createClient();
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token || null;
  } catch {
    return null;
  }
});
