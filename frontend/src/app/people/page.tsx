"use client";

import { useQuery } from "@tanstack/react-query";
import { Sparkles, UsersRound } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { SocialGraphList } from "@/components/profile/social-graph-list";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { Page, SocialRecommendation } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function PeoplePage(){
  const {user,loading}=useAuth();
  const [page,setPage]=useState(1);
  const recommendations=useQuery({
    queryKey:["social-recommendations",page],
    queryFn:()=>clientApi<Page<SocialRecommendation>>("/social/recommendations/?page="+page),
    enabled:Boolean(user),
  });

  if(loading)return <AppShell><LoadingBlock/></AppShell>;

  return <AppShell>
    <section className="page-head">
      <div>
        <div className="eyebrow">SOCIAL GRAPH / NIGHT IRIS</div>
        <h1>Люди, с которыми есть контекст</h1>
        <p>Рекомендации строятся по общим подпискам, сообществам, интересам и пересечениям в обсуждениях. Никакой мистической оценки личности, человечеству и без неё хватает странных рейтингов.</p>
      </div>
      <UsersRound size={28}/>
    </section>

    {!user?(
      <EmptyState icon={UsersRound} title="Войдите, чтобы увидеть рекомендации" text="Социальный граф рассчитывается относительно вашего аккаунта."/>
    ):recommendations.isLoading?(
      <LoadingBlock/>
    ):(
      <>
        <section className="section-block">
          <div className="section-heading">
            <h2><Sparkles size={18}/>Для вас</h2>
            <span>{recommendations.data?.count??0} рекомендаций</span>
          </div>
          <SocialGraphList items={recommendations.data?.results??[]} empty="Пока не нашли подходящих людей. После активности в сообществах рекомендации станут точнее."/>
        </section>
        <div className="social-graph-pagination">
          <button className="secondary-button" disabled={!recommendations.data?.previous} onClick={()=>setPage(value=>Math.max(1,value-1))}>Назад</button>
          <span>Страница {page}</span>
          <button className="secondary-button" disabled={!recommendations.data?.next} onClick={()=>setPage(value=>value+1)}>Дальше</button>
        </div>
      </>
    )}
  </AppShell>;
}
