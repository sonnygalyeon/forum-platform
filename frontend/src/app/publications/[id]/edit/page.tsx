"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { PublicationEditorForm } from "@/components/editor/publication-editor-form";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { Publication } from "@/lib/types";

export default function EditPublicationPage() {
  const params = useParams<{id:string}>(); const router = useRouter();
  const query = useQuery({ queryKey:["publication",params.id], queryFn:()=>clientApi<Publication>(`/publications/${params.id}/`) });
  if (query.isLoading) return <AppShell><LoadingBlock/></AppShell>;
  if (!query.data || !query.data.can_edit) return <AppShell><div className="error-panel">Редактирование этой публикации недоступно.</div></AppShell>;
  const p = query.data;
  return <AppShell><section className="page-head"><div><div className="eyebrow">РЕДАКТИРОВАНИЕ / REVISION {p.revision}</div><h1>{p.title || "Редактирование поста"}</h1><p>После сохранения backend создаст новую неизменяемую ревизию.</p></div></section><PublicationEditorForm mode="edit" initial={{id:p.id,type:p.type,title:p.title,tags:p.tags.map(t=>t.name).join(", "),communityId:p.community?.id??"",blocks:p.content??[]}} onSaved={(publication)=>router.push(`/publications/${publication.id}`)}/></AppShell>;
}
