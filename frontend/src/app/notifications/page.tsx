"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing, CheckCheck, Filter } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, Notification, NotificationCenterPreferences } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

type NotificationCategory = "replies" | "social" | "communities" | "moderation";
type NotificationV2 = Notification & {
  category: NotificationCategory;
  priority: "high" | "normal" | "low";
  label: string;
  target_url: string;
};

type NotificationGroup = {
  key: string;
  ids: string[];
  items: NotificationV2[];
  primary: NotificationV2;
  unread: boolean;
};

const categoryTabs: Array<{ value: NotificationCategory | null; label: string }> = [
  { value: null, label: "Все" },
  { value: "replies", label: "Ответы" },
  { value: "social", label: "Социальные" },
  { value: "communities", label: "Сообщества" },
  { value: "moderation", label: "Модерация" },
];

export default function NotificationsPage() {
  const { user, loading } = useAuth();
  const qc = useQueryClient();
  const [category, setCategory] = useState<NotificationCategory | null>(null);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const suffix = `${category ? `category=${category}&` : ""}${unreadOnly ? "unread=1" : ""}`.replace(/&$/, "");
  const endpoint = `/notifications/center/${suffix ? `?${suffix}` : ""}`;

  const preferences = useQuery({
    queryKey: ["notification-center-preferences"],
    queryFn: () => clientApi<NotificationCenterPreferences>("/notifications/center/preferences/"),
    enabled: Boolean(user),
  });

  const query = useQuery({
    queryKey: ["notifications", category, unreadOnly],
    queryFn: () => clientApi<CursorPage<NotificationV2>>(endpoint),
    enabled: Boolean(user),
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });

  const refreshCounts = () => {
    void qc.invalidateQueries({ queryKey: ["notifications"] });
    void qc.invalidateQueries({ queryKey: ["notification-unread"] });
  };

  const markGroup = useMutation({
    mutationFn: (ids: string[]) => clientApi<{ updated: number }>("/notifications/read/", {
      method: "PUT",
      body: JSON.stringify({ ids }),
    }),
    onSuccess: refreshCounts,
  });

  const markAll = useMutation({
    mutationFn: () => clientApi<{ updated: number }>(`/notifications/read-all/${category ? `?category=${category}` : ""}`, { method: "PUT" }),
    onSuccess: refreshCounts,
  });

  const toggleReactionNotifications = useMutation({
    mutationFn: (enabled: boolean) => clientApi<NotificationCenterPreferences>("/notifications/center/preferences/", {
      method: "PATCH",
      body: JSON.stringify({ publication_reactions: enabled }),
    }),
    onSuccess: (data) => {
      qc.setQueryData(["notification-center-preferences"], data);
    },
  });

  const groups = useMemo(() => groupNotifications(query.data?.results ?? []), [query.data?.results]);
  const hasUnread = groups.some(group => group.unread);

  if (!loading && !user) {
    return <AppShell><EmptyState icon={BellRing} title="Уведомления доступны после входа" text="Здесь будут ответы, подписки, события сообществ и модерации." action={{ href: "/login", label: "Войти" }}/></AppShell>;
  }

  return <AppShell>
    <section className="page-head split-head">
      <div>
        <div className="eyebrow">NIGHT IRIS / СОБЫТИЯ</div>
        <h1>Уведомления</h1>
        <p>Ответы, подписки, сообщества и модерация в одном центре. Состояние синхронизируется с backend.</p>
      </div>
      {hasUnread ? <button className="secondary-button" disabled={markAll.isPending} onClick={() => markAll.mutate()}><CheckCheck size={15}/> Прочитать {category ? "категорию" : "все"}</button> : null}
    </section>

    <div className="feed-tabs" role="tablist" aria-label="Категории уведомлений">
      {categoryTabs.map(tab => <button key={tab.label} className={category === tab.value ? "active" : ""} onClick={() => setCategory(tab.value)} role="tab" aria-selected={category === tab.value}>{tab.label}</button>)}
    </div>

    <div className="section-heading">
      <span>{query.data?.results.length ?? 0} событий на странице</span>
      <div className="notification-inline-controls">
        {preferences.data ? <label className="notification-preference-inline">
          <input
            type="checkbox"
            checked={preferences.data.publication_reactions}
            disabled={toggleReactionNotifications.isPending}
            onChange={(event) => toggleReactionNotifications.mutate(event.target.checked)}
          />
          Реакции
        </label> : null}
        <button className="secondary-button compact-button" onClick={() => setUnreadOnly(value => !value)}><Filter size={14}/>{unreadOnly ? "Показать все" : "Только непрочитанные"}</button>
      </div>
    </div>

    {query.isLoading ? <LoadingBlock/> : query.isError ? <div className="error-panel">Не удалось загрузить уведомления.</div> : groups.length ? <div className="notification-list">
      {groups.map(group => {
        const n = group.primary;
        const actorText = actorSummary(group.items);
        const details = n.comment?.excerpt || n.publication?.title || n.label;
        return <article key={group.key} className={`notification-row ${group.unread ? "notification-unread" : ""}`}>
          <span className="notification-dot"/>
          <div>
            <div className="meta-row">
              <strong>{actorText}</strong>
              <span className="status-chip">{categoryLabel(n.category)}</span>
              {n.priority === "high" ? <span className="status-chip">Важно</span> : null}
            </div>
            <p><strong>{group.items.length > 1 ? `${n.label} · ${group.items.length}` : n.label}</strong></p>
            <p>{details}</p>
            <div className="meta-row">
              <time>{new Date(n.created_at).toLocaleString("ru-RU")}</time>
              <Link href={n.target_url} onClick={() => { if (group.unread) markGroup.mutate(group.ids); }}>Открыть</Link>
            </div>
          </div>
        </article>;
      })}
    </div> : <EmptyState icon={BellRing} title={unreadOnly ? "Всё прочитано" : "Пока тихо"} text={unreadOnly ? "В этой категории нет непрочитанных событий." : "Новые события появятся здесь автоматически."}/>} 
  </AppShell>;
}

function categoryLabel(category: NotificationCategory) {
  return ({ replies: "Ответы", social: "Социальное", communities: "Сообщество", moderation: "Модерация" } as const)[category];
}

function actorSummary(items: NotificationV2[]) {
  const names = Array.from(new Set(items.map(item => item.actor?.nickname).filter(Boolean) as string[]));
  if (!names.length) return "Night Iris";
  if (names.length === 1) return `@${names[0]}`;
  if (names.length === 2) return `@${names[0]} и @${names[1]}`;
  return `@${names[0]}, @${names[1]} и ещё ${names.length - 2}`;
}

function groupNotifications(items: NotificationV2[]): NotificationGroup[] {
  const groups: NotificationGroup[] = [];
  const sixHours = 6 * 60 * 60 * 1000;

  for (const item of items) {
    const target = item.target_url.split("#")[0];
    const previous = groups.at(-1);
    const closeInTime = previous ? Math.abs(new Date(previous.primary.created_at).getTime() - new Date(item.created_at).getTime()) <= sixHours : false;
    const canGroup = Boolean(previous && closeInTime && previous.primary.kind === item.kind && previous.primary.target_url.split("#")[0] === target);

    if (canGroup && previous) {
      previous.items.push(item);
      previous.ids.push(item.id);
      previous.unread = previous.unread || !item.is_read;
      continue;
    }

    groups.push({
      key: `${item.kind}:${target}:${item.id}`,
      ids: [item.id],
      items: [item],
      primary: item,
      unread: !item.is_read,
    });
  }

  return groups;
}
