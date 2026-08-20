"use client";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, User } from "@/lib/types";

type Revision={revision:number;title:string;edited_by:User;created_at:string};
export default function RevisionsPage(){const {id}=useParams<{id:string}>();const q=useQuery({queryKey:["revisions",id],queryFn:()=>clientApi<CursorPage<Revision>>(`/publications/${id}/revisions/`)});return <AppShell><section className="page-head"><div><div className="eyebrow">ИСТОРИЯ</div><h1>Ревизии публикации</h1><p>Каждое изменение сохраняется отдельно и не перезаписывает историю.</p></div></section>{q.isLoading?<LoadingBlock/>:q.data?.results.length?<div className="revision-list">{q.data.results.map(r=><article key={r.revision}><div><strong>Revision {r.revision}</strong><span>{r.title||"Без заголовка"}</span></div><small>@{r.edited_by.nickname} · {new Date(r.created_at).toLocaleString("ru-RU")}</small></article>)}</div>:<div className="inline-empty">История пока пуста.</div>}<Link href={`/publications/${id}`} className="secondary-button">Назад к публикации</Link></AppShell>}
