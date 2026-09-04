"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Compass, Hash, Sparkles, UsersRound } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PublicationCard } from "@/components/feed/publication-card";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { DiscoveryResponse } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

type DiscoveryPayload = DiscoveryResponse & { personalized: boolean };

export default function DiscoverPage() {
  const { user } = useAuth();
  const discovery = useQuery({
    queryKey: ["discover", user?.id ?? "anonymous"],
    queryFn: () => clientApi<DiscoveryPayload>("/discover/"),
  });

  return (
    <AppShell>
      <section className="page-head">
        <div>
          <div className="eyebrow">DISCOVERY / NIGHT IRIS</div>
          <h1>Найти полезное без бесконечной ленты</h1>
          <p>{discovery.data?.personalized ? "Рекомендации учитывают ваши подписки, сообщества и темы, которые вы сохраняете или публикуете." : "Пока показываем свежие и активные материалы. После входа рекомендации станут персональными."}</p>
        </div>
        <Link href="/search" className="secondary-button"><Compass size={15}/> Расширенный поиск</Link>
      </section>

      {discovery.isLoading ? <LoadingBlock/> : discovery.data ? (
        <>
          <section className="section-block">
            <div className="section-heading"><h2><Sparkles size={18}/> {discovery.data.personalized ? "Для вас" : "Что посмотреть"}</h2><span>{discovery.data.recommended_publications?.length ?? 0} рекомендаций</span></div>
            {discovery.data.recommended_publications?.length ? <div className="feed-list">{discovery.data.recommended_publications.map((publication) => <PublicationCard key={publication.id} publication={publication}/>)}</div> : <EmptyState icon={Sparkles} title="Пока нечего рекомендовать" text="После появления публикаций здесь сформируется подборка."/>}
          </section>

          <section className="discovery-grid">
            <div className="discovery-panel">
              <div className="section-heading"><h2><Hash size={17}/> Популярные темы</h2></div>
              <div className="discovery-tags">{discovery.data.popular_tags.map((tag) => <Link href={`/search?scope=publications&tag=${encodeURIComponent(tag.slug)}`} key={tag.id}>#{tag.name}<span>{tag.publication_count}</span></Link>)}</div>
            </div>
            <div className="discovery-panel">
              <div className="section-heading"><h2><UsersRound size={17}/> Активные сообщества</h2></div>
              <div className="discovery-communities">{discovery.data.active_communities.map((community) => <Link href={`/communities/${community.id}`} key={community.id}><strong>{community.name}</strong><span>/{community.slug} · {community.publication_count} публикаций</span></Link>)}</div>
            </div>
          </section>

          <section className="section-block">
            <div className="section-heading"><h2>Открытые вопросы</h2><span>Без принятого ответа</span></div>
            {discovery.data.open_topics.length ? <div className="feed-list">{discovery.data.open_topics.map((publication) => <PublicationCard key={publication.id} publication={publication}/>)}</div> : <div className="inline-empty">Открытых вопросов сейчас нет.</div>}
          </section>
        </>
      ) : <div className="error-panel">Не удалось загрузить подборки.</div>}
    </AppShell>
  );
}
