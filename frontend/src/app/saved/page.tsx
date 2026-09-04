"use client";

import { useQuery } from "@tanstack/react-query";
import { Bookmark } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PublicationCard } from "@/components/feed/publication-card";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, Publication } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function SavedPage() {
  const { user, loading } = useAuth();
  const saved = useQuery({
    queryKey: ["bookmarks"],
    queryFn: () => clientApi<CursorPage<Publication>>("/users/me/bookmarks/"),
    enabled: Boolean(user),
  });
  if (loading) return <AppShell><LoadingBlock/></AppShell>;
  if (!user) return <AppShell><EmptyState icon={Bookmark} title="Нужен аккаунт" text="Сохранённые публикации привязаны к вашему аккаунту." action={{href:"/login",label:"Войти"}}/></AppShell>;
  return (
    <AppShell>
      <section className="page-head"><div><div className="eyebrow">БИБЛИОТЕКА / SAVED</div><h1>Сохранённые публикации</h1><p>Материалы, к которым хочется вернуться без археологии по истории браузера.</p></div></section>
      {saved.isLoading ? <LoadingBlock/> : saved.data?.results.length ? <div className="feed-list">{saved.data.results.map((publication) => <PublicationCard key={publication.id} publication={publication}/>)}</div> : <EmptyState icon={Bookmark} title="Пока пусто" text="Сохраняйте полезные вопросы, статьи и посты кнопкой закладки на странице публикации."/>}
    </AppShell>
  );
}
