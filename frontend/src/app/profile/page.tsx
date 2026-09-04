"use client";

import { useQuery } from "@tanstack/react-query";
import { Edit3, Gauge, LogOut, Palette, UserRound } from "lucide-react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { PublicationCard } from "@/components/feed/publication-card";
import { ProfileBanner } from "@/components/profile/profile-banner";
import { UserAvatar } from "@/components/profile/user-avatar";
import { AnswerCard } from "@/components/profile/answer-card";
import { IdentitySummary } from "@/components/profile/identity-summary";
import { clientApi } from "@/lib/client-api";
import type { Comment, CursorPage, Publication, User } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function ProfilePage(){
  const router=useRouter();const {user,loading,logout}=useAuth();const [tab,setTab]=useState<"publications"|"answers">("publications");
  const publicProfile=useQuery({queryKey:["profile",user?.id],queryFn:()=>clientApi<User>(`/users/${user!.id}/`),enabled:Boolean(user)});
  const publications=useQuery({queryKey:["profile-publications",user?.id],queryFn:()=>clientApi<CursorPage<Publication>>(`/publications/?author=${user!.id}`),enabled:Boolean(user)});
  const answers=useQuery({queryKey:["profile-answers",user?.id],queryFn:()=>clientApi<CursorPage<Comment>>(`/users/${user!.id}/answers/`),enabled:Boolean(user)});
  if(loading)return <AppShell><LoadingBlock/></AppShell>;
  if(!user)return <AppShell><EmptyState icon={UserRound} title="Профиль доступен после входа" text="Зарегистрируйтесь, чтобы создать социальный профиль Night Iris." action={{href:"/register",label:"Создать аккаунт"}}/></AppShell>;
  const profile=publicProfile.data??user;async function signOut(){await logout();router.push("/");}
  return <AppShell>
    <section className="profile-shell"><ProfileBanner user={profile}/><div className="profile-main"><UserAvatar user={profile} size="xl"/><div className="profile-copy"><div className="profile-title-row"><div><h1>{[user.first_name,user.last_name].filter(Boolean).join(" ")||user.nickname}</h1><span>@{user.nickname}</span></div><div className="profile-actions"><Link href="/profile/edit" className="primary-button"><Edit3 size={14}/>Настроить профиль</Link><Link href="/profile/identity" className="secondary-button"><Palette size={14}/>Стиль и бейджи</Link><Link href="/profile/progress" className="secondary-button"><Gauge size={14}/>Прогресс</Link><button className="secondary-button" onClick={signOut}><LogOut size={14}/> Выйти</button></div></div><>{profile.identity.headline?<div className="profile-headline">{profile.identity.headline}</div>:null}<p>{user.bio||"Описание профиля пока не заполнено."}</p><div className="profile-meta"><Link href={`/users/${user.id}/followers`}>{profile.follower_count??0} подписчиков</Link> · <Link href={`/users/${user.id}/following`}>{profile.following_count??0} подписок</Link> · {profile.country} · с {new Date(user.date_joined).toLocaleDateString("ru-RU")}</div><IdentitySummary identity={profile.identity}/></></div></div></section>
    <div className="profile-stats"><div className="stat-box"><strong>{publications.data?.results.length??0}</strong><span>публикаций на странице</span></div><div className="stat-box"><strong>{answers.data?.results.length??0}</strong><span>ответов на странице</span></div><div className="stat-box"><strong>{profile.follower_count??0}</strong><span>подписчиков</span></div></div>
    <div className="profile-tabs"><button className={tab==="publications"?"active":""} onClick={()=>setTab("publications")}>Публикации</button><button className={tab==="answers"?"active":""} onClick={()=>setTab("answers")}>Ответы</button></div>
    <section className="section-block">{tab==="publications"?(publications.isLoading?<LoadingBlock/>:publications.data?.results.length?<div className="feed-list">{publications.data.results.map(p=><PublicationCard key={p.id} publication={p}/>)}</div>:<div className="inline-empty">Вы ещё ничего не публиковали.</div>):(answers.isLoading?<LoadingBlock/>:answers.data?.results.length?<div className="answer-list">{answers.data.results.map(a=><AnswerCard key={a.id} answer={a}/>)}</div>:<div className="inline-empty">Вы ещё не отвечали на вопросы.</div>)}</section>
  </AppShell>;
}
