import { useEffect, useRef, useState, useCallback } from "react";
import type { DetectionResult } from "../lib/types";

export function useWebSocket() {
  const [results, setResults] = useState<DetectionResult[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);

  const connect = useCallback(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws/live");
    ws.onopen = () => {
      setConnected(true);
      retryRef.current = 0;
    };
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data) as DetectionResult;
      setResults((prev) => [data, ...prev].slice(0, 500));
    };
    ws.onclose = () => {
      setConnected(false);
      const delay = Math.min(1000 * Math.pow(2, retryRef.current), 30000);
      retryRef.current += 1;
      setTimeout(connect, delay);
    };
    wsRef.current = ws;
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  return { results, connected, clear: () => setResults([]) };
}
