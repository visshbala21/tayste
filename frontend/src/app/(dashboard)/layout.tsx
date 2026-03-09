import Link from "next/link";
import Image from "next/image";
import { createClient } from "@/lib/supabase/server";
import { redirect } from "next/navigation";
import { SignOutButton } from "./sign-out-button";
import "@/lib/api-server-init";

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const supabase = await createClient();
  const { data: { user } } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const name = user.user_metadata?.name || user.user_metadata?.full_name || null;
  const picture = user.user_metadata?.picture || user.user_metadata?.avatar_url || null;

  return (
    <div className="bg-[#050507] min-h-screen" style={{ fontFamily: 'Verdana, Geneva, sans-serif' }}>
      <nav className="border-b border-white/[0.06] bg-[#050507]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="text-xl font-extrabold tracking-tight text-white">
            TAYSTE
          </Link>
          <div className="flex items-center gap-1 text-sm">
            <Link href="/dashboard" className="text-white/50 hover:text-white hover:bg-white/[0.04] px-3 py-1.5 rounded-md transition-all duration-200">
              Labels
            </Link>
            <Link href="/import" className="text-white/50 hover:text-white hover:bg-white/[0.04] px-3 py-1.5 rounded-md transition-all duration-200">
              Import
            </Link>
          </div>
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
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
