"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { SocialUserList } from "@/components/profile/social-user-list";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, SocialUserEdge, User } from "@/lib/types";

export default function FollowersPage(){
  const {id}=useParams<{id:string}>();
  const profile=useQuery({queryKey:["user",id],queryFn:()=>clientApi<User>(`/users/${id}/`)});
  const list=useQuery({queryKey:["followers",id],queryFn:()=>clientApi<CursorPage<SocialUserEdge>>(`/users/${id}/followers/`)});
  return <AppShell><section className="page-head"><div><div className="eyebrow">СОЦИАЛЬНЫЙ ГРАФ</div><h1>Подписчики {profile.data?`@${profile.data.nickname}`:""}</h1><p>Люди, которые получают публикации этого автора в своей ленте подписок.</p></div></section>{list.isLoading?<LoadingBlock/>:<SocialUserList edges={list.data?.results??[]} empty="Подписчиков пока нет."/>}</AppShell>;
}
