import { ImportRosterClient } from "./client";

export const dynamic = "force-dynamic";

export default function ImportPage() {
  return (
    <div className="page-fade">
      <div className="mb-6">
        <h1 className="font-display text-[clamp(36px,8vw,72px)] leading-none tracking-wide text-[#f5f5f0]">
          ROSTER IMPORT
        </h1>
        <p className="text-white/45 mt-2 italic text-sm">
          Import your roster by typing artist names or pasting structured data.
        </p>
      </div>
      <ImportRosterClient />
    </div>
  );
}
