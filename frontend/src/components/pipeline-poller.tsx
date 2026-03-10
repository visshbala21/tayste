"use client";

import { useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";

const ACTIVE_STATUSES = new Set(["queued", "running"]);
const POLL_INTERVAL = 8000; // 8 seconds — avoids piling up slow requests

/**
 * Invisible component that polls (via router.refresh()) while the pipeline is active.
 * Pauses when the browser tab is hidden to avoid wasted requests.
 */
export function PipelinePoller({ status }: { status?: string | null }) {
  const router = useRouter();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isActive = !!status && ACTIVE_STATUSES.has(status);

  const startPolling = useCallback(() => {
    if (intervalRef.current) return;
    intervalRef.current = setInterval(() => {
      if (!document.hidden) {
        router.refresh();
      }
    }, POLL_INTERVAL);
  }, [router]);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!isActive) {
      stopPolling();
      return;
    }

    startPolling();

    const onVisibility = () => {
      if (document.hidden) {
        stopPolling();
      } else {
        router.refresh(); // immediate refresh on tab return
        startPolling();
      }
    };
    document.addEventListener("visibilitychange", onVisibility);

    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [isActive, router, startPolling, stopPolling]);

  return null;
}
