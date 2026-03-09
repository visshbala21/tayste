"use client";

import { useEffect, useRef } from "react";
import { useRouter } from "next/navigation";

const ACTIVE_STATUSES = new Set(["queued", "running"]);
const POLL_INTERVAL = 3000; // 3 seconds

/**
 * Invisible component that polls (via router.refresh()) while the pipeline is active.
 * Drop it into any page that displays pipeline status.
 */
export function PipelinePoller({ status }: { status?: string | null }) {
  const router = useRouter();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isActive = !!status && ACTIVE_STATUSES.has(status);

  useEffect(() => {
    if (!isActive) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      router.refresh();
    }, POLL_INTERVAL);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isActive, router]);

  return null;
}
