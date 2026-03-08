import { auth } from "@/lib/auth";
import LandingClient from "./landing-client";

export default async function LandingPage() {
  let isLoggedIn = false;
  try {
    const session = await auth();
    isLoggedIn = !!session?.backendToken;
  } catch (error) {
    console.error("Auth check failed:", error);
    isLoggedIn = false;
  }

  return <LandingClient isLoggedIn={isLoggedIn} />;
}
