"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";
import Link from "next/link";
import { Plus, UsersRound } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { Community, CursorPage } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function CommunitiesPage(){
  const {user}=useAuth(); const qc=useQueryClient(); const [open,setOpen]=useState(false); const [slug,setSlug]=useState(""); const [name,setName]=useState(""); const [description,setDescription]=useState("");
  const query=useQuery({queryKey:["communities"],queryFn:()=>clientApi<CursorPage<Community>>("/communities/")});
  const create=useMutation({mutationFn:()=>clientApi<Community>("/communities/",{method:"POST",body:JSON.stringify({slug,name,description})}),onSuccess:()=>{setOpen(false);setSlug("");setName("");setDescription("");qc.invalidateQueries({queryKey:["communities"]})}});
  function submit(e:FormEvent){e.preventDefault();create.mutate()}
  return <AppShell><section className="page-head split-head"><div><div className="eyebrow">СООБЩЕСТВА</div><h1>Пространства по интересам</h1><p>Сообщества создаются пользователями и формируют персональную ленту подписчиков.</p></div>{user?<button className="primary-button" onClick={()=>setOpen(v=>!v)}><Plus size={15}/>{open?"Закрыть":"Создать сообщество"}</button>:null}</section>{open?<form className="settings-card community-create" onSubmit={submit}><div className="form-grid"><label>Название<input value={name} onChange={e=>setName(e.target.value)} minLength={3} maxLength={120} required placeholder="Backend Engineering"/></label><label>Slug<input value={slug} onChange={e=>setSlug(e.target.value.toLowerCase().replace(/[^a-z0-9-_]/g,""))} minLength={3} maxLength={80} required placeholder="backend-engineering"/></label></div><label>Описание<textarea rows={4} value={description} onChange={e=>setDescription(e.target.value)} maxLength={5000} placeholder="Для чего создано это сообщество?"/></label>{create.isError?<div className="form-error">{errorMessage(create.error)}</div>:null}<button className="primary-button" disabled={create.isPending}>{create.isPending?"Создаём…":"Создать"}</button></form>:null}{query.isLoading?<LoadingBlock/>:query.data?.results.length?<div className="community-grid">{query.data.results.map(c=><Link href={`/communities/${c.id}`} className="community-card" key={c.id}><div className="community-card-icon"><UsersRound size={20}/></div><div><h2>{c.name}</h2><span>/{c.slug}</span><p>{c.description||"Описание пока не заполнено."}</p></div><footer><span>{c.subscriber_count} подписчиков</span><span>{c.publication_count} публикаций</span></footer></Link>)}</div>:<EmptyState icon={UsersRound} title="Сообществ пока нет" text={user?"Создайте первое тематическое пространство Night Iris.":"После регистрации вы сможете создать первое сообщество."} action={user?undefined:{href:"/register",label:"Создать аккаунт"}}/>}</AppShell>
}
