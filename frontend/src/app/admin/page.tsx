"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, ArrowRight, CircleUserRound, FileText, MessageSquareText, UsersRound } from "lucide-react";
import { MetricCard } from "@/components/admin/admin-ui";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { AdminOverview } from "@/lib/types";

export default function AdminOverviewPage(){
 const q=useQuery({queryKey:["admin","overview"],queryFn:()=>clientApi<AdminOverview>("/admin/overview/")});
 if(q.isLoading)return <LoadingBlock/>; if(q.error)return <div className="error-panel">{errorMessage(q.error)}</div>; const d=q.data!;
 return <><div className="admin-page-head"><div><div className="eyebrow">NIGHT IRIS CONTROL</div><h1>Обзор</h1><p>Только реальные данные текущей базы. Здесь нет демонстрационных показателей.</p></div><span className="admin-updated">Обновлено {new Date(d.generated_at).toLocaleTimeString("ru-RU",{hour:"2-digit",minute:"2-digit"})}</span></div>
 <section className="admin-metric-grid"><MetricCard label="Пользователи" value={d.users.total} detail={`+${d.users.joined_last_7d} за 7 дней`}/><MetricCard label="Публикации" value={d.publications.total} detail={`${d.publications.created_last_24h} за 24 часа`}/><MetricCard label="Комментарии" value={d.comments.total} detail={`${d.comments.created_last_24h} за 24 часа`}/><MetricCard label="Открытые жалобы" value={d.reports.open} detail={`${d.reports.reviewing} на проверке`} tone={d.reports.open?"warning":"normal"}/><MetricCard label="Скрытый контент" value={d.publications.hidden+d.comments.hidden} detail={`${d.publications.hidden} публикаций · ${d.comments.hidden} ответов`} tone={d.publications.hidden+d.comments.hidden?"warning":"normal"}/><MetricCard label="Сбои событий" value={d.notification_events.failed} detail={`${d.notification_events.pending} ожидают обработки`} tone={d.notification_events.failed?"danger":"normal"}/></section>
 <section className="admin-section"><div className="admin-section-title"><h2>Быстрые действия</h2><span>Основные рабочие разделы</span></div><div className="admin-shortcuts"><Link href="/admin/reports"><AlertTriangle/><div><strong>Разобрать жалобы</strong><span>{d.reports.open+d.reports.reviewing} требуют внимания</span></div><ArrowRight/></Link><Link href="/admin/users"><CircleUserRound/><div><strong>Пользователи</strong><span>{d.users.active} активных · {d.users.staff} сотрудников</span></div><ArrowRight/></Link><Link href="/admin/content"><FileText/><div><strong>Контент</strong><span>{d.publications.published} публикаций доступны</span></div><ArrowRight/></Link><Link href="/admin/communities"><UsersRound/><div><strong>Сообщества</strong><span>{d.communities.active} активных</span></div><ArrowRight/></Link></div></section>
 <section className="admin-section admin-policy"><MessageSquareText/><div><strong>Принцип модерации Night Iris</strong><p>Публикации и комментарии не удаляются через панель. Модератор скрывает или восстанавливает их, а действие остаётся в журнале.</p></div></section></>;
}
