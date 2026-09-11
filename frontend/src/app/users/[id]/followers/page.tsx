"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { SocialGraphList } from "@/components/profile/social-graph-list";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { Page, SocialGraphConnection, User } from "@/lib/types";

export default function FollowersPage(){
  const {id}=useParams<{id:string}>();
  const [q,setQ]=useState("");
  const [page,setPage]=useState(1);
  const profile=useQuery({queryKey:["user",id],queryFn:()=>clientApi<User>("/users/"+id+"/")});
  const list=useQuery({
    queryKey:["social-followers",id,q,page],
    queryFn:()=>clientApi<Page<SocialGraphConnection>>("/social/users/"+id+"/followers/?page="+page+"&q="+encodeURIComponent(q)),
  });

  return <AppShell>
    <section className="page-head">
      <div>
        <div className="eyebrow">СОЦИАЛЬНЫЙ ГРАФ</div>
        <h1>Подписчики {profile.data?"@"+profile.data.nickname:""}</h1>
        <p>Подписчики с контекстом общих связей, сообществ и интересов.</p>
      </div>
    </section>

    <div className="social-graph-toolbar">
      <input
        className="text-input"
        value={q}
        onChange={(event)=>{setQ(event.target.value);setPage(1);}}
        placeholder="Найти среди подписчиков"
        aria-label="Найти среди подписчиков"
      />
      <span>{list.data?.count??0} человек</span>
    </div>

    {list.isLoading?<LoadingBlock/>:<SocialGraphList items={list.data?.results??[]} empty="Подписчиков пока нет."/>}

    <div className="social-graph-pagination">
      <button className="secondary-button" disabled={!list.data?.previous} onClick={()=>setPage(value=>Math.max(1,value-1))}>Назад</button>
      <span>Страница {page}</span>
      <button className="secondary-button" disabled={!list.data?.next} onClick={()=>setPage(value=>value+1)}>Дальше</button>
    </div>
  </AppShell>;
}
