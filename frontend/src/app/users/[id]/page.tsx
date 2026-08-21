"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { BellOff, MessageCircle, ShieldBan, UserMinus, UserPlus } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { ProfileBanner } from "@/components/profile/profile-banner";
import { UserAvatar } from "@/components/profile/user-avatar";
import { PublicationCard } from "@/components/feed/publication-card";
import { AnswerCard } from "@/components/profile/answer-card";
import { IdentitySummary } from "@/components/profile/identity-summary";
import { LoadingBlock } from "@/components/ui/loading";
import { EmptyState } from "@/components/ui/empty-state";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { Comment, CursorPage, Publication, User } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function PublicProfilePage(){
  const {id}=useParams<{id:string}>(); const router=useRouter(); const {user:me}=useAuth(); const qc=useQueryClient(); const [tab,setTab]=useState<"publications"|"answers">("publications");
  const profile=useQuery({queryKey:["user",id],queryFn:()=>clientApi<User>(`/users/${id}/`)});
  const publications=useQuery({queryKey:["user-publications",id],queryFn:()=>clientApi<CursorPage<Publication>>(`/publications/?author=${id}`)});
  const answers=useQuery({queryKey:["user-answers",id],queryFn:()=>clientApi<CursorPage<Comment>>(`/users/${id}/answers/`)});
  const refresh=()=>qc.invalidateQueries({queryKey:["user",id]});
  const follow=useMutation({mutationFn:(method:"PUT"|"DELETE")=>clientApi(`/users/${id}/follow/`,{method}),onSuccess:refresh});
  const mute=useMutation({mutationFn:(method:"PUT"|"DELETE")=>clientApi(`/users/${id}/mute/`,{method}),onSuccess:refresh});
  const message=useMutation({mutationFn:()=>clientApi<{id:string}>("/messenger/conversations/direct/",{method:"POST",body:JSON.stringify({user_id:id})}),onSuccess:c=>router.push(`/messages/${c.id}`)});
  const block=useMutation({mutationFn:(method:"PUT"|"DELETE")=>clientApi(`/users/${id}/block/`,{method}),onSuccess:refresh});
  if(profile.isLoading)return <AppShell><LoadingBlock/></AppShell>;
  if(!profile.data)return <AppShell><div className="error-panel">Пользователь не найден.</div></AppShell>;
  const p=profile.data; const own=me?.id===p.id;
  return <AppShell>
    <section className="profile-shell"><ProfileBanner user={p}/><div className="profile-main"><UserAvatar user={p} size="xl"/><div className="profile-copy"><div className="profile-title-row"><div><h1>{[p.first_name,p.last_name].filter(Boolean).join(" ")||p.nickname}</h1><span>@{p.nickname}</span></div>{!own&&me?<div className="profile-actions"><button className="secondary-button" onClick={()=>message.mutate()} disabled={p.is_blocked||message.isPending}><MessageCircle size={14}/>Сообщение</button><button className={p.is_following?"secondary-button":"primary-button"} onClick={()=>follow.mutate(p.is_following?"DELETE":"PUT")}>{p.is_following?<><UserMinus size={14}/>Отписаться</>:<><UserPlus size={14}/>Подписаться</>}</button><button className="icon-button" title={p.is_muted?"Включить автора":"Не показывать в ленте"} onClick={()=>mute.mutate(p.is_muted?"DELETE":"PUT")}><BellOff size={15}/></button><button className={`icon-button ${p.is_blocked?"danger-button":""}`} title={p.is_blocked?"Разблокировать":"Заблокировать"} onClick={()=>block.mutate(p.is_blocked?"DELETE":"PUT")}><ShieldBan size={15}/></button></div>:null}</div><>{p.identity.headline?<div className="profile-headline">{p.identity.headline}</div>:null}<p>{p.bio||"Описание профиля пока не заполнено."}</p><div className="profile-meta"><Link href={`/users/${p.id}/followers`}>{p.follower_count??0} подписчиков</Link> · <Link href={`/users/${p.id}/following`}>{p.following_count??0} подписок</Link> · {p.country} · с {new Date(p.date_joined).toLocaleDateString("ru-RU")}</div><IdentitySummary identity={p.identity}/>{follow.isError||mute.isError||block.isError?<div className="form-error">{errorMessage(follow.error||mute.error||block.error)}</div>:null}</></div></div></section>
    <div className="profile-stats"><div className="stat-box"><strong>{publications.data?.results.length??0}</strong><span>публикаций на странице</span></div><div className="stat-box"><strong>{answers.data?.results.length??0}</strong><span>ответов на странице</span></div><div className="stat-box"><strong>{p.follower_count??0}</strong><span>подписчиков</span></div></div>
    <div className="profile-tabs"><button className={tab==="publications"?"active":""} onClick={()=>setTab("publications")}>Публикации</button><button className={tab==="answers"?"active":""} onClick={()=>setTab("answers")}>Ответы</button></div>
    <section className="section-block">{tab==="publications"?(publications.isLoading?<LoadingBlock/>:publications.data?.results.length?<div className="feed-list">{publications.data.results.map(item=><PublicationCard key={item.id} publication={item}/>)}</div>:<EmptyState title="Публикаций пока нет" text="Здесь появятся реальные публикации пользователя."/>):(answers.isLoading?<LoadingBlock/>:answers.data?.results.length?<div className="answer-list">{answers.data.results.map(a=><AnswerCard key={a.id} answer={a}/>)}</div>:<EmptyState title="Ответов пока нет" text="Здесь появятся ответы пользователя на вопросы."/>)}</section>
  </AppShell>;
}
