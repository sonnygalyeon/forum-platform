"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { FileEdit, PenSquare, Trash2 } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, PublicationDraft } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

export default function DraftsPage() {
  const { user, loading } = useAuth();
  const queryClient = useQueryClient();
  const drafts = useQuery({
    queryKey: ["publication-drafts"],
    queryFn: () => clientApi<CursorPage<PublicationDraft>>("/publication-drafts/"),
    enabled: Boolean(user),
  });

  async function remove(id: string) {
    await clientApi(`/publication-drafts/${id}/`, { method: "DELETE" });
    await queryClient.invalidateQueries({ queryKey: ["publication-drafts"] });
  }

  if (loading) return <AppShell><LoadingBlock/></AppShell>;
  if (!user) return <AppShell><EmptyState icon={FileEdit} title="Нужен аккаунт" text="Черновики синхронизируются с аккаунтом, а не прячутся в одном браузере." action={{href:"/login",label:"Войти"}}/></AppShell>;

  return (
    <AppShell>
      <section className="page-head"><div><div className="eyebrow">ЧЕРНОВИКИ / SERVER-SIDE</div><h1>Незавершённые публикации</h1><p>Автосохранённые материалы доступны после повторного входа и на другом устройстве.</p></div><Link className="primary-button" href="/new"><PenSquare size={15}/> Новая публикация</Link></section>
      {drafts.isLoading ? <LoadingBlock/> : drafts.data?.results.length ? (
        <div className="draft-list">
          {drafts.data.results.map((draft) => {
            const href = draft.source_publication ? `/publications/${draft.source_publication.id}/edit` : "/new";
            return (
              <article className="draft-card" key={draft.id}>
                <div><span className="draft-kind">{draft.source_publication ? "РЕДАКТИРОВАНИЕ" : draft.type.toUpperCase()}</span><h2>{draft.title || "Без заголовка"}</h2><p>{draft.content.length} блоков · {draft.tags.length} тегов · обновлён {new Date(draft.updated_at).toLocaleString("ru-RU")}</p></div>
                <div className="draft-actions"><Link className="secondary-button" href={href}>Продолжить</Link><button className="ghost-danger" type="button" onClick={() => void remove(draft.id)}><Trash2 size={14}/> Удалить</button></div>
              </article>
            );
          })}
        </div>
      ) : <EmptyState icon={FileEdit} title="Черновиков нет" text="Начните новую публикацию. После первого изменения редактор сохранит её автоматически." action={{href:"/new",label:"Создать"}}/>}
    </AppShell>
  );
}
