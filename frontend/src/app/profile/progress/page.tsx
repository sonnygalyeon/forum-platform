"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowRight, Gauge, Sparkles, Trophy } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import { useAuth } from "@/providers/auth-provider";

type IdentityProgress = {
  reputation: number;
  level: number;
  current_level_threshold: number;
  next_level_threshold: number | null;
  points_to_next_level: number;
  progress_percent: number;
  metrics: { publications:number; answers:number; accepted:number; followers:number; communities:number; positive_score:number };
  point_breakdown: { publications:number; answers:number; accepted_answers:number; positive_score:number; followers:number };
};

const rows: Array<[keyof IdentityProgress["point_breakdown"], string, string]> = [
  ["publications", "Публикации", "2 балла за опубликованный материал"],
  ["answers", "Ответы", "3 балла за опубликованный ответ"],
  ["accepted_answers", "Принятые ответы", "15 дополнительных баллов"],
  ["positive_score", "Положительная оценка", "2 балла за каждый положительный балл ответов/комментариев"],
  ["followers", "Подписчики", "1 балл за подписчика"],
];

export default function IdentityProgressPage() {
  const { user, loading } = useAuth();
  const progress = useQuery({
    queryKey: ["identity-progress"],
    queryFn: () => clientApi<IdentityProgress>("/identity/me/progress/"),
    enabled: Boolean(user),
  });
  if (loading) return <AppShell><LoadingBlock/></AppShell>;
  if (!user) return <AppShell><EmptyState icon={Gauge} title="Нужен аккаунт" text="Прогресс репутации рассчитывается для вашего профиля." action={{href:"/login",label:"Войти"}}/></AppShell>;
  if (progress.isLoading || !progress.data) return <AppShell><LoadingBlock/></AppShell>;
  const data = progress.data;
  return (
    <AppShell>
      <section className="page-head"><div><div className="eyebrow">IDENTITY / PROGRESS</div><h1>Как растёт ваша репутация</h1><p>Формула открыта. Никакой мистической «кармы», которую система начисляет за настроение сервера.</p></div><Link href="/profile/identity" className="secondary-button">Стиль и достижения <ArrowRight size={14}/></Link></section>
      <section className="identity-progress-hero">
        <div><Gauge size={18}/><span>Репутация</span><strong>{data.reputation}</strong></div>
        <div><Sparkles size={18}/><span>Уровень</span><strong>{data.level}</strong></div>
        <div><Trophy size={18}/><span>До следующего</span><strong>{data.next_level_threshold === null ? "MAX" : data.points_to_next_level}</strong></div>
      </section>
      <section className="identity-level-card">
        <div className="identity-level-copy"><strong>{data.next_level_threshold === null ? "Максимальный текущий уровень" : `Уровень ${data.level} → ${data.level + 1}`}</strong><span>{data.current_level_threshold} / {data.next_level_threshold ?? data.reputation} репутации</span></div>
        <div className="identity-progress-track"><i style={{width:`${data.progress_percent}%`}}/></div>
        <small>{data.progress_percent.toFixed(1)}%</small>
      </section>
      <section className="identity-breakdown">
        <div className="section-heading"><h2>Вклад по источникам</h2><span>Итого {Object.values(data.point_breakdown).reduce((sum,value)=>sum+value,0)} баллов</span></div>
        {rows.map(([key,label,description]) => <article key={key}><div><strong>{label}</strong><span>{description}</span></div><b>+{data.point_breakdown[key]}</b></article>)}
      </section>
      <section className="identity-raw-metrics"><div><span>Публикации</span><strong>{data.metrics.publications}</strong></div><div><span>Ответы</span><strong>{data.metrics.answers}</strong></div><div><span>Принятые</span><strong>{data.metrics.accepted}</strong></div><div><span>Followers</span><strong>{data.metrics.followers}</strong></div><div><span>Сообщества</span><strong>{data.metrics.communities}</strong></div><div><span>Positive score</span><strong>{data.metrics.positive_score}</strong></div></section>
    </AppShell>
  );
}
