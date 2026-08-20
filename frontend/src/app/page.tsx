"use client";

import { useQuery } from "@tanstack/react-query";
import { FilePlus2, Sparkles } from "lucide-react";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { PublicationCard } from "@/components/feed/publication-card";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, Publication } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function HomePage() {
  const { user, loading: authLoading } = useAuth(); const [mode,setMode]=useState<"latest"|"following">("latest");
  const query = useQuery({ queryKey: ["home-feed", mode, Boolean(user)], queryFn: () => clientApi<CursorPage<Publication>>(mode === "following" && user ? "/feed/" : "/publications/"), enabled: !authLoading && (mode === "latest" || Boolean(user)) });
  return <AppShell><section className="page-head"><div><div className="eyebrow">NIGHT IRIS / ЛЕНТА</div><h1>{user ? `Добро пожаловать, ${user.nickname}` : "Обсуждения без шума"}</h1><p>{mode==="following"?"Публикации людей и сообществ, на которые вы подписаны.":"Свежие публичные публикации Night Iris."}</p></div></section>{user?<div className="feed-tabs"><button className={mode==="latest"?"active":""} onClick={()=>setMode("latest")}>Последние</button><button className={mode==="following"?"active":""} onClick={()=>setMode("following")}>Подписки</button></div>:null}{query.isLoading ? <LoadingBlock/> : query.isError ? <div className="error-panel">Backend недоступен. Проверьте Django API.</div> : query.data?.results.length ? <div className="feed-list">{query.data.results.map(item => <PublicationCard key={item.id} publication={item}/>)}</div> : <EmptyState icon={user ? FilePlus2 : Sparkles} title={mode==="following"?"Лента подписок пока пуста":"Форум пока пуст"} text={mode==="following"?"Подпишитесь на автора или сообщество — новые публикации появятся здесь.":user?"Создайте первую публикацию Night Iris.":"Пока никто ничего не опубликовал. Зарегистрируйтесь и станьте первым автором."} action={user ? {href:"/new",label:"Создать публикацию"} : {href:"/register",label:"Создать аккаунт"}}/>}</AppShell>;
}
