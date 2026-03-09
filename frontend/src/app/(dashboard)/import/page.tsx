import { ImportRosterClient } from "./client";

export const dynamic = "force-dynamic";

export default function ImportPage() {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-2 text-white">Roster Import</h1>
        <p className="text-white/60">Import your roster by typing artist names or pasting structured data.</p>
      </div>
      <ImportRosterClient />
    </div>
  );
}
