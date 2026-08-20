"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { BellPlus, BellMinus, PenSquare, UsersRound } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { PublicationCard } from "@/components/feed/publication-card";
import { UserAvatar } from "@/components/profile/user-avatar";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { Community, CursorPage, Publication } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function CommunityPage(){const {id}=useParams<{id:string}>();const {user}=useAuth();const qc=useQueryClient();const community=useQuery({queryKey:["community",id],queryFn:()=>clientApi<Community>(`/communities/${id}/`)});const posts=useQuery({queryKey:["community-publications",id],queryFn:()=>clientApi<CursorPage<Publication>>(`/publications/?community=${id}`)});const subscription=useMutation({mutationFn:(method:"PUT"|"DELETE")=>clientApi(`/communities/${id}/subscription/`,{method}),onSuccess:()=>{qc.invalidateQueries({queryKey:["community",id]});qc.invalidateQueries({queryKey:["home-feed"]})}});if(community.isLoading)return <AppShell><LoadingBlock/></AppShell>;if(!community.data)return <AppShell><div className="error-panel">Сообщество не найдено.</div></AppShell>;const c=community.data;return <AppShell><section className="community-hero"><div className="community-symbol"><UsersRound size={29}/></div><div><div className="eyebrow">/{c.slug}</div><h1>{c.name}</h1><p>{c.description||"Описание сообщества пока не заполнено."}</p><div className="community-owner"><UserAvatar user={c.owner} size="xs"/><span>создано <Link href={`/users/${c.owner.id}`}>@{c.owner.nickname}</Link> · {c.subscriber_count} подписчиков · {c.publication_count} публикаций</span></div></div>{user?<div className="community-hero-actions"><button className={c.is_subscribed?"secondary-button":"primary-button"} onClick={()=>subscription.mutate(c.is_subscribed?"DELETE":"PUT")}>{c.is_subscribed?<><BellMinus size={15}/>Отписаться</>:<><BellPlus size={15}/>Подписаться</>}</button><Link href="/new" className="secondary-button"><PenSquare size={15}/>Написать</Link></div>:null}</section><section className="section-block"><div className="section-heading"><h2>Публикации</h2></div>{posts.isLoading?<LoadingBlock/>:posts.data?.results.length?<div className="feed-list">{posts.data.results.map(p=><PublicationCard key={p.id} publication={p}/>)}</div>:<EmptyState title="Здесь пока пусто" text="Первая публикация в сообществе появится здесь." action={user?{href:"/new",label:"Создать публикацию"}:undefined}/>}</section></AppShell>}
