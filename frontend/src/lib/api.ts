// Server-side (SSR) uses Docker internal network; client-side uses the browser-accessible URL.
const SERVER_API_BASE = process.env.INTERNAL_API_URL || "http://backend:8000";
const CLIENT_API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001";

function getApiBase(): string {
  return typeof window === "undefined" ? SERVER_API_BASE : CLIENT_API_BASE;
}

async function fetchAPI<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${getApiBase()}/api${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options?.headers },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

async function fetchMultipart<T>(path: string, form: FormData): Promise<T> {
  const res = await fetch(`${getApiBase()}/api${path}`, {
    method: "POST",
    body: form,
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Label {
  id: string;
  name: string;
  description?: string;
  genre_tags?: Record<string, string[]>;
  label_dna?: Record<string, unknown>;
  pipeline_status?: string;
  pipeline_started_at?: string;
  pipeline_completed_at?: string;
  created_at: string;
}

export interface ScoutFeedItem {
  artist_id: string;
  artist_name: string;
  image_url?: string;
  fit_score: number;
  momentum_score: number;
  risk_score: number;
  final_score: number;
  nearest_roster_artist?: string;
  growth_7d?: number;
  growth_30d?: number;
  genre_tags?: string[];
}

export interface ScoutFeed {
  label_id: string;
  batch_id: string;
  items: ScoutFeedItem[];
  total: number;
}

export interface ClusterInfo {
  cluster_id: string;
  cluster_index: number;
  cluster_name?: string;
  artist_ids: string[];
}

export interface TasteMap {
  label_id: string;
  label_name: string;
  label_dna?: Record<string, unknown>;
  clusters: ClusterInfo[];
}

export interface Snapshot {
  platform: string;
  captured_at: string;
  followers?: number;
  views?: number;
  likes?: number;
  comments?: number;
  engagement_rate?: number;
}

export interface ArtistFeatures {
  computed_at: string;
  growth_7d?: number;
  growth_30d?: number;
  acceleration?: number;
  engagement_rate?: number;
  momentum_score?: number;
  risk_score?: number;
  risk_flags?: string[];
}

export interface ArtistDetail {
  id: string;
  name: string;
  bio?: string;
  genre_tags?: string[];
  image_url?: string;
  is_candidate: boolean;
  platform_accounts: { platform: string; platform_id: string; platform_url?: string }[];
  created_at: string;
  snapshots: Snapshot[];
  latest_features?: ArtistFeatures;
  llm_brief?: {
    what_is_happening: string;
    why_fit: string;
    risks_unknowns: string;
    next_actions: string[];
  };
  feedback_history?: { action: string; notes?: string; created_at: string }[];
}

export interface RosterImportPayload {
  label: {
    name: string;
    description?: string;
    genre_tags?: Record<string, string[]>;
  };
  raw_text: string;
  default_platform?: string;
  resolve_missing?: boolean;
  dry_run?: boolean;
  run_pipeline?: boolean;
}

export interface RosterImportFilePayload {
  label: {
    name: string;
    description?: string;
    genre_tags?: Record<string, string[]>;
  };
  file: File;
  default_platform?: string;
  resolve_missing?: boolean;
  dry_run?: boolean;
  run_pipeline?: boolean;
}

export interface RosterConfirmPayload {
  label: {
    name: string;
    description?: string;
    genre_tags?: Record<string, string[]>;
  };
  artists: {
    name: string;
    platform?: string;
    platform_id?: string;
    platform_url?: string;
    genre_tags?: string[];
  }[];
  default_platform?: string;
  run_pipeline?: boolean;
}

export interface RosterImportResult {
  label_id?: string;
  label_name?: string;
  parsed_count: number;
  created_count: number;
  skipped_count: number;
  parsed: {
    name: string;
    platform?: string;
    platform_id?: string;
    platform_url?: string;
    genre_tags?: string[];
  }[];
  created: { artist_id: string; name: string; platform: string; platform_id?: string }[];
  skipped: { name: string; reason: string }[];
  warnings: string[];
}

export const api = {
  getLabels: () => fetchAPI<Label[]>("/labels"),
  getLabel: (id: string) => fetchAPI<Label>(`/labels/${id}`),
  getTasteMap: (id: string) => fetchAPI<TasteMap>(`/labels/${id}/taste-map`),
  getScoutFeed: (id: string, limit: number = 50) =>
    fetchAPI<ScoutFeed>(`/labels/${id}/scout-feed?limit=${limit}`),
  getArtist: (id: string) => fetchAPI<ArtistDetail>(`/artists/${id}`),
  submitFeedback: (labelId: string, data: { artist_id: string; action: string; notes?: string }) =>
    fetchAPI(`/labels/${labelId}/feedback`, { method: "POST", body: JSON.stringify(data) }),
  refreshLabelLLM: (id: string) =>
    fetchAPI(`/labels/${id}/llm/refresh`, { method: "POST" }),
  refreshArtistLLM: (id: string) =>
    fetchAPI(`/artists/${id}/llm/refresh`, { method: "POST" }),
  importRoster: (payload: RosterImportPayload) =>
    fetchAPI<RosterImportResult>("/labels/import-text", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  importRosterFile: (payload: RosterImportFilePayload) => {
    const form = new FormData();
    form.append("file", payload.file);
    form.append("label_name", payload.label.name);
    if (payload.label.description) {
      form.append("label_description", payload.label.description);
    }
    if (payload.label.genre_tags) {
      form.append("label_genre_tags", JSON.stringify(payload.label.genre_tags));
    }
    form.append("default_platform", payload.default_platform || "youtube");
    form.append("resolve_missing", String(payload.resolve_missing ?? true));
    form.append("dry_run", String(payload.dry_run ?? false));
    form.append("run_pipeline", String(payload.run_pipeline ?? false));
    return fetchMultipart<RosterImportResult>("/labels/import-file", form);
  },
  importRosterConfirm: (payload: RosterConfirmPayload) =>
    fetchAPI<RosterImportResult>("/labels/import-confirm", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
