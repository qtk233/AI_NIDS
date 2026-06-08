import { useState, useEffect, useCallback } from "react";
import type { ApiResponse } from "../lib/types";

export function useApi<T>(
  fetcher: () => Promise<ApiResponse<T>>
) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(() => {
    setLoading(true);
    setError(null);
    fetcher()
      .then((r) => {
        if (r.success) {
          setData(r.data);
        } else {
          setError(r.error ?? "Unknown error");
        }
      })
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : "Request failed");
      })
      .finally(() => setLoading(false));
  }, [fetcher]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
}
