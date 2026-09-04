"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Flag, ShieldCheck } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, User } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

type MyReport = {
  id: string;
  target_type: "publication" | "comment" | "user";
  target_id: string | null;
  reason: string;
  details: string;
  status: "open" | "reviewing" | "resolved" | "dismissed";
  moderator: User | null;
  resolution_note: string;
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
};

const statusLabels: Record<MyReport["status"], string> = {
  open: "Открыта",
  reviewing: "На проверке",
  resolved: "Решена",
  dismissed: "Отклонена",
};
const reasonLabels: Record<string, string> = {
  spam: "Спам",
  harassment: "Преследование",
  hate: "Ненависть",
  violence: "Насилие",
  illegal: "Незаконный контент",
  personal_data: "Персональные данные",
  copyright: "Авторские права",
  other: "Другое",
};

function targetHref(report: MyReport) {
  if (!report.target_id) return null;
  if (report.target_type === "publication") return `/publications/${report.target_id}`;
  if (report.target_type === "user") return `/users/${report.target_id}`;
  return null;
}

export default function MyReportsPage() {
  const { user, loading } = useAuth();
  const reports = useQuery({
    queryKey: ["my-reports"],
    queryFn: () => clientApi<CursorPage<MyReport>>("/reports/mine/"),
    enabled: Boolean(user),
  });

  if (loading) return <AppShell><LoadingBlock/></AppShell>;
  if (!user) return <AppShell><EmptyState icon={Flag} title="Нужен аккаунт" text="История ваших обращений доступна после входа." action={{href:"/login",label:"Войти"}}/></AppShell>;

  return (
    <AppShell>
      <section className="page-head"><div><div className="eyebrow">TRUST / REPORTS</div><h1>Мои обращения</h1><p>Статус жалоб и решение модерации остаются видимыми, чтобы обращения не исчезали в административной чёрной дыре.</p></div></section>
      {reports.isLoading ? <LoadingBlock/> : reports.data?.results.length ? (
        <div className="trust-report-list">{reports.data.results.map((report) => {
          const href = targetHref(report);
          return <article className="trust-report-card" key={report.id}>
            <div className="trust-report-card-head"><span className={`trust-status trust-status-${report.status}`}>{statusLabels[report.status]}</span><time>{new Date(report.created_at).toLocaleString("ru-RU")}</time></div>
            <h2>{reasonLabels[report.reason] ?? report.reason}</h2>
            <p>{report.details || "Без дополнительного комментария."}</p>
            {report.resolution_note ? <div className="trust-resolution"><ShieldCheck size={15}/><span><strong>Решение модерации</strong>{report.resolution_note}</span></div> : null}
            <div className="trust-report-meta"><span>{report.target_type === "publication" ? "Публикация" : report.target_type === "comment" ? "Комментарий" : "Пользователь"}</span>{href ? <Link href={href}>Открыть объект</Link> : null}</div>
          </article>;
        })}</div>
      ) : <EmptyState icon={ShieldCheck} title="Обращений нет" text="Здесь появятся ваши жалобы и результаты их рассмотрения."/>}
    </AppShell>
  );
}
