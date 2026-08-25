"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { clientApi } from "@/lib/client-api";
import type { MessengerActivityState, MessengerEventPage, MessengerSocketEvent } from "@/lib/types";

function websocketBase() {
  if (typeof window === "undefined") return "";
  if (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") {
    return "ws://localhost:8000/ws/messenger/";
  }
  return `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/ws/messenger/`;
}

const CURSOR_PREFIX = "night-iris:messenger:last-event-id";

export function useMessengerSocket(
  onEvent: (event: MessengerSocketEvent) => void,
  enabled = true,
  cursorNamespace = "anonymous",
) {
  const socketRef = useRef<WebSocket | null>(null);
  const callbackRef = useRef(onEvent);
  const retryRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const syncingRef = useRef(false);
  const bufferedDurableRef = useRef<MessengerSocketEvent[]>([]);
  const readyBarrierRef = useRef<number | null>(null);
  const [connected, setConnected] = useState(false);
  const [syncing, setSyncing] = useState(false);

  callbackRef.current = onEvent;

  const cursorKey = `${CURSOR_PREFIX}:${cursorNamespace}`;

  const getCursor = useCallback(() => {
    if (typeof window === "undefined") return 0;
    const value = Number(window.localStorage.getItem(cursorKey) ?? 0);
    return Number.isFinite(value) && value > 0 ? value : 0;
  }, [cursorKey]);

  const advanceCursor = useCallback((eventId?: number) => {
    if (!eventId || typeof window === "undefined") return;
    const current = getCursor();
    if (eventId > current) window.localStorage.setItem(cursorKey, String(eventId));
  }, [cursorKey, getCursor]);

  const replay = useCallback((event: MessengerSocketEvent) => {
    callbackRef.current(event);
    advanceCursor(event.event_id);
  }, [advanceCursor]);

  const syncMissedEvents = useCallback(async (targetEventId?: number) => {
    if (syncingRef.current || !enabled) return;
    syncingRef.current = true;
    setSyncing(true);
    try {
      let after = getCursor();
      let pageCount = 0;
      while (pageCount < 100) {
        pageCount += 1;
        const result = await clientApi<MessengerEventPage>(`/messenger/events/?after=${after}`);
        if (!result.results.length) break;
        for (const row of result.results) {
          if (row.event_id <= getCursor()) continue;
          replay({ ...row.payload, event_id: row.event_id, sequence: row.sequence });
        }
        if (result.next_after <= after) break;
        after = result.next_after;
        if (targetEventId && after >= targetEventId) break;
        if (result.results.length < 200) break;
      }

      // Durable events can arrive over the socket while the REST catch-up is in
      // progress. Replay them only after the gap is closed so a newer live event
      // can never advance the cursor past an older missed event.
      const buffered = bufferedDurableRef.current
        .splice(0)
        .sort((a, b) => (a.event_id ?? 0) - (b.event_id ?? 0));
      for (const event of buffered) {
        if ((event.event_id ?? 0) > getCursor()) replay(event);
      }
    } finally {
      syncingRef.current = false;
      readyBarrierRef.current = null;
      setSyncing(false);
    }
  }, [enabled, getCursor, replay]);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;

    const connect = async () => {
      try {
        const { ticket } = await clientApi<{ ticket: string }>("/messenger/ws-ticket/", { method: "POST" });
        if (cancelled) return;
        const socket = new WebSocket(`${websocketBase()}?ticket=${encodeURIComponent(ticket)}`);
        socketRef.current = socket;
        bufferedDurableRef.current = [];
        readyBarrierRef.current = null;

        socket.onopen = () => {
          retryRef.current = 0;
          setConnected(true);
          heartbeatRef.current = setInterval(() => {
            if (socket.readyState === WebSocket.OPEN) socket.send(JSON.stringify({ type: "ping" }));
          }, 30000);
        };

        socket.onmessage = event => {
          try {
            const payload = JSON.parse(event.data) as MessengerSocketEvent;
            if (payload.type === "messenger.ready") {
              readyBarrierRef.current = payload.latest_event_id ?? getCursor();
              void syncMissedEvents(readyBarrierRef.current);
              return;
            }

            // Presence/activity/pong are transient and should not wait for the
            // durable catch-up barrier.
            if (!payload.event_id) {
              callbackRef.current(payload);
              return;
            }

            if (syncingRef.current || readyBarrierRef.current !== null) {
              bufferedDurableRef.current.push(payload);
              return;
            }

            if (payload.event_id > getCursor()) replay(payload);
          } catch {
            // Persistent state remains in PostgreSQL and will be resynced.
          }
        };

        socket.onclose = () => {
          setConnected(false);
          readyBarrierRef.current = null;
          bufferedDurableRef.current = [];
          if (heartbeatRef.current) clearInterval(heartbeatRef.current);
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
  }, [enabled, getCursor, replay, syncMissedEvents]);

  const sendActivity = useCallback((conversationId: string, state: MessengerActivityState) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify({ type: "activity", conversation_id: conversationId, state }));
    }
  }, []);

  const sendTyping = useCallback((conversationId: string, active: boolean) => {
    sendActivity(conversationId, active ? "typing" : "none");
  }, [sendActivity]);

  return { connected, syncing, sendActivity, sendTyping, syncMissedEvents };
}
