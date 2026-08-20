"use client";

import { Code2, MessageSquareQuote, Send, Type, X } from "lucide-react";
import { useState } from "react";
import type { CommentBlock } from "@/lib/types";

export function CommentComposer({
  label,
  placeholder,
  busy,
  compact = false,
  onSubmit,
}: {
  label?: string;
  placeholder: string;
  busy?: boolean;
  compact?: boolean;
  onSubmit: (blocks: CommentBlock[]) => Promise<void> | void;
}) {
  const [blocks, setBlocks] = useState<CommentBlock[]>([{ type: "paragraph", text: "" }]);

  const valid = blocks.some((block) => block.type === "code" ? block.code.trim() : block.text.trim());
  async function submit() {
    if (!valid || busy) return;
    const normalized = blocks.filter((block) => block.type === "code" ? block.code.trim() : block.text.trim());
    await onSubmit(normalized);
    setBlocks([{ type: "paragraph", text: "" }]);
  }

  return (
    <div className={`comment-composer ${compact ? "comment-composer-compact" : ""}`}>
      {label ? <strong className="composer-label">{label}</strong> : null}
      {blocks.map((block, index) => (
        <div className="comment-composer-block" key={`${block.type}-${index}`}>
          {block.type === "code" ? (
            <div className="comment-code-input"><input value={block.language ?? ""} onChange={(e)=>setBlocks(current=>current.map((item,i)=>i===index?{...block,language:e.target.value}:item))} placeholder="Язык"/><textarea rows={compact?4:6} spellCheck={false} value={block.code} onChange={(e)=>setBlocks(current=>current.map((item,i)=>i===index?{...block,code:e.target.value}:item))} placeholder="Код…"/></div>
          ) : (
            <textarea rows={compact?2:4} value={block.text} onChange={(e)=>setBlocks(current=>current.map((item,i)=>i===index?{...block,text:e.target.value}:item))} placeholder={index===0?placeholder:block.type==="quote"?"Цитата…":"Продолжение…"}/>
          )}
          {blocks.length > 1 ? <button type="button" className="composer-remove" onClick={()=>setBlocks(current=>current.filter((_,i)=>i!==index))}><X size={14}/></button> : null}
        </div>
      ))}
      <div className="composer-actions">
        <div><button type="button" onClick={()=>setBlocks(current=>[...current,{type:"paragraph",text:""}])}><Type size={14}/> Текст</button><button type="button" onClick={()=>setBlocks(current=>[...current,{type:"quote",text:""}])}><MessageSquareQuote size={14}/> Цитата</button><button type="button" onClick={()=>setBlocks(current=>[...current,{type:"code",code:"",language:""}])}><Code2 size={14}/> Код</button></div>
        <button type="button" className="primary-button compact-button" disabled={!valid||busy} onClick={submit}><Send size={14}/>{busy?"Отправляем…":"Отправить"}</button>
      </div>
    </div>
  );
}
