"use client";

import { useQuery } from "@tanstack/react-query";
import { Activity, Database, HardDrive, RadioTower, RefreshCw, Server, Timer, Workflow } from "lucide-react";
import { StatusBadge } from "@/components/admin/admin-ui";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi, errorMessage } from "@/lib/client-api";

type Ready = { status: string; checks: Record<string, string> };
type Summary = {
  generated_at: string;
  database_latency_ms: number;
  redis: string;
  celery: {
    heartbeat_age_seconds: number | null;
    healthy: boolean;
    tasks_succeeded: number;
    tasks_failed: number;
    last_failure: { task?: string; error?: string; at?: string } | null;
  };
  notifications: { pending: number; failed: number };
  messenger: { events_last_hour: number; events_total: number };
  slow_query_threshold_ms: number;
  request_id: string;
};

const icons: Record<string, React.ReactNode> = {
  database: <Database />,
  redis: <RadioTower />,
  object_storage: <HardDrive />,
};

export default function AdminSystemPage() {
  const ready = useQuery({
    queryKey: ["admin", "ready"],
    queryFn: () => clientApi<Ready>("/ready/"),
    refetchInterval: 15_000,
    retry: false,
  });
  const telemetry = useQuery({
    queryKey: ["admin", "observability"],
    queryFn: () => clientApi<Summary>("/observability/summary/"),
    refetchInterval: 15_000,
    retry: false,
  });
  const refresh = () => { ready.refetch(); telemetry.refetch(); };

  return <>
    <div className="admin-page-head">
      <div>
        <div className="eyebrow">ИНФРАСТРУКТУРА / TELEMETRY</div>
        <h1>Состояние системы</h1>
        <p>Readiness, Celery heartbeat, очередь уведомлений, активность Messenger и базовая DB latency. Обновляется каждые 15 секунд.</p>
      </div>
      <button className="secondary-button compact-button" onClick={refresh}><RefreshCw size={14}/> Проверить</button>
    </div>

    {ready.isLoading ? <LoadingBlock /> : ready.error ? <div className="error-panel">{errorMessage(ready.error)}</div> : <>
      <div className="admin-system-summary">
        <div><span>Общий readiness</span><strong>{ready.data?.status}</strong></div>
        <StatusBadge value={ready.data?.status ?? "unknown"}/>
      </div>
      <div className="admin-system-grid">
        {Object.entries(ready.data?.checks ?? {}).map(([name, value]) => <article key={name}>
          <div className="system-icon">{icons[name] ?? <Server/>}</div>
          <div><strong>{name.replace("_", " ")}</strong><span>readiness check</span></div>
          <StatusBadge value={value}/>
        </article>)}
      </div>
    </>}

    <div className="admin-section">
      <div className="admin-section-title"><h2>Operational telemetry</h2><span>{telemetry.data ? new Date(telemetry.data.generated_at).toLocaleTimeString() : "—"}</span></div>
      {telemetry.isLoading ? <LoadingBlock /> : telemetry.error ? <div className="error-panel">{errorMessage(telemetry.error)}</div> : telemetry.data ? <>
        <div className="admin-metric-grid">
          <article className="admin-metric"><span>DB latency</span><strong>{telemetry.data.database_latency_ms.toFixed(1)} ms</strong><small>SELECT 1 from API process</small></article>
          <article className={`admin-metric ${telemetry.data.celery.healthy ? "" : "metric-danger"}`}><span>Celery heartbeat</span><strong>{telemetry.data.celery.heartbeat_age_seconds == null ? "—" : `${telemetry.data.celery.heartbeat_age_seconds}s`}</strong><small>{telemetry.data.celery.healthy ? "worker/beat signal is fresh" : "heartbeat is stale or missing"}</small></article>
          <article className={`admin-metric ${telemetry.data.notifications.failed ? "metric-danger" : telemetry.data.notifications.pending ? "metric-warning" : ""}`}><span>Notification outbox</span><strong>{telemetry.data.notifications.pending}</strong><small>{telemetry.data.notifications.failed} failed</small></article>
          <article className="admin-metric"><span>Messenger events / 1h</span><strong>{telemetry.data.messenger.events_last_hour}</strong><small>{telemetry.data.messenger.events_total} durable events total</small></article>
          <article className={`admin-metric ${telemetry.data.celery.tasks_failed ? "metric-warning" : ""}`}><span>Celery tasks</span><strong>{telemetry.data.celery.tasks_succeeded}</strong><small>{telemetry.data.celery.tasks_failed} failed since shared counters were initialized</small></article>
          <article className="admin-metric"><span>Slow query threshold</span><strong>{telemetry.data.slow_query_threshold_ms} ms</strong><small>request id: {telemetry.data.request_id || "—"}</small></article>
        </div>
        {telemetry.data.celery.last_failure ? <div className="admin-policy admin-observability-failure"><Activity/><div><strong>Последняя ошибка Celery: {telemetry.data.celery.last_failure.task ?? "unknown task"}</strong><p>{telemetry.data.celery.last_failure.error ?? "No error text"}</p></div></div> : null}
      </> : null}
    </div>

    <div className="admin-section">
      <div className="admin-section-title"><h2>Что отслеживается</h2><span>Stage 8.11</span></div>
      <div className="admin-shortcuts">
        <div className="admin-policy"><Timer/><div><strong>HTTP / SQL latency</strong><p>Prometheus histogram, request ID и slow-query logging без параметров запроса.</p></div></div>
        <div className="admin-policy"><Workflow/><div><strong>Realtime / Celery</strong><p>WebSocket gauge, durable Messenger events, heartbeat и shared task counters.</p></div></div>
      </div>
    </div>
  </>;
}
