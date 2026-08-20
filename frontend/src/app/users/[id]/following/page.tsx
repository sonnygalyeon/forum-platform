"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { SocialUserList } from "@/components/profile/social-user-list";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, SocialUserEdge, User } from "@/lib/types";

export default function FollowingPage(){
  const {id}=useParams<{id:string}>();
  const profile=useQuery({queryKey:["user",id],queryFn:()=>clientApi<User>(`/users/${id}/`)});
  const list=useQuery({queryKey:["following",id],queryFn:()=>clientApi<CursorPage<SocialUserEdge>>(`/users/${id}/following/`)});
  return <AppShell><section className="page-head"><div><div className="eyebrow">СОЦИАЛЬНЫЙ ГРАФ</div><h1>Подписки {profile.data?`@${profile.data.nickname}`:""}</h1><p>Авторы, за публикациями которых следит пользователь.</p></div></section>{list.isLoading?<LoadingBlock/>:<SocialUserList edges={list.data?.results??[]} empty="Пользователь пока ни на кого не подписан."/>}</AppShell>;
}
