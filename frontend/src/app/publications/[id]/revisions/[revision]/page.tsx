"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { History } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { ContentBlocks } from "@/components/content/content-blocks";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { PublicationMedia, PublicationRevision } from "@/lib/types";

export default function RevisionDetailPage() {
  const { id, revision } = useParams<{id:string;revision:string}>();
  const query = useQuery({
    queryKey:["revision",id,revision],
    queryFn:()=>clientApi<PublicationRevision>(`/publications/${id}/revisions/${revision}/`),
  });
  if (query.isLoading) return <AppShell><LoadingBlock/></AppShell>;
  if (!query.data) return <AppShell><div className="error-panel">Ревизия не найдена.</div></AppShell>;
  const item = query.data;
  const media: PublicationMedia[] = (item.media_snapshot ?? []).map((asset) => ({
    asset_id: asset.asset_id,
    role: asset.role,
    sort_order: asset.sort_order,
    name: asset.name,
    kind: asset.kind,
    content_type: "",
    size_bytes: asset.size_bytes,
    status: "snapshot",
    url: null,
  }));
  return (
    <AppShell>
      <section className="page-head revision-detail-head"><div><div className="eyebrow"><History size={13}/> IMMUTABLE REVISION {item.revision}</div><h1>{item.title || "Без заголовка"}</h1><p>Сохранено @{item.edited_by.nickname} · {new Date(item.created_at).toLocaleString("ru-RU")}</p></div></section>
      <article className="revision-detail-card">
        <ContentBlocks blocks={item.content ?? []} media={media}/>
        {item.tags_snapshot?.length ? <div className="preview-tags">{item.tags_snapshot.map((tag) => <span key={tag.slug}>#{tag.name}</span>)}</div> : null}
      </article>
      <div className="revision-actions"><Link href={`/publications/${id}/revisions`} className="secondary-button">К истории</Link><Link href={`/publications/${id}`} className="secondary-button">Текущая версия</Link></div>
    </AppShell>
  );
}
