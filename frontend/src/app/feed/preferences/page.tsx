"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { RotateCcw, SlidersHorizontal } from "lucide-react";
import Link from "next/link";

import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, FeedFeedbackItem } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

const reasonLabels = {
  not_interested: "Не интересно",
  too_repetitive: "Слишком много похожего",
  already_seen: "Уже видел",
} as const;

export default function FeedPreferencesPage(){
  const {user,loading}=useAuth();
  const qc=useQueryClient();
  const query=useQuery({
    queryKey:["feed-feedback-history"],
    queryFn:()=>clientApi<CursorPage<FeedFeedbackItem>>("/feed/feedback/"),
    enabled:Boolean(user),
  });
  const restore=useMutation({
    mutationFn:(publicationId:string)=>clientApi<{reason:null}>("/publications/"+publicationId+"/feed-feedback/",{method:"DELETE"}),
    onSuccess:()=>{
      void qc.invalidateQueries({queryKey:["feed-feedback-history"]});
      void qc.invalidateQueries({queryKey:["home-feed"]});
    },
  });

  if(!loading&&!user)return <AppShell><EmptyState icon={SlidersHorizontal} title="Настройки ленты доступны после входа" text="Здесь можно вернуть скрытые публикации."/></AppShell>;

  return <AppShell>
    <section className="page-head split-head">
      <div>
        <div className="eyebrow">NIGHT IRIS / ЛЕНТА</div>
        <h1>Настройки ленты</h1>
        <p>Публикации, которые вы скрыли из «Для вас». Любое решение можно отменить.</p>
      </div>
      <Link href="/" className="secondary-button">Вернуться в ленту</Link>
    </section>

    {query.isLoading?<LoadingBlock/>:query.data?.results.length?
      <div className="feed-preference-list">
        {query.data.results.map(item=><article className="feed-preference-row" key={item.publication.id}>
          <div>
            <span className="status-chip">{reasonLabels[item.reason]}</span>
            <Link href={"/publications/"+item.publication.id}><strong>{item.publication.title||item.publication.excerpt.slice(0,90)||"Публикация"}</strong></Link>
            <small>@{item.publication.author.nickname} · {new Date(item.updated_at).toLocaleDateString("ru-RU")}</small>
          </div>
          <button
            className="secondary-button compact-button"
            disabled={restore.isPending&&restore.variables===item.publication.id}
            onClick={()=>restore.mutate(item.publication.id)}
          ><RotateCcw size={13}/>Вернуть</button>
        </article>)}
      </div>
      :<EmptyState icon={SlidersHorizontal} title="Скрытых публикаций нет" text="Night Iris пока ничего не исключает из вашей персональной ленты по явному feedback."/>}
  </AppShell>;
}
