"use client";

import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { Snapshot } from "@/lib/api";

export function ArtistCharts({ snapshots }: { snapshots: Snapshot[] }) {
  const data = snapshots.map((s) => ({
    date: new Date(s.captured_at).toLocaleDateString("en-US", { month: "short", day: "numeric" }),
    followers: s.followers,
    views: s.views,
    engagement: s.engagement_rate != null ? +(s.engagement_rate * 100).toFixed(2) : null,
  }));
  const hasEngagement = data.some((d) => d.engagement != null);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <h3 className="text-sm text-muted mb-3">Followers</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3e" />
            <XAxis dataKey="date" tick={{ fill: "#6b7280", fontSize: 10 }} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} />
            <Tooltip contentStyle={{ background: "#12121a", border: "1px solid #2a2a3e", borderRadius: "8px", color: "#e5e7eb" }} />
            <Line type="monotone" dataKey="followers" stroke="#8b5cf6" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div>
        <h3 className="text-sm text-muted mb-3">Views</h3>
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3e" />
            <XAxis dataKey="date" tick={{ fill: "#6b7280", fontSize: 10 }} />
            <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} />
            <Tooltip contentStyle={{ background: "#12121a", border: "1px solid #2a2a3e", borderRadius: "8px", color: "#e5e7eb" }} />
            <Line type="monotone" dataKey="views" stroke="#06b6d4" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="md:col-span-2">
        <h3 className="text-sm text-muted mb-3">Engagement Rate (%)</h3>
        {hasEngagement ? (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#2a2a3e" />
              <XAxis dataKey="date" tick={{ fill: "#6b7280", fontSize: 10 }} />
              <YAxis tick={{ fill: "#6b7280", fontSize: 10 }} />
              <Tooltip contentStyle={{ background: "#12121a", border: "1px solid #2a2a3e", borderRadius: "8px", color: "#e5e7eb" }} />
              <Line type="monotone" dataKey="engagement" stroke="#10b981" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-xs text-muted">No engagement data available yet.</div>
        )}
      </div>
    </div>
  );
}
