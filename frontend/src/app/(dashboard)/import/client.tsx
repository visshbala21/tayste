"use client";

import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { api, RosterImportResult } from "@/lib/api";
import Link from "next/link";

type Status = "idle" | "loading" | "success" | "error";

type EditableEntry = {
  name: string;
  platform?: string;
  platform_id?: string;
  platform_url?: string;
  genre_tags?: string[];
  include: boolean;
  genre_input: string;
};

export function ImportRosterClient() {
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
    <div className="bg-surface border border-border rounded-lg p-6 animate-bounce-in">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">Import Roster</h2>
        <Link
          href="/dashboard"
          className="text-sm text-primary hover:text-primary-light transition px-3 py-1.5 rounded bg-primary/10"
        >
          Back to Dashboard
        </Link>
      </div>
      <p className="text-muted mb-6">
        Paste raw roster text or upload a file (PDF, XLSX, CSV, JSON). We will parse it with an LLM,
        resolve missing YouTube IDs, and optionally run the discovery pipeline.
      </p>

      <form onSubmit={onPreview} className="grid gap-4">
        <div className="grid gap-2">
          <label className="text-sm text-muted">Label Name</label>
          <input
            className="bg-surface-light border border-border rounded px-3 py-2"
            value={labelName}
            onChange={(e) => setLabelName(e.target.value)}
            placeholder="Neon Dusk Records"
          />
        </div>

        <div className="grid gap-2">
          <label className="text-sm text-muted">Label Description (optional)</label>
          <input
            className="bg-surface-light border border-border rounded px-3 py-2"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Atmospheric, guitar-driven indie..."
          />
        </div>

        <div className="grid gap-2">
          <label className="text-sm text-muted">Primary Genres (comma-separated)</label>
          <input
            className="bg-surface-light border border-border rounded px-3 py-2"
            value={primaryGenres}
            onChange={(e) => setPrimaryGenres(e.target.value)}
            placeholder="dream-pop, post-punk, ambient"
          />
        </div>

        <div className="grid gap-2">
          <label className="text-sm text-muted">Roster Text</label>
          <textarea
            className="bg-surface-light border border-border rounded px-3 py-2 min-h-[24rem]"
            value={rawText}
            onChange={(e) => setRawText(e.target.value)}
            placeholder={`${sampleJson}\n\nFreeform examples:\nVelvet Collapse - https://youtube.com/channel/UC...\nPale Meridian - https://open.spotify.com/artist/4Z8W30...\nGhost Antenna (post-punk, darkwave)\n@duskprotocol https://youtube.com/@duskprotocol`}
          />
          <input
            type="file"
            accept=".txt,.csv,.tsv,.json,.xlsx,.pdf"
            onChange={onFileChange}
            className="text-sm text-muted"
          />
          {file && (
            <div className="text-xs text-muted">Using file: {file.name} (file takes precedence over pasted text)</div>
          )}
        </div>

        <div className="flex items-center gap-3">
          <input
            id="resolve-missing"
            type="checkbox"
            checked={resolveMissing}
            onChange={(e) => setResolveMissing(e.target.checked)}
          />
          <label htmlFor="resolve-missing" className="text-sm text-muted">
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
          <label htmlFor="run-pipeline" className="text-sm text-muted">
            Run discovery pipeline after import
          </label>
        </div>

        {step === "input" && (
          <button
            type="submit"
            className="bg-primary text-white rounded px-4 py-2 disabled:opacity-50"
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
        <div className="mt-6 bg-surface-light border border-border rounded p-4 text-sm animate-bounce-in">
          <div className="font-semibold mb-2">Review Parsed Roster</div>
          <div className="text-muted mb-2">
            Parsed {result.parsed_count} entries. Review and confirm before importing.
          </div>
          {result.warnings?.length > 0 && (
            <div className="mt-3">
              <div className="font-semibold">Warnings</div>
              <ul className="list-disc pl-5">
                {result.warnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          <div className="mt-4 grid gap-3">
            {entries.map((entry, idx) => (
              <div key={idx} className="grid gap-2 border border-border rounded p-3">
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
                    className="bg-surface border border-border rounded px-2 py-1 flex-1"
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
                    className="bg-surface border border-border rounded px-2 py-1"
                    value={entry.platform || ""}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, platform: e.target.value };
                      setEntries(next);
                    }}
                    placeholder="platform (youtube)"
                  />
                  <input
                    className="bg-surface border border-border rounded px-2 py-1"
                    value={entry.platform_id || ""}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, platform_id: e.target.value };
                      setEntries(next);
                    }}
                    placeholder="platform_id (UC...)"
                  />
                  <input
                    className="bg-surface border border-border rounded px-2 py-1 md:col-span-2"
                    value={entry.platform_url || ""}
                    onChange={(e) => {
                      const next = [...entries];
                      next[idx] = { ...entry, platform_url: e.target.value };
                      setEntries(next);
                    }}
                    placeholder="platform_url"
                  />
                  <input
                    className="bg-surface border border-border rounded px-2 py-1 md:col-span-2"
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
              className="bg-surface border border-border rounded px-4 py-2"
              onClick={() => setStep("input")}
            >
              Back
            </button>
            <button
              type="button"
              className="bg-primary text-white rounded px-4 py-2 disabled:opacity-50"
              onClick={onConfirm}
              disabled={status === "loading"}
            >
              {status === "loading" ? "Importing..." : "Confirm Import"}
            </button>
          </div>
        </div>
      )}

      {step === "done" && result && (
        <div className="mt-6 bg-surface-light border border-border rounded p-4 text-sm animate-bounce-in">
          <div className="font-semibold mb-2">Import Complete</div>
          <div className="text-muted mb-2">
            Parsed {result.parsed_count} entries, created {result.created_count}, skipped {result.skipped_count}.
          </div>
          {runPipeline && (
            <div className="mb-2 text-xs text-accent-light">
              Pipeline queued. You can follow status on the dashboard.
            </div>
          )}
          {result.label_id && (
            <div className="text-muted">
              Label ID: <span className="text-primary-light">{result.label_id}</span>
            </div>
          )}
          {result.warnings?.length > 0 && (
            <div className="mt-3">
              <div className="font-semibold">Warnings</div>
              <ul className="list-disc pl-5">
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
