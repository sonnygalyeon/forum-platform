"use client";

import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { clientApi } from "@/lib/client-api";

export type EngagementSocketState = "rest" | "connecting" | "live" | "reconnecting";

function websocketUrl(ticket: string, publicationId: string) {
  if (typeof window === "undefined") return "";
  const base = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
    ? "ws://localhost:8000/ws/engagement/"
    : `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/engagement/`;
  const params = new URLSearchParams({ ticket, publication: publicationId });
  return `${base}?${params.toString()}`;
}

export function useEngagementSocket(publicationId: string, enabled: boolean): EngagementSocketState {
  const qc = useQueryClient();
  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const retryTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [state, setState] = useState<EngagementSocketState>(enabled ? "connecting" : "rest");

  useEffect(() => {
    if (!enabled || !publicationId) {
      setState("rest");
      return;
    }
    let cancelled = false;
    setState("connecting");

    const reconcile = () => {
      void qc.invalidateQueries({ queryKey: ["publication-engagement", publicationId] });
      void qc.invalidateQueries({ queryKey: ["comments", publicationId] });
      void qc.invalidateQueries({ queryKey: ["home-feed"] });
      void qc.invalidateQueries({ queryKey: ["community-publications"] });
    };

    const stopHeartbeat = () => {
      if (heartbeatRef.current) clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    };

    const scheduleReconnect = (connect: () => Promise<void>) => {
      if (cancelled) return;
      setState("reconnecting");
      const delay = Math.min(750 * 2 ** retryRef.current++, 10000);
      retryTimerRef.current = setTimeout(() => void connect(), delay);
    };

    const connect = async () => {
      try {
        const { ticket } = await clientApi<{ ticket: string }>("/messenger/ws-ticket/", { method: "POST" });
        if (cancelled) return;

        const socket = new WebSocket(websocketUrl(ticket, publicationId));
        socketRef.current = socket;

        socket.onopen = () => {
          if (cancelled) return;
          retryRef.current = 0;
          setState("live");
          reconcile();
          stopHeartbeat();
          heartbeatRef.current = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) {
              socket.send(JSON.stringify({ type: "ping" }));
            }
          }, 30000);
        };

        socket.onmessage = (event) => {
          try {
            const payload = JSON.parse(event.data) as { type?: string; publication_id?: string };
            if (
              (payload.type === "engagement.changed" || payload.type === "engagement.ready")
              && payload.publication_id === publicationId
            ) {
              reconcile();
            }
          } catch {
            // REST reconciliation on reconnect/focus remains authoritative.
          }
        };

        socket.onclose = () => {
          stopHeartbeat();
          reconcile();
          scheduleReconnect(connect);
        };

        socket.onerror = () => {
          socket.close();
        };
      } catch {
        scheduleReconnect(connect);
      }
    };

    void connect();

    const onVisible = () => {
      if (document.visibilityState === "visible") reconcile();
    };
    document.addEventListener("visibilitychange", onVisible);

    return () => {
      cancelled = true;
      document.removeEventListener("visibilitychange", onVisible);
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
      stopHeartbeat();
      socketRef.current?.close();
    };
  }, [enabled, publicationId, qc]);

  return state;
}
