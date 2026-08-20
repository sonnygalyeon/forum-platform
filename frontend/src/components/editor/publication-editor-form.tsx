"use client";

import { useQuery } from "@tanstack/react-query";
import { Save, Send } from "lucide-react";
import { FormEvent, useMemo, useState } from "react";
import { BlockEditor, normalizeBlocks, type PendingMedia } from "@/components/editor/block-editor";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { Community, ContentBlock, CursorPage, Publication } from "@/lib/types";

export type PublicationEditorValue = {
  type: "post" | "article" | "topic";
  title: string;
  tags: string;
  communityId: string;
  blocks: ContentBlock[];
};

export function PublicationEditorForm({
  initial,
  mode,
  onSaved,
}: {
  initial?: Partial<PublicationEditorValue> & { id?: string };
  mode: "create" | "edit";
  onSaved: (publication: Publication) => void;
}) {
  const [type, setType] = useState<"post" | "article" | "topic">(initial?.type ?? "topic");
  const [title, setTitle] = useState(initial?.title ?? "");
  const [tags, setTags] = useState(initial?.tags ?? "");
  const [communityId, setCommunityId] = useState(initial?.communityId ?? "");
  const [blocks, setBlocks] = useState<ContentBlock[]>(initial?.blocks?.length ? initial.blocks : [{ type: "paragraph", text: "" }]);
  const [pendingMedia, setPendingMedia] = useState<PendingMedia[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const communities = useQuery({ queryKey: ["communities"], queryFn: () => clientApi<CursorPage<Community>>("/communities/") });
  const normalized = useMemo(() => normalizeBlocks(blocks), [blocks]);

  function tagsArray() {
    return tags.split(",").map(value => value.trim()).filter(Boolean).slice(0, 20);
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!normalized.length) { setError("Добавьте хотя бы один непустой блок."); return; }
    if (type !== "post" && !title.trim()) { setError("Для вопроса и статьи нужен заголовок."); return; }
    setBusy(true); setError("");
    try {
      let publication: Publication;
      if (mode === "create") {
        publication = await clientApi<Publication>("/publications/", {
          method: "POST",
          body: JSON.stringify({ type, title: title.trim(), content: normalized, community_id: communityId || null, tags: tagsArray() }),
        });
      } else {
        const id = initial?.id;
        if (!id) throw new Error("Publication id is missing");
        publication = await clientApi<Publication>(`/publications/${id}/`, {
          method: "PATCH",
          body: JSON.stringify({ title: title.trim(), content: normalized, tags: tagsArray() }),
        });
      }
      onSaved(publication);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="editor-panel publication-editor" onSubmit={submit}>
      {mode === "create" ? <div className="type-selector">{(["topic","post","article"] as const).map(value => <button type="button" key={value} onClick={() => setType(value)} className={type === value ? "active" : ""}>{value === "topic" ? "Вопрос" : value === "post" ? "Пост" : "Статья"}</button>)}</div> : null}
      <label>{type === "post" ? <>Короткий заголовок <span className="optional">необязательно</span></> : "Заголовок"}<input value={title} onChange={e => setTitle(e.target.value)} maxLength={300} required={type !== "post"} placeholder={type === "topic" ? "Сформулируйте вопрос" : type === "article" ? "Название статьи" : "О чём публикация?"}/></label>
      <div><div className="field-label">Содержимое</div><BlockEditor value={blocks} onChange={setBlocks} onMediaUploaded={(media) => setPendingMedia(current => [...current.filter(item => item.asset.id !== media.asset.id), media])}/></div>
      <div className="form-grid"><label>Теги <span className="optional">через запятую</span><input value={tags} onChange={e => setTags(e.target.value)} placeholder="django, python, backend"/></label>{mode === "create" ? <label>Сообщество <span className="optional">необязательно</span><select value={communityId} onChange={e => setCommunityId(e.target.value)}><option value="">Без сообщества</option>{communities.data?.results.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label> : null}</div>
      {error ? <div className="form-error">{error}</div> : null}
      <div className="editor-actions"><span className="editor-status">{normalized.length} блоков · {pendingMedia.length} новых медиа</span><button className="primary-button" disabled={busy}>{mode === "create" ? <Send size={15}/> : <Save size={15}/>} {busy ? "Сохраняем…" : mode === "create" ? "Опубликовать" : "Сохранить изменения"}</button></div>
    </form>
  );
}
