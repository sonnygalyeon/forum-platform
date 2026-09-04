"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { EyeOff, ShieldCheck, ShieldX } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { CursorPage, User } from "@/lib/types";

type CommunityReport = {
  id: string;
  reporter: User;
  target_type: "publication" | "comment";
  target_id: string | null;
  reason: string;
  details: string;
  status: "open" | "reviewing" | "resolved" | "dismissed";
  moderator: User | null;
  resolution_note: string;
  created_at: string;
};

export default function CommunityModerationPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();
  const reports = useQuery({
    queryKey: ["community-moderation-reports", id],
    queryFn: () => clientApi<CursorPage<CommunityReport>>(`/communities/${id}/moderation/reports/`),
  });
  const statusMutation = useMutation({
    mutationFn: ({ reportId, status, note }: { reportId:string; status:CommunityReport["status"]; note:string }) => clientApi(`/communities/${id}/moderation/reports/${reportId}/`, { method:"PATCH", body:JSON.stringify({status,resolution_note:note}) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["community-moderation-reports", id] }),
  });
  const hideMutation = useMutation({
    mutationFn: async (report: CommunityReport) => {
      if (!report.target_id) return;
      const root = report.target_type === "publication" ? "publications" : "comments";
      await clientApi(`/communities/${id}/moderation/${root}/${report.target_id}/hidden/`, {
        method: "PUT",
        body: JSON.stringify({ report_id: report.id, reason: `Community moderation: ${report.reason}` }),
      });
      await clientApi(`/communities/${id}/moderation/reports/${report.id}/`, {
        method: "PATCH",
        body: JSON.stringify({ status: "resolved", resolution_note: "Контент скрыт модератором сообщества." }),
      });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["community-moderation-reports", id] });
      await queryClient.invalidateQueries({ queryKey: ["community-publications", id] });
    },
  });

  if (reports.isLoading) return <AppShell><LoadingBlock/></AppShell>;
  if (reports.isError) return <AppShell><div className="error-panel">Очередь модерации недоступна: {errorMessage(reports.error)}</div></AppShell>;

  return (
    <AppShell>
      <section className="page-head"><div><div className="eyebrow">COMMUNITY / MODERATION</div><h1>Очередь сообщества</h1><p>Здесь видны только жалобы на публикации и комментарии этого сообщества. Жалобы на пользователей остаются у глобальной модерации.</p></div><Link href={`/communities/${id}`} className="secondary-button">К сообществу</Link></section>
      <div className="community-moderation-list">
        {reports.data?.results.length ? reports.data.results.map((report) => (
          <article className="community-moderation-card" key={report.id}>
            <div className="community-moderation-head"><span className={`trust-status trust-status-${report.status}`}>{report.status}</span><time>{new Date(report.created_at).toLocaleString("ru-RU")}</time></div>
            <h2>{report.reason}</h2>
            <p>{report.details || "Без дополнительного описания."}</p>
            <div className="community-moderation-meta"><span>{report.target_type} · {report.target_id?.slice(0,8)}…</span><span>от @{report.reporter.nickname}</span></div>
            <div className="community-moderation-actions">
              {report.status === "open" ? <button className="secondary-button compact-button" onClick={() => statusMutation.mutate({reportId:report.id,status:"reviewing",note:""})}>Взять в работу</button> : null}
              {report.status === "open" || report.status === "reviewing" ? <button className="secondary-button compact-button" onClick={() => hideMutation.mutate(report)}><EyeOff size={14}/> Скрыть контент</button> : null}
              {report.status === "open" || report.status === "reviewing" ? <button className="secondary-button compact-button" onClick={() => statusMutation.mutate({reportId:report.id,status:"dismissed",note:"Нарушение не подтверждено модератором сообщества."})}><ShieldX size={14}/> Отклонить</button> : <span className="community-moderation-resolved"><ShieldCheck size={14}/>{report.resolution_note || "Рассмотрено"}</span>}
            </div>
          </article>
        )) : <div className="inline-empty"><ShieldCheck size={20}/> Активных обращений нет.</div>}
      </div>
    </AppShell>
  );
}
