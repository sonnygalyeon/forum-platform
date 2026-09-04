"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronRight, History } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, PublicationRevision } from "@/lib/types";

export default function RevisionsPage() {
  const { id } = useParams<{id:string}>();
  const query = useQuery({
    queryKey:["revisions",id],
    queryFn:()=>clientApi<CursorPage<PublicationRevision>>(`/publications/${id}/revisions/`),
  });
  return (
    <AppShell>
      <section className="page-head"><div><div className="eyebrow">ИСТОРИЯ / IMMUTABLE</div><h1>Ревизии публикации</h1><p>Каждое изменение хранится отдельно. Старые версии можно открыть и проверить, а не верить надписи «edited» на слово.</p></div></section>
      {query.isLoading ? <LoadingBlock/> : query.data?.results.length ? (
        <div className="revision-list">
          {query.data.results.map((revision) => (
            <Link className="revision-row" href={`/publications/${id}/revisions/${revision.revision}`} key={revision.revision}>
              <span className="revision-number"><History size={15}/> Revision {revision.revision}</span>
              <span className="revision-title">{revision.title || "Без заголовка"}</span>
              <small>@{revision.edited_by.nickname} · {new Date(revision.created_at).toLocaleString("ru-RU")}</small>
              <ChevronRight size={16}/>
            </Link>
          ))}
        </div>
      ) : <div className="inline-empty">История пока пуста.</div>}
      <Link href={`/publications/${id}`} className="secondary-button">Назад к публикации</Link>
    </AppShell>
  );
}
