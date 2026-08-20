"use client";

import {
  ArrowDown,
  ArrowUp,
  Code2,
  FileUp,
  Heading2,
  ImagePlus,
  LoaderCircle,
  MessageSquareQuote,
  Plus,
  Trash2,
  Type,
  Video,
} from "lucide-react";
import { ChangeEvent, useRef, useState } from "react";
import { uploadMediaFile } from "@/lib/media-upload";
import type { ContentBlock, MediaAsset } from "@/lib/types";

export type PendingMedia = {
  asset: MediaAsset;
  role: "inline" | "attachment";
  sort_order: number;
};

function newParagraph(): ContentBlock {
  return { type: "paragraph", text: "" };
}

export function BlockEditor({
  value,
  onChange,
  onMediaUploaded,
}: {
  value: ContentBlock[];
  onChange: (blocks: ContentBlock[]) => void;
  onMediaUploaded?: (media: PendingMedia) => void;
}) {
  const [uploading, setUploading] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const fileInput = useRef<HTMLInputElement>(null);
  const requestedMediaType = useRef<"image" | "video" | "attachment">("image");

  function patch(index: number, block: ContentBlock) {
    onChange(value.map((current, i) => (i === index ? block : current)));
  }

  function remove(index: number) {
    const next = value.filter((_, i) => i !== index);
    onChange(next.length ? next : [newParagraph()]);
  }

  function move(index: number, direction: -1 | 1) {
    const target = index + direction;
    if (target < 0 || target >= value.length) return;
    const next = [...value];
    [next[index], next[target]] = [next[target], next[index]];
    onChange(next);
  }

  function add(block: ContentBlock) {
    onChange([...value, block]);
  }

  function requestUpload(type: "image" | "video" | "attachment") {
    requestedMediaType.current = type;
    fileInput.current?.click();
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    const type = requestedMediaType.current;
    if (type === "image" && !file.type.startsWith("image/")) {
      alert("Для блока изображения выберите графический файл.");
      return;
    }
    if (type === "video" && !file.type.startsWith("video/")) {
      alert("Для видео-блока выберите видеофайл.");
      return;
    }
    setUploading(file.name);
    setProgress(0);
    try {
      const asset = await uploadMediaFile(file, (state) => setProgress(state.percent));
      const block: ContentBlock =
        type === "image"
          ? { type: "image", asset_id: asset.id, caption: "" }
          : type === "video"
            ? { type: "video", asset_id: asset.id, caption: "" }
            : { type: "attachment", asset_id: asset.id, caption: file.name };
      const sortOrder = value.filter((item) => ["image", "video", "attachment"].includes(item.type)).length;
      add(block);
      onMediaUploaded?.({ asset, role: type === "attachment" ? "attachment" : "inline", sort_order: sortOrder });
    } finally {
      setUploading(null);
      setProgress(0);
    }
  }

  return (
    <div className="block-editor">
      <input ref={fileInput} className="sr-only" type="file" onChange={upload} />
      <div className="block-list">
        {value.map((block, index) => (
          <div className="editor-block" key={`${block.type}-${index}`}>
            <div className="block-grip">
              <span>{index + 1}</span>
              <button type="button" onClick={() => move(index, -1)} disabled={index === 0} aria-label="Переместить вверх"><ArrowUp size={13}/></button>
              <button type="button" onClick={() => move(index, 1)} disabled={index === value.length - 1} aria-label="Переместить вниз"><ArrowDown size={13}/></button>
            </div>
            <div className="block-field">
              {block.type === "paragraph" ? (
                <textarea rows={4} value={block.text} onChange={(e) => patch(index, { ...block, text: e.target.value })} placeholder="Текст абзаца…" />
              ) : block.type === "quote" ? (
                <textarea rows={3} value={block.text} onChange={(e) => patch(index, { ...block, text: e.target.value })} placeholder="Цитата…" />
              ) : block.type === "heading" ? (
                <div className="heading-block-row">
                  <select value={block.level} onChange={(e) => patch(index, { ...block, level: Number(e.target.value) as 1|2|3|4 })}>
                    <option value={1}>H1</option><option value={2}>H2</option><option value={3}>H3</option><option value={4}>H4</option>
                  </select>
                  <input value={block.text} onChange={(e) => patch(index, { ...block, text: e.target.value })} placeholder="Заголовок раздела…" />
                </div>
              ) : block.type === "code" ? (
                <div className="code-editor-block">
                  <input value={block.language ?? ""} onChange={(e) => patch(index, { ...block, language: e.target.value })} placeholder="Язык: rust, python, ts…" />
                  <textarea rows={8} spellCheck={false} value={block.code} onChange={(e) => patch(index, { ...block, code: e.target.value })} placeholder="Код…" />
                </div>
              ) : (
                <div className="media-editor-block">
                  <div className="media-editor-icon">{block.type === "image" ? <ImagePlus/> : block.type === "video" ? <Video/> : <FileUp/>}</div>
                  <div><strong>{block.type === "image" ? "Изображение" : block.type === "video" ? "Видео" : "Вложение"}</strong><small>asset: {block.asset_id.slice(0, 8)}…</small></div>
                  <input value={block.caption ?? ""} onChange={(e) => patch(index, { ...block, caption: e.target.value })} placeholder="Подпись…" />
                </div>
              )}
            </div>
            <button className="block-delete" type="button" onClick={() => remove(index)} aria-label="Удалить блок"><Trash2 size={15}/></button>
          </div>
        ))}
      </div>

      {uploading ? (
        <div className="upload-progress"><LoaderCircle className="spin" size={16}/><span>Загружаем {uploading}</span><strong>{progress}%</strong><div><i style={{width:`${progress}%`}}/></div></div>
      ) : null}

      <div className="block-toolbar">
        <button type="button" onClick={() => add({ type: "paragraph", text: "" })}><Type size={15}/> Текст</button>
        <button type="button" onClick={() => add({ type: "heading", level: 2, text: "" })}><Heading2 size={15}/> Заголовок</button>
        <button type="button" onClick={() => add({ type: "quote", text: "" })}><MessageSquareQuote size={15}/> Цитата</button>
        <button type="button" onClick={() => add({ type: "code", code: "", language: "" })}><Code2 size={15}/> Код</button>
        <button type="button" onClick={() => requestUpload("image")}><ImagePlus size={15}/> Фото</button>
        <button type="button" onClick={() => requestUpload("video")}><Video size={15}/> Видео</button>
        <button type="button" onClick={() => requestUpload("attachment")}><FileUp size={15}/> Файл</button>
        <span className="block-toolbar-hint"><Plus size={13}/> блоки сохраняются как JSON, не HTML</span>
      </div>
    </div>
  );
}

export function normalizeBlocks(blocks: ContentBlock[]) {
  return blocks.filter((block) => {
    if (block.type === "paragraph" || block.type === "quote" || block.type === "heading") return block.text.trim().length > 0;
    if (block.type === "code") return block.code.trim().length > 0;
    return Boolean(block.asset_id);
  });
}
