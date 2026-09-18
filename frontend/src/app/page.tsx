"use client";

import { useInfiniteQuery } from "@tanstack/react-query";
import { FilePlus2, SlidersHorizontal, Sparkles } from "lucide-react";
import { useState } from "react";
import Link from "next/link";

import { PublicationCard } from "@/components/feed/publication-card";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, Publication } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

type FeedMode = "latest" | "following" | "for-you";

const descriptions: Record<FeedMode, string> = {
  latest: "Свежие публичные публикации Night Iris.",
  following: "Публикации людей и сообществ, на которые вы подписаны.",
  "for-you": "Персональная лента по подпискам, сообществам, интересам и активности.",
};

export default function HomePage() {
  const { user, loading: authLoading } = useAuth();
  const [mode, setMode] = useState<FeedMode>("for-you");
  const effectiveMode: FeedMode = user ? mode : "latest";

  const endpoint =
    effectiveMode === "following"
      ? "/feed/"
      : effectiveMode === "for-you"
        ? "/feed/for-you/"
        : "/publications/";

  const query = useInfiniteQuery({
    queryKey: ["home-feed", effectiveMode, user?.id ?? null],
    initialPageParam: "",
    // Only use the query string from API pagination links. The backend host
    // may be internal; all browser requests must still pass through the BFF.
    queryFn: ({ pageParam, signal }) => clientApi<CursorPage<Publication>>(`${endpoint}${pageParam}`, { signal }),
    getNextPageParam: (page) => page.next ? new URL(page.next, "http://pagination.local").search : undefined,
    enabled: !authLoading,
  });
  const publications = [...new Map(
    query.data?.pages.flatMap((page) => page.results).map((item) => [item.id, item]) ?? [],
  ).values()];

  const emptyTitle =
    effectiveMode === "following"
      ? "Лента подписок пока пуста"
      : effectiveMode === "for-you"
        ? "Пока мало сигналов для персональной ленты"
        : "Форум пока пуст";

  const emptyText =
    effectiveMode === "following"
      ? "Подпишитесь на автора или сообщество, и новые публикации появятся здесь."
      : effectiveMode === "for-you"
        ? "Подпишитесь на авторов, сохраните публикации или участвуйте в обсуждениях. Night Iris начнёт точнее подбирать материалы."
        : user
          ? "Создайте первую публикацию Night Iris."
          : "Пока никто ничего не опубликовал. Зарегистрируйтесь и станьте первым автором.";

  return (
    <AppShell>
      <section className="page-head">
        <div>
          <div className="eyebrow">NIGHT IRIS / ЛЕНТА</div>
          <h1>{user ? `Добро пожаловать, ${user.nickname}` : "Обсуждения без шума"}</h1>
          <p>{descriptions[effectiveMode]}</p>
        </div>
      </section>

      {user ? (
        <div className="feed-tabs" role="tablist" aria-label="Режим ленты">
          <button
            className={mode === "for-you" ? "active" : ""}
            onClick={() => setMode("for-you")}
            role="tab"
            aria-selected={mode === "for-you"}
          >
            Для вас
          </button>
          <button
            className={mode === "following" ? "active" : ""}
            onClick={() => setMode("following")}
            role="tab"
            aria-selected={mode === "following"}
          >
            Подписки
          </button>
          <button
            className={mode === "latest" ? "active" : ""}
            onClick={() => setMode("latest")}
            role="tab"
            aria-selected={mode === "latest"}
          >
            Последние
          </button>
        </div>
      ) : null}

      {user && effectiveMode === "for-you" ? (
        <div className="feed-quality-tools">
          <span>Лента чередует знакомые источники и контролируемое исследование новых.</span>
          <Link href="/feed/preferences" className="secondary-button compact-button"><SlidersHorizontal size={14}/>Настройки ленты</Link>
        </div>
      ) : null}

      {query.isLoading ? (
        <LoadingBlock />
      ) : query.isError && !query.data ? (
        <div className="error-panel" role="alert">Не удалось загрузить ленту. <button type="button" className="secondary-button" onClick={() => void query.refetch()}>Повторить</button></div>
      ) : publications.length ? (
        <div className="feed-list">
          {publications.map((item) => (
            <PublicationCard key={item.id} publication={item} feedFeedback={effectiveMode === "for-you"} />
          ))}
        </div>
      ) : (
        <EmptyState
          icon={user ? FilePlus2 : Sparkles}
          title={emptyTitle}
          text={emptyText}
          action={
            user
              ? { href: "/discover", label: "Найти интересное" }
              : { href: "/register", label: "Создать аккаунт" }
          }
        />
      )}
      {query.isFetchNextPageError ? <div className="error-panel" role="alert">Не удалось загрузить следующую страницу. Попробуйте ещё раз.</div> : null}
      {query.hasNextPage ? (
        <button type="button" className="secondary-button" disabled={query.isFetching} onClick={() => void query.fetchNextPage()}>
          {query.isFetchingNextPage ? "Загружаем…" : query.isFetchNextPageError ? "Повторить загрузку" : "Показать ещё"}
        </button>
      ) : null}
    </AppShell>
  );
}
