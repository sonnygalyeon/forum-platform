"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { SocialGraphList } from "@/components/profile/social-graph-list";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { Page, SocialGraphConnection, User } from "@/lib/types";

export default function MutualsPage(){
  const {id}=useParams<{id:string}>();
  const [q,setQ]=useState("");
  const [page,setPage]=useState(1);
  const profile=useQuery({queryKey:["user",id],queryFn:()=>clientApi<User>("/users/"+id+"/")});
  const list=useQuery({
    queryKey:["social-mutuals",id,q,page],
    queryFn:()=>clientApi<Page<SocialGraphConnection>>("/social/users/"+id+"/mutuals/?page="+page+"&q="+encodeURIComponent(q)),
  });

  return <AppShell>
    <section className="page-head">
      <div>
        <div className="eyebrow">СОЦИАЛЬНЫЙ ГРАФ</div>
        <h1>Общие связи {profile.data?"с @"+profile.data.nickname:""}</h1>
        <p>Аккаунты, на которые подписаны и вы, и этот пользователь.</p>
      </div>
    </section>

    <div className="social-graph-toolbar">
      <input
        className="text-input"
        value={q}
        onChange={(event)=>{setQ(event.target.value);setPage(1);}}
        placeholder="Найти среди общих связей"
        aria-label="Найти среди общих связей"
      />
      <span>{list.data?.count??0} человек</span>
    </div>

    {list.isLoading?<LoadingBlock/>:<SocialGraphList items={list.data?.results??[]} empty="Общих подписок пока нет."/>}

    <div className="social-graph-pagination">
      <button className="secondary-button" disabled={!list.data?.previous} onClick={()=>setPage(value=>Math.max(1,value-1))}>Назад</button>
      <span>Страница {page}</span>
      <button className="secondary-button" disabled={!list.data?.next} onClick={()=>setPage(value=>value+1)}>Дальше</button>
    </div>
  </AppShell>;
}
