"use client";

import { useQuery } from "@tanstack/react-query";
import { FilePlus2, Sparkles } from "lucide-react";
import { useState } from "react";

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

  const query = useQuery({
    queryKey: ["home-feed", effectiveMode, user?.id ?? null],
    queryFn: () => clientApi<CursorPage<Publication>>(endpoint),
    enabled: !authLoading,
  });

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

      {query.isLoading ? (
        <LoadingBlock />
      ) : query.isError ? (
        <div className="error-panel">Backend недоступен. Проверьте Django API.</div>
      ) : query.data?.results.length ? (
        <div className="feed-list">
          {query.data.results.map((item) => (
            <PublicationCard key={item.id} publication={item} />
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
    </AppShell>
  );
}
