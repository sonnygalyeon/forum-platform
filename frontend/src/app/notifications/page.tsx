"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellRing } from "lucide-react";
import Link from "next/link";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, Notification } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function NotificationsPage(){const {user,loading}=useAuth();const qc=useQueryClient();const query=useQuery({queryKey:["notifications"],queryFn:()=>clientApi<CursorPage<Notification>>("/notifications/"),enabled:Boolean(user)});const markAll=useMutation({mutationFn:()=>clientApi<{updated:number}>("/notifications/read-all/",{method:"PUT"}),onSuccess:()=>qc.invalidateQueries({queryKey:["notifications"]})});if(!loading&&!user)return <AppShell><EmptyState icon={BellRing} title="Уведомления доступны после входа" text="Здесь будут реальные ответы, подписки и события модерации." action={{href:"/login",label:"Войти"}}/></AppShell>;
return <AppShell><section className="page-head split-head"><div><div className="eyebrow">СОБЫТИЯ</div><h1>Уведомления</h1><p>Только события, созданные backend — никаких демонстрационных уведомлений.</p></div>{query.data?.results.some(n=>!n.is_read)?<button className="secondary-button" onClick={()=>markAll.mutate()}>Прочитать все</button>:null}</section>{query.isLoading?<LoadingBlock/>:query.data?.results.length?<div className="notification-list">{query.data.results.map(n=><article key={n.id} className={`notification-row ${n.is_read?"":"notification-unread"}`}><span className="notification-dot"/><div><strong>{n.actor?`@${n.actor.nickname}`:"Night Iris"}</strong><p>{n.comment?.excerpt || n.publication?.title || notificationLabel(n.kind)}</p><div className="meta-row"><time>{new Date(n.created_at).toLocaleString("ru-RU")}</time>{n.publication?<Link href={`/publications/${n.publication.id}`}>Открыть</Link>:null}</div></div></article>)}</div>:<EmptyState icon={BellRing} title="Пока тихо" text="Уведомления появятся после ответов, новых подписчиков и другой реальной активности."/>}</AppShell>}
function notificationLabel(kind:string){return kind.replaceAll("_"," ");}
