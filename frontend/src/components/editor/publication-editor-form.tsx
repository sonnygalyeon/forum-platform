"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Eye, RotateCcw, Save, Send, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { BlockEditor, normalizeBlocks, type PendingMedia } from "@/components/editor/block-editor";
import { ContentBlocks } from "@/components/content/content-blocks";
import { clientApi, errorMessage } from "@/lib/client-api";
import type {
  Community,
  ContentBlock,
  CursorPage,
  Publication,
  PublicationDraft,
  PublicationMedia,
} from "@/lib/types";

export type PublicationEditorValue = {
  type: "post" | "article" | "topic";
  title: string;
  tags: string;
  communityId: string;
  blocks: ContentBlock[];
};

type AutosaveState = "idle" | "saving" | "saved" | "error";

export function PublicationEditorForm({
  initial,
  initialMedia = [],
  mode,
  onSaved,
}: {
  initial?: Partial<PublicationEditorValue> & { id?: string };
  initialMedia?: PublicationMedia[];
  mode: "create" | "edit";
  onSaved: (publication: Publication) => void;
}) {
  const queryClient = useQueryClient();
  const [type, setType] = useState<"post" | "article" | "topic">(initial?.type ?? "topic");
  const [title, setTitle] = useState(initial?.title ?? "");
  const [tags, setTags] = useState(initial?.tags ?? "");
  const [communityId, setCommunityId] = useState(initial?.communityId ?? "");
  const [blocks, setBlocks] = useState<ContentBlock[]>(initial?.blocks?.length ? initial.blocks : [{ type: "paragraph", text: "" }]);
  const [pendingMedia, setPendingMedia] = useState<PendingMedia[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [autosave, setAutosave] = useState<AutosaveState>("idle");
  const [savedAt, setSavedAt] = useState<string | null>(null);
  const [recoveryDismissed, setRecoveryDismissed] = useState(false);
  const draftIdRef = useRef<string | null>(null);
  const savingRef = useRef(false);

  const communities = useQuery({
    queryKey: ["communities"],
    queryFn: () => clientApi<CursorPage<Community>>("/communities/"),
  });
  const drafts = useQuery({
    queryKey: ["publication-drafts"],
    queryFn: () => clientApi<CursorPage<PublicationDraft>>("/publication-drafts/"),
  });
  const normalized = useMemo(() => normalizeBlocks(blocks), [blocks]);

  const recoverableDraft = useMemo(() => {
    if (recoveryDismissed) return null;
    return drafts.data?.results.find((draft) => {
      if (mode === "create") return draft.source_publication === null;
      return draft.source_publication?.id === initial?.id;
    }) ?? null;
  }, [drafts.data, initial?.id, mode, recoveryDismissed]);

  const previewMedia = useMemo<PublicationMedia[]>(() => {
    const uploaded = pendingMedia.map(({ asset, role, sort_order }) => ({
      asset_id: asset.id,
      role,
      sort_order,
      name: asset.name ?? asset.original_name ?? "Медиа",
      kind: asset.kind,
      content_type: asset.content_type ?? asset.declared_content_type ?? "application/octet-stream",
      size_bytes: asset.size_bytes,
      status: asset.status,
      url: asset.url,
    }));
    const byId = new Map<string, PublicationMedia>();
    for (const item of initialMedia) byId.set(item.asset_id, item);
    for (const item of uploaded) byId.set(item.asset_id, item);
    return [...byId.values()];
  }, [initialMedia, pendingMedia]);

  function tagsArray() {
    return tags.split(",").map((value) => value.trim()).filter(Boolean).slice(0, 20);
  }

  function markChanged() {
    setDirty(true);
    if (autosave !== "saving") setAutosave("idle");
  }

  function draftPayload() {
    return {
      type,
      title,
      content: blocks,
      tags: tagsArray(),
      community_id: communityId || null,
      source_publication_id: mode === "edit" ? initial?.id ?? null : null,
    };
  }

  async function saveDraftNow() {
    if (savingRef.current) return draftIdRef.current;
    savingRef.current = true;
    setAutosave("saving");
    try {
      const existingId = draftIdRef.current;
      const saved = await clientApi<PublicationDraft>(
        existingId ? `/publication-drafts/${existingId}/` : "/publication-drafts/",
        {
          method: existingId ? "PATCH" : "POST",
          body: JSON.stringify(draftPayload()),
        },
      );
      draftIdRef.current = saved.id;
      setDirty(false);
      setAutosave("saved");
      setSavedAt(saved.updated_at);
      void queryClient.invalidateQueries({ queryKey: ["publication-drafts"] });
      return saved.id;
    } catch (err) {
      setAutosave("error");
      throw err;
    } finally {
      savingRef.current = false;
    }
  }

  useEffect(() => {
    if (!dirty || busy || savingRef.current) return;
    const timer = window.setTimeout(() => {
      void saveDraftNow().catch(() => undefined);
    }, 1100);
    return () => window.clearTimeout(timer);
  }, [blocks, busy, communityId, dirty, tags, title, type]);

  function restoreDraft(draft: PublicationDraft) {
    setType(draft.type);
    setTitle(draft.title);
    setTags(draft.tags.join(", "));
    setCommunityId(draft.community?.id ?? "");
    setBlocks(draft.content.length ? draft.content : [{ type: "paragraph", text: "" }]);
    draftIdRef.current = draft.id;
    setDirty(false);
    setAutosave("saved");
    setSavedAt(draft.updated_at);
    setRecoveryDismissed(true);
  }

  async function discardDraft(draft: PublicationDraft) {
    await clientApi(`/publication-drafts/${draft.id}/`, { method: "DELETE" });
    if (draftIdRef.current === draft.id) draftIdRef.current = null;
    setRecoveryDismissed(true);
    await queryClient.invalidateQueries({ queryKey: ["publication-drafts"] });
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!normalized.length) { setError("Добавьте хотя бы один непустой блок."); return; }
    if (type !== "post" && !title.trim()) { setError("Для вопроса и статьи нужен заголовок."); return; }
    setBusy(true);
    setError("");
    try {
      const draftId = await saveDraftNow();
      if (!draftId) throw new Error("Не удалось сохранить черновик перед публикацией.");
      const publication = await clientApi<Publication>(`/publication-drafts/${draftId}/publish/`, { method: "POST" });
      draftIdRef.current = null;
      setDirty(false);
      await queryClient.invalidateQueries({ queryKey: ["publication-drafts"] });
      onSaved(publication);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  const statusText = autosave === "saving"
    ? "Сохраняем черновик…"
    : autosave === "error"
      ? "Автосохранение не удалось"
      : autosave === "saved" && savedAt
        ? `Черновик сохранён ${new Date(savedAt).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}`
        : dirty
          ? "Есть несохранённые изменения"
          : "Черновик синхронизирован";

  return (
    <form className="editor-panel publication-editor" onSubmit={submit}>
      {recoverableDraft ? (
        <div className="draft-recovery">
          <div>
            <strong>Найден сохранённый черновик</strong>
            <span>Обновлён {new Date(recoverableDraft.updated_at).toLocaleString("ru-RU")}. Можно восстановить его или удалить.</span>
          </div>
          <div>
            <button type="button" className="secondary-button" onClick={() => restoreDraft(recoverableDraft)}><RotateCcw size={14}/> Восстановить</button>
            <button type="button" className="ghost-danger" onClick={() => void discardDraft(recoverableDraft)}><Trash2 size={14}/> Удалить</button>
          </div>
        </div>
      ) : null}

      <div className="editor-topline">
        <span className={`autosave-state autosave-${autosave}`}>{statusText}</span>
        <button type="button" className="secondary-button" onClick={() => setPreview((value) => !value)}><Eye size={15}/> {preview ? "Вернуться к редактору" : "Предпросмотр"}</button>
      </div>

      {preview ? (
        <div className="publication-preview">
          <div className="eyebrow">ПРЕДПРОСМОТР / НЕ ОПУБЛИКОВАНО</div>
          {title.trim() ? <h1>{title}</h1> : null}
          <ContentBlocks blocks={normalized} media={previewMedia}/>
          {tagsArray().length ? <div className="preview-tags">{tagsArray().map((tag) => <span key={tag}>#{tag}</span>)}</div> : null}
        </div>
      ) : (
        <>
          {mode === "create" ? <div className="type-selector">{(["topic","post","article"] as const).map((value) => <button type="button" key={value} onClick={() => { setType(value); markChanged(); }} className={type === value ? "active" : ""}>{value === "topic" ? "Вопрос" : value === "post" ? "Пост" : "Статья"}</button>)}</div> : null}
          <label>{type === "post" ? <>Короткий заголовок <span className="optional">необязательно</span></> : "Заголовок"}<input value={title} onChange={(e) => { setTitle(e.target.value); markChanged(); }} maxLength={300} required={type !== "post"} placeholder={type === "topic" ? "Сформулируйте вопрос" : type === "article" ? "Название статьи" : "О чём публикация?"}/></label>
          <div><div className="field-label">Содержимое</div><BlockEditor value={blocks} onChange={(next) => { setBlocks(next); markChanged(); }} onMediaUploaded={(media) => { setPendingMedia((current) => [...current.filter((item) => item.asset.id !== media.asset.id), media]); markChanged(); }}/></div>
          <div className="form-grid"><label>Теги <span className="optional">через запятую</span><input value={tags} onChange={(e) => { setTags(e.target.value); markChanged(); }} placeholder="django, python, backend"/></label>{mode === "create" ? <label>Сообщество <span className="optional">необязательно</span><select value={communityId} onChange={(e) => { setCommunityId(e.target.value); markChanged(); }}><option value="">Без сообщества</option>{communities.data?.results.map((community) => <option key={community.id} value={community.id}>{community.name}</option>)}</select></label> : null}</div>
        </>
      )}

      {error ? <div className="form-error">{error}</div> : null}
      <div className="editor-actions">
        <span className="editor-status">{normalized.length} блоков · {pendingMedia.length} новых медиа</span>
        <button className="primary-button" disabled={busy}>{mode === "create" ? <Send size={15}/> : <Save size={15}/>} {busy ? "Сохраняем…" : mode === "create" ? "Опубликовать" : "Сохранить новую ревизию"}</button>
      </div>
    </form>
  );
}
