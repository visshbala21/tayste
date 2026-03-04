"use client";

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="bg-surface border border-border rounded-lg p-12 text-center">
      <h2 className="text-lg font-semibold mb-2">Something went wrong</h2>
      <p className="text-muted text-sm mb-4">
        {error.message?.includes("API error")
          ? "The backend service is temporarily unavailable. Please try again."
          : "An unexpected error occurred."}
      </p>
      <button
        onClick={reset}
        className="text-sm bg-primary/10 text-primary px-4 py-2 rounded-lg hover:bg-primary/20 transition-all duration-200"
      >
        Try again
      </button>
    </div>
  );
}
