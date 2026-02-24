import Link from "next/link";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <nav className="border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          <Link href="/" className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
            Tayste
          </Link>
          <div className="flex items-center gap-1 text-sm">
            <Link href="/dashboard" className="text-muted hover:text-gray-200 hover:bg-surface-light px-3 py-1.5 rounded-lg transition-all duration-200">
              Labels
            </Link>
            <Link href="/import" className="text-muted hover:text-gray-200 hover:bg-surface-light px-3 py-1.5 rounded-lg transition-all duration-200">
              Import
            </Link>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
    </>
  );
}
