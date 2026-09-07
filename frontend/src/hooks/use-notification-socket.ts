"use client";

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { clientApi } from "@/lib/client-api";

function websocketUrl(ticket: string) {
  if (typeof window === "undefined") return "";
  const base = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "ws://localhost:8000/ws/notifications/"
    : `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/notifications/`;
  return `${base}?ticket=${encodeURIComponent(ticket)}`;
}

export function useNotificationSocket(enabled: boolean) {
  const qc = useQueryClient();
  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;

    const refresh = () => {
      void qc.invalidateQueries({ queryKey: ["notification-unread"] });
      void qc.invalidateQueries({ queryKey: ["notifications"] });
    };

    const connect = async () => {
      try {
        const { ticket } = await clientApi<{ ticket: string }>("/messenger/ws-ticket/", { method: "POST" });
        if (cancelled) return;
        const socket = new WebSocket(websocketUrl(ticket));
        socketRef.current = socket;

        socket.onopen = () => {
          retryRef.current = 0;
          refresh();
          heartbeatRef.current = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: "ping" }));
          }, 30000);
        };

        socket.onmessage = event => {
          try {
            const payload = JSON.parse(event.data) as { type?: string };
            if (payload.type === "notification.changed" || payload.type === "notifications.ready") refresh();
          } catch {
            // REST polling/focus refresh remains the reconciliation fallback.
          }
        };

        socket.onclose = () => {
          if (heartbeatRef.current) clearInterval(heartbeatRef.current);
          refresh();
          if (!cancelled) {
            const delay = Math.min(1000 * 2 ** retryRef.current++, 10000);
            timerRef.current = setTimeout(connect, delay);
          }
        };
      } catch {
        if (!cancelled) timerRef.current = setTimeout(connect, 3000);
      }
    };

    void connect();
    return () => {
      cancelled = true;
      if (timerRef.current) clearTimeout(timerRef.current);
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      socketRef.current?.close();
    };
  }, [enabled, qc]);
}
