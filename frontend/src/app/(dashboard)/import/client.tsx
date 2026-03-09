"use client";

import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { api, RosterImportResult, ResolvedArtistProfile } from "@/lib/api";
import Link from "next/link";

type Status = "idle" | "loading" | "success" | "error";
type ImportTab = "simple" | "advanced";

type AdditionalPlatform = {
  platform: string;
  platform_id?: string;
  platform_url?: string;
};

type EditableEntry = {
  name: string;
  platform?: string;
  platform_id?: string;
  platform_url?: string;
  genre_tags?: string[];
  additional_platforms?: AdditionalPlatform[];
  include: boolean;
  genre_input: string;
};

// ---------- Simple Import ----------

function SimpleImport() {
  const [labelName, setLabelName] = useState("");
  const [artistText, setArtistText] = useState("");
  const [runPipeline, setRunPipeline] = useState(true);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<"input" | "preview" | "done">("input");
  const [resolved, setResolved] = useState<(ResolvedArtistProfile & { include: boolean })[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [result, setResult] = useState<RosterImportResult | null>(null);

  const onResolve = async (e: FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setError(null);

    try {
      const names = artistText
        .split("\n")
        .map((l) => l.trim())
        .filter(Boolean);

      const res = await api.simpleImportResolve(labelName.trim(), names);
      setResolved(res.artists.map((a) => ({ ...a, include: true })));
      setWarnings(res.warnings);
      setStep("preview");
      setStatus("success");
    } catch (err: any) {
      setStatus("error");
      setError(err?.message || "Resolution failed");
    }
  };

  const onConfirm = async () => {
    setStatus("loading");
    setError(null);

    try {
      const artists = resolved
        .filter((a) => a.include)
        .map(({ include, ...rest }) => rest);

      const res = await api.simpleImportConfirm(labelName.trim(), artists, runPipeline);
      setResult(res);
      setStep("done");
      setStatus("success");
    } catch (err: any) {
      setStatus("error");
      setError(err?.message || "Import failed");
    }
  };

  const formatFollowers = (n?: number) => {
    if (!n) return null;
    if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
    return String(n);
  };

  const disabled = !labelName.trim() || !artistText.trim() || status === "loading";

  return (
    <div className="grid gap-6">
      {step === "input" && (
        <form onSubmit={onResolve} className="grid gap-4">
          <div className="grid gap-2">
            <label className="text-sm text-white/35">Label Name</label>
            <input
              className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30"
              value={labelName}
              onChange={(e) => setLabelName(e.target.value)}
              placeholder="Neon Dusk Records"
            />
          </div>

          <div className="grid gap-2">
            <label className="text-sm text-white/35">Artist Names</label>
            <textarea
              className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 min-h-[12rem] text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30"
              value={artistText}
              onChange={(e) => setArtistText(e.target.value)}
              placeholder={"One artist per line, e.g.:\n\nTame Impala\nMen I Trust\nBeabadoobee\nClairo\nBoy Pablo"}
            />
          </div>

          <div className="flex items-center gap-3">
            <input
              id="simple-run-pipeline"
              type="checkbox"
              checked={runPipeline}
              onChange={(e) => setRunPipeline(e.target.checked)}
            />
            <label htmlFor="simple-run-pipeline" className="text-sm text-white/60">
              Run discovery pipeline after import
            </label>
          </div>

          <button
            type="submit"
            className="bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-lg px-4 py-2 hover:bg-purple-500/15 transition disabled:opacity-50"
            disabled={disabled}
          >
            {status === "loading" ? (
              <span className="flex items-center gap-2 justify-center">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Resolving artists...
              </span>
            ) : (
              "Resolve Artists"
            )}
          </button>
        </form>
      )}

      {step === "preview" && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Resolved Artists</h3>
              <p className="text-sm text-white/40">
                {resolved.filter((a) => a.include).length} of {resolved.length} selected
              </p>
            </div>
            <button
              type="button"
              className="text-sm text-white/40 hover:text-white/60 transition px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05]"
              onClick={() => setStep("input")}
            >
              Back
            </button>
          </div>

          {warnings.length > 0 && (
            <div className="mb-4 bg-yellow-500/5 border border-yellow-500/20 rounded-lg p-3">
              <ul className="list-disc pl-5 text-sm text-yellow-300/80">
                {warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {resolved.map((artist, idx) => (
              <div
                key={idx}
                className={`relative border rounded-xl p-4 transition cursor-pointer ${
                  artist.include
                    ? "border-purple-500/30 bg-white/[0.04]"
                    : "border-white/[0.06] bg-white/[0.01] opacity-50"
                }`}
                onClick={() => {
                  const next = [...resolved];
                  next[idx] = { ...artist, include: !artist.include };
                  setResolved(next);
                }}
              >
                <div className="flex items-start gap-3">
                  {artist.image_url ? (
                    <img
                      src={artist.image_url}
                      alt={artist.name}
                      className="w-12 h-12 rounded-full object-cover flex-shrink-0"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-full bg-white/[0.06] flex items-center justify-center flex-shrink-0">
                      <span className="text-white/20 text-lg">?</span>
                    </div>
                  )}
                  <div className="min-w-0 flex-1">
                    <div className="font-medium text-white truncate">{artist.name}</div>
                    {artist.query_name !== artist.name && (
                      <div className="text-xs text-white/30 truncate">searched: {artist.query_name}</div>
                    )}
                    {artist.spotify_followers && (
                      <div className="text-xs text-white/40 mt-0.5">
                        {formatFollowers(artist.spotify_followers)} Spotify followers
                      </div>
                    )}
                  </div>
                  <input
                    type="checkbox"
                    checked={artist.include}
                    onChange={() => {}}
                    className="flex-shrink-0 mt-1"
                  />
                </div>

                {artist.genres && artist.genres.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {artist.genres.slice(0, 4).map((g, gi) => (
                      <span
                        key={gi}
                        className="text-[10px] px-1.5 py-0.5 rounded-full bg-white/[0.06] text-white/50"
                      >
                        {g}
                      </span>
                    ))}
                  </div>
                )}

                <div className="flex gap-2 mt-2">
                  {artist.spotify?.platform_id && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-500/10 text-green-400/70">Spotify</span>
                  )}
                  {artist.youtube?.platform_id && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/10 text-red-400/70">YouTube</span>
                  )}
                  {artist.soundcharts?.platform_id && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400/70">Soundcharts</span>
                  )}
                  {!artist.resolved && (
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-orange-500/10 text-orange-400/70">Unresolved</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-6 flex gap-3">
            <button
              type="button"
              className="bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-lg px-4 py-2 hover:bg-purple-500/15 transition disabled:opacity-50"
              onClick={onConfirm}
              disabled={status === "loading" || resolved.filter((a) => a.include).length === 0}
            >
              {status === "loading" ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Importing...
                </span>
              ) : (
                `Confirm Import (${resolved.filter((a) => a.include).length} artists)`
              )}
            </button>
          </div>
        </div>
      )}

      {step === "done" && result && (
        <div className="bg-white/[0.04] border border-white/[0.06] rounded-xl p-5">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-5 h-5 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            <span className="font-semibold text-white">Import Complete</span>
          </div>
          <div className="text-sm text-white/60 space-y-1">
            <p>Created {result.created_count} artists for <span className="text-white/80">{result.label_name}</span></p>
            {result.skipped_count > 0 && <p>Skipped {result.skipped_count} (already existed)</p>}
            {runPipeline && <p className="text-xs text-white/40">Discovery pipeline queued.</p>}
          </div>
          {result.label_id && (
            <Link
              href={`/labels/${result.label_id}`}
              className="inline-block mt-4 text-sm text-purple-300 hover:text-purple-200 transition"
            >
              Go to Dashboard →
            </Link>
          )}
        </div>
      )}

      {status === "error" && <div className="text-sm text-red-400">{error}</div>}
    </div>
  );
}

// ---------- Advanced Import (existing form) ----------

function AdvancedImport() {
  const sampleJson = `Sample JSON (multi-platform):
{
  "artists": [
    {
      "name": "Velvet Collapse",
      "platform": "youtube",
      "platform_id": "UCxxxxxxxxxxxxxxxxxxxx",
      "platform_url": "https://youtube.com/channel/UCxxxxxxxxxxxxxxxxxxxx",
      "genre_tags": ["indie-rock", "shoegaze"]
    },
    {
      "name": "Pale Meridian",
      "platform": "spotify",
      "platform_id": "4Z8W30Rd5zhGzSmJmGK7gc",
      "platform_url": "https://open.spotify.com/artist/4Z8W30Rd5zhGzSmJmGK7gc",
      "genre_tags": ["dream-pop", "ambient"]
    }
  ]
}`;
  const [labelName, setLabelName] = useState("");
  const [description, setDescription] = useState("");
  const [primaryGenres, setPrimaryGenres] = useState("");
  const [rawText, setRawText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [runPipeline, setRunPipeline] = useState(true);
  const [resolveMissing, setResolveMissing] = useState(true);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RosterImportResult | null>(null);
  const [entries, setEntries] = useState<EditableEntry[]>([]);
  const [step, setStep] = useState<"input" | "review" | "done">("input");

  const toEditable = (parsed: RosterImportResult["parsed"]) =>
    parsed.map((p) => ({
      ...p,
      include: true,
      genre_input: (p.genre_tags || []).join(", "),
    }));

  const onPreview = async (e: FormEvent) => {
    e.preventDefault();
    setStatus("loading");
    setError(null);
    setResult(null);
    setEntries([]);

    try {
      const genres = primaryGenres
        .split(",")
        .map((g) => g.trim())
        .filter(Boolean);

      const base = {
        label: {
          name: labelName.trim(),
          description: description.trim() || undefined,
          genre_tags: genres.length ? { primary: genres } : undefined,
        },
        resolve_missing: resolveMissing,
        run_pipeline: false,
        dry_run: true,
      };

      const res = file
        ? await api.importRosterFile({
            ...base,
            file,
          })
        : await api.importRoster({
            ...base,
            raw_text: rawText,
          });
      setResult(res);
      setEntries(toEditable(res.parsed));
      setStep("review");
      setStatus("success");
    } catch (err: any) {
      setStatus("error");
      setError(err?.message || "Import failed");
    }
  };

  const onConfirm = async () => {
    setStatus("loading");
    setError(null);
    try {
      const genres = primaryGenres
        .split(",")
        .map((g) => g.trim())
        .filter(Boolean);

      const artists = entries
        .filter((e) => e.include && e.name.trim())
        .map((e) => ({
          name: e.name.trim(),
          platform: e.platform,
          platform_id: e.platform_id || undefined,
          platform_url: e.platform_url || undefined,
          genre_tags: e.genre_input
            .split(",")
            .map((g) => g.trim())
            .filter(Boolean),
          additional_platforms: e.additional_platforms || undefined,
        }));

      const res = await api.importRosterConfirm({
        label: {
          name: labelName.trim(),
          description: description.trim() || undefined,
          genre_tags: genres.length ? { primary: genres } : undefined,
        },
        artists,
        run_pipeline: runPipeline,
      });
      setResult(res);
      setStep("done");
      setStatus("success");
    } catch (err: any) {
      setStatus("error");
      setError(err?.message || "Import failed");
    }
  };

  const onFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFile(file);
    const lower = file.name.toLowerCase();
    if (lower.endsWith(".pdf") || lower.endsWith(".xlsx")) {
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const text = typeof reader.result === "string" ? reader.result : "";
      if (text) {
        setRawText(text);
      }
    };
    reader.readAsText(file);
  };

  const disabled = !labelName.trim() || (!rawText.trim() && !file) || status === "loading";

  return (
    <div>
      <form onSubmit={onPreview} className="grid gap-4">
        <div className="grid gap-2">
          <label className="text-sm text-white/35">Label Name</label>
          <input
            className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30"
            value={labelName}
            onChange={(e) => setLabelName(e.target.value)}
            placeholder="Neon Dusk Records"
          />
        </div>

        <div className="grid gap-2">
          <label className="text-sm text-white/35">Label Description (optional)</label>
          <input
            className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Atmospheric, guitar-driven indie..."
          />
        </div>

        <div className="grid gap-2">
          <label className="text-sm text-white/35">Primary Genres (comma-separated)</label>
          <input
            className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30"
            value={primaryGenres}
            onChange={(e) => setPrimaryGenres(e.target.value)}
            placeholder="dream-pop, post-punk, ambient"
          />
        </div>

        <div className="grid gap-2">
          <label className="text-sm text-white/35">Roster Text</label>
          <textarea
            className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-3 py-2 min-h-[24rem] text-white/80 placeholder-white/25 focus:outline-none focus:border-purple-500/30"
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder={`${sampleJson}\n\nFreeform examples:\nVelvet Collapse - https://youtube.com/channel/UC...\nPale Meridian - https://open.spotify.com/artist/4Z8W30...\nGhost Antenna (post-punk, darkwave)\n@duskprotocol https://youtube.com/@duskprotocol`}
          />
          <input
            type="file"
            accept=".txt,.csv,.tsv,.json,.xlsx,.pdf"
            onChange={onFileChange}
            className="text-sm text-white/35"
          />
          {file && (
            <div className="text-xs text-white/35">Using file: {file.name} (file takes precedence over pasted text)</div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <input
            id="resolve-missing"
            type="checkbox"
            checked={resolveMissing}
            onChange={(e) => setResolveMissing(e.target.checked)}
          />
          <label htmlFor="resolve-missing" className="text-sm text-white/60">
            Resolve missing YouTube IDs by search
          </label>
        </div>

        <div className="flex items-center gap-3">
          <input
            id="run-pipeline"
            type="checkbox"
            checked={runPipeline}
            onChange={(e) => setRunPipeline(e.target.checked)}
          />
          <label htmlFor="run-pipeline" className="text-sm text-white/60">
            Run discovery pipeline after import
          </label>
        </div>

        {step === "input" && (
          <button
            type="submit"
            className="bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-lg px-4 py-2 hover:bg-purple-500/15 transition disabled:opacity-50"
            disabled={disabled}
          >
            {status === "loading" ? "Parsing..." : "Preview Parse"}
          </button>
        )}
      </form>

      {status === "error" && (
        <div className="mt-4 text-sm text-red-400">{error}</div>
      )}

      {step === "review" && result && (
        <div className="mt-6 bg-white/[0.04] border border-white/[0.06] rounded-xl p-4 text-sm">
          <div className="font-bold mb-2 text-white">Review Parsed Roster</div>
          <div className="text-white/60 mb-2">
            Parsed {result.parsed_count} entries. Review and confirm before importing.
          </div>
          {result.warnings?.length > 0 && (
            <div className="mt-3">
              <div className="font-bold text-white">Warnings</div>
              <ul className="list-disc pl-5 text-white/60">
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 grid gap-3">
            {entries.map((entry, idx) => (
              <div key={idx} className="grid gap-2 border border-white/[0.06] rounded-xl p-3">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={entry.include}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, include: e.target.checked };
                      setEntries(next);
                    }}
                  />
                  <input
                    className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-2 py-1 flex-1 text-white/80 focus:outline-none focus:border-purple-500/30"
                    value={entry.name}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, name: e.target.value };
                      setEntries(next);
                    }}
                    placeholder="Artist name"
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  <input
                    className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-2 py-1 text-white/80 focus:outline-none focus:border-purple-500/30"
                    value={entry.platform || ""}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, platform: e.target.value };
                      setEntries(next);
                    }}
                    placeholder="platform (youtube)"
                  />
                  <input
                    className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-2 py-1 text-white/80 focus:outline-none focus:border-purple-500/30"
                    value={entry.platform_id || ""}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, platform_id: e.target.value };
                      setEntries(next);
                    }}
                    placeholder="platform_id (UC...)"
                  />
                  <input
                    className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-2 py-1 md:col-span-2 text-white/80 focus:outline-none focus:border-purple-500/30"
                    value={entry.platform_url || ""}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, platform_url: e.target.value };
                      setEntries(next);
                    }}
                    placeholder="platform_url"
                  />
                  {entry.additional_platforms && entry.additional_platforms.length > 0 && (
                    entry.additional_platforms.map((ap, apIdx) => (
                      <div key={apIdx} className="md:col-span-2 flex items-center gap-2 text-xs text-white/35 bg-white/[0.03] border border-white/[0.06] rounded-lg px-2 py-1.5">
                        <span className="text-white/60 font-medium">{ap.platform}</span>
                        {ap.platform_id && <span className="truncate">{ap.platform_id}</span>}
                        {ap.platform_url && <span className="truncate opacity-70">{ap.platform_url}</span>}
                      </div>
                    ))
                  )}
                  <input
                    className="bg-white/[0.03] border border-white/[0.08] rounded-lg px-2 py-1 md:col-span-2 text-white/80 focus:outline-none focus:border-purple-500/30"
                    value={entry.genre_input}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, genre_input: e.target.value };
                      setEntries(next);
                    }}
                    placeholder="genres (comma-separated)"
                  />
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 flex gap-3">
            <button
              type="button"
              className="bg-white/[0.03] border border-white/[0.06] rounded-lg px-4 py-2 text-white/40 hover:bg-white/[0.05]"
              onClick={() => setStep("input")}
            >
              Back
            </button>
            <button
              type="button"
              className="bg-purple-500/10 text-purple-300 border border-purple-500/20 rounded-lg px-4 py-2 hover:bg-purple-500/15 transition disabled:opacity-50"
              onClick={onConfirm}
              disabled={status === "loading"}
            >
              {status === "loading" ? "Importing..." : "Confirm Import"}
            </button>
          </div>
        </div>
      )}

      {step === "done" && result && (
        <div className="mt-6 bg-white/[0.04] border border-white/[0.06] rounded-xl p-4 text-sm">
          <div className="font-bold mb-2 text-white">Import Complete</div>
          <div className="text-white/60 mb-2">
            Parsed {result.parsed_count} entries, created {result.created_count}, skipped {result.skipped_count}.
          </div>
          {runPipeline && (
            <div className="mb-2 text-xs text-white/60">
              Pipeline queued. You can follow status on the dashboard.
            </div>
          )}
          {result.label_id && (
            <div className="text-white/60">
              Label ID: <span className="text-white/60">{result.label_id}</span>
            </div>
          )}
          {result.warnings?.length > 0 && (
            <div className="mt-3">
              <div className="font-bold text-white">Warnings</div>
              <ul className="list-disc pl-5 text-white/60">
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------- Main Component ----------

export function ImportRosterClient() {
  const [tab, setTab] = useState<ImportTab>("simple");

  return (
    <div className="bg-white/[0.02] border border-white/[0.06] rounded-xl p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">Import Roster</h2>
        <Link
          href="/dashboard"
          className="text-sm text-white/40 hover:text-white/60 transition px-3 py-1.5 rounded-lg bg-white/[0.03] border border-white/[0.06] hover:bg-white/[0.05]"
        >
          Back to Dashboard
        </Link>
      </div>

      {/* Tab Switcher */}
      <div className="flex gap-1 mb-6 bg-white/[0.03] rounded-lg p-1 w-fit">
        <button
          className={`px-4 py-1.5 rounded-md text-sm transition ${
            tab === "simple"
              ? "bg-purple-500/15 text-purple-300 border border-purple-500/20"
              : "text-white/40 hover:text-white/60"
          }`}
          onClick={() => setTab("simple")}
        >
          Simple
        </button>
        <button
          className={`px-4 py-1.5 rounded-md text-sm transition ${
            tab === "advanced"
              ? "bg-purple-500/15 text-purple-300 border border-purple-500/20"
              : "text-white/40 hover:text-white/60"
          }`}
          onClick={() => setTab("advanced")}
        >
          Advanced
        </button>
      </div>

      {tab === "simple" ? (
        <>
          <p className="text-white/60 mb-6">
            Type your label name and paste artist names — we&apos;ll auto-resolve their Spotify, YouTube, and Soundcharts profiles.
          </p>
          <SimpleImport />
        </>
      ) : (
        <>
          <p className="text-white/60 mb-6">
            Paste raw roster text or upload a file (PDF, XLSX, CSV, JSON). We will parse it with an LLM,
            resolve missing YouTube IDs, and optionally run the discovery pipeline.
          </p>
          <AdvancedImport />
        </>
      )}
    </div>
  );
}
