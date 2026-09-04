"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { PublicationEditorForm } from "@/components/editor/publication-editor-form";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { Publication } from "@/lib/types";

export default function EditPublicationPage() {
  const params = useParams<{id:string}>();
  const router = useRouter();
  const query = useQuery({ queryKey:["publication",params.id], queryFn:()=>clientApi<Publication>(`/publications/${params.id}/`) });
  if (query.isLoading) return <AppShell><LoadingBlock/></AppShell>;
  if (!query.data || !query.data.can_edit) return <AppShell><div className="error-panel">Редактирование этой публикации недоступно.</div></AppShell>;
  const publication = query.data;
  return (
    <AppShell>
      <section className="page-head"><div><div className="eyebrow">РЕДАКТИРОВАНИЕ / REVISION {publication.revision}</div><h1>{publication.title || "Редактирование поста"}</h1><p>Изменения автоматически уходят в серверный черновик. При публикации создаётся новая неизменяемая ревизия.</p></div></section>
      <PublicationEditorForm
        mode="edit"
        initial={{id:publication.id,type:publication.type,title:publication.title,tags:publication.tags.map((tag)=>tag.name).join(", "),communityId:publication.community?.id??"",blocks:publication.content??[]}}
        initialMedia={publication.media ?? []}
        onSaved={(saved)=>router.push(`/publications/${saved.id}`)}
      />
    </AppShell>
  );
}
