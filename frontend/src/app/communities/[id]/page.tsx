"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { BellMinus, BellPlus, PenSquare, ShieldCheck, UsersRound } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { CommunitySettingsPanel } from "@/components/community/community-settings-panel";
import { CommunityStaffPanel } from "@/components/community/community-staff-panel";
import { PublicationCard } from "@/components/feed/publication-card";
import { UserAvatar } from "@/components/profile/user-avatar";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { Community, CursorPage, Publication } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

type CommunityWithPermissions = Community & { can_edit?: boolean };

const roleLabels: Record<string, string> = {
  owner: "Владелец",
  moderator: "Модератор",
  editor: "Редактор",
  subscriber: "Подписчик",
};

export default function CommunityPage() {
  const { id } = useParams<{id:string}>();
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const community = useQuery({ queryKey:["community",id], queryFn:()=>clientApi<CommunityWithPermissions>(`/communities/${id}/`) });
  const posts = useQuery({ queryKey:["community-publications",id], queryFn:()=>clientApi<CursorPage<Publication>>(`/publications/?community=${id}`) });
  const subscription = useMutation({
    mutationFn:(method:"PUT"|"DELETE")=>clientApi(`/communities/${id}/subscription/`,{method}),
    onSuccess:async()=>{
      await Promise.all([
        queryClient.invalidateQueries({queryKey:["community",id]}),
        queryClient.invalidateQueries({queryKey:["home-feed"]}),
      ]);
    },
  });
  if (community.isLoading) return <AppShell><LoadingBlock/></AppShell>;
  if (!community.data) return <AppShell><div className="error-panel">Сообщество не найдено.</div></AppShell>;
  const current = community.data;
  return (
    <AppShell>
      <section className="community-hero">
        <div className="community-symbol"><UsersRound size={29}/></div>
        <div>
          <div className="eyebrow">/{current.slug}</div>
          <h1>{current.name}</h1>
          <p>{current.description||"Описание сообщества пока не заполнено."}</p>
          <div className="community-owner"><UserAvatar user={current.owner} size="xs"/><span>создано <Link href={`/users/${current.owner.id}`}>@{current.owner.nickname}</Link> · {current.subscriber_count} подписчиков · {current.publication_count} публикаций</span></div>
          {current.my_role ? <div className="community-role-chip"><ShieldCheck size={13}/>{roleLabels[current.my_role] ?? current.my_role}</div> : null}
        </div>
        {user?<div className="community-hero-actions"><button className={current.is_subscribed?"secondary-button":"primary-button"} onClick={()=>subscription.mutate(current.is_subscribed?"DELETE":"PUT")}>{current.is_subscribed?<><BellMinus size={15}/>Отписаться</>:<><BellPlus size={15}/>Подписаться</>}</button><Link href="/new" className="secondary-button"><PenSquare size={15}/>Написать</Link></div>:null}
      </section>

      {current.can_edit ? <CommunitySettingsPanel community={current}/> : null}
      {(current.staff_count ?? 0) > 0 || current.can_manage ? <CommunityStaffPanel communityId={current.id} canManage={Boolean(current.can_manage)}/> : null}

      <section className="section-block">
        <div className="section-heading"><h2>Публикации</h2></div>
        {posts.isLoading?<LoadingBlock/>:posts.data?.results.length?<div className="feed-list">{posts.data.results.map((publication)=><PublicationCard key={publication.id} publication={publication}/>)}</div>:<EmptyState title="Здесь пока пусто" text="Первая публикация в сообществе появится здесь." action={user?{href:"/new",label:"Создать публикацию"}:undefined}/>} 
      </section>
    </AppShell>
  );
}
