import Link from "next/link";
import Image from "next/image";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { headers } from "next/headers";
import { SignOutButton } from "./sign-out-button";
import { NavBar } from "@/components/nav-bar";
import { LabelProvider } from "@/lib/label-context";
import { api } from "@/lib/api";
import "@/lib/api-server-init";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    // Preserve the current path so login can redirect back
    const headersList = await headers();
    const url = headersList.get("x-next-url") || headersList.get("x-invoke-path") || "";
    const next = url && url !== "/dashboard" ? `?next=${encodeURIComponent(url)}` : "";
    redirect(`/login${next}`);
  }

  const name = user.user_metadata?.name || user.user_metadata?.full_name || null;
  const picture = user.user_metadata?.picture || user.user_metadata?.avatar_url || null;

  // Fetch labels to determine active label for nav
  let activeLabelId: string | null = null;
  try {
    const labels = await api.getLabels();
    if (labels.length > 0) {
      activeLabelId = labels[0].id;
    }
  } catch {
    // API not available
  }

  return (
    <LabelProvider activeLabelId={activeLabelId}>
      <div className="bg-background min-h-screen font-body">
        <nav className="flex items-center justify-between px-6 h-[54px] bg-[rgba(10,10,10,0.92)] border-b border-white/[0.12] sticky top-0 z-50 backdrop-blur-xl">
          <Link
            href="/dashboard"
            className="font-display text-[28px] tracking-[2px] text-[#f5f5f0] leading-none"
          >
            TAYSTE
          </Link>

          <NavBar />

          <div className="flex items-center gap-3">
            {picture && (
              <Image
                src={picture}
                alt={name || "User"}
                width={28}
                height={28}
                className="rounded-full ring-1 ring-white/10"
              />
            )}
            {name && (
              <span className="text-sm text-white/40 hidden sm:inline">{name}</span>
            )}
            <SignOutButton />
          </div>
        </nav>
        <main className="max-w-7xl mx-auto px-6 py-8 page-fade">{children}</main>
      </div>
    </LabelProvider>
  );
}
