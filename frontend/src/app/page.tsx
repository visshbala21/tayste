import { createClient } from "@/lib/supabase/server";
import LandingClient from "./landing-client";

export const dynamic = "force-dynamic";

export default async function LandingPage() {
  let isLoggedIn = false;
  try {
    const supabase = await createClient();
    const { data: { user } } = await supabase.auth.getUser();
    isLoggedIn = !!user;
  } catch (error) {
    console.error("Auth check failed:", error);
    isLoggedIn = false;
  }

  return <LandingClient isLoggedIn={isLoggedIn} />;
}
