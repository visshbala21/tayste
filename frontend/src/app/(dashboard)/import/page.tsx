import { ImportRosterClient } from "./client";

export const dynamic = "force-dynamic";

export default function ImportPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-white">Roster Import</h1>
        <p className="text-white/60">Paste any roster text and let the platform normalize it.</p>
      </div>
      <ImportRosterClient />
    </div>
  );
}
