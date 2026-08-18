"use client";

import { useQuery } from "@tanstack/react-query";
import { FilePlus2, Sparkles } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { PublicationCard } from "@/components/feed/publication-card";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, Publication } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function HomePage() {
  const { user, loading: authLoading } = useAuth();
  const query = useQuery({
    queryKey: ["home-feed", Boolean(user)],
    queryFn: () => clientApi<CursorPage<Publication>>(user ? "/feed/" : "/publications/"),
    enabled: !authLoading,
  });

  return <AppShell><section className="page-head"><div><div className="eyebrow">NIGHT IRIS / ЛЕНТА</div><h1>{user ? `Добро пожаловать, ${user.nickname}` : "Обсуждения без шума"}</h1><p>{user ? "Здесь появятся публикации людей и сообществ, на которые вы подписаны." : "Публичная лента форума. Сейчас здесь отображаются только реальные публикации."}</p></div></section>{query.isLoading ? <LoadingBlock/> : query.isError ? <div className="error-panel">Backend недоступен. Проверьте, что Django запущен на порту 8000.</div> : query.data?.results.length ? <div className="feed-list">{query.data.results.map(item => <PublicationCard key={item.id} publication={item}/>)}</div> : <EmptyState icon={user ? FilePlus2 : Sparkles} title="Форум пока пуст" text={user ? "Создайте первую публикацию — никаких демонстрационных карточек здесь больше нет." : "Пока никто ничего не опубликовал. Зарегистрируйтесь и станьте первым автором Night Iris."} action={user ? {href:"/new",label:"Создать первую публикацию"} : {href:"/register",label:"Создать аккаунт"}}/>}</AppShell>;
}
