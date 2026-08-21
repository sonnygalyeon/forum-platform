"use client";

import { FileText, Pencil, Reply, SmilePlus, Trash2 } from "lucide-react";
import type { MessengerMessage, User } from "@/lib/types";
import { UserAvatar } from "@/components/profile/user-avatar";

const QUICK_REACTIONS=["👍","❤️","🔥"];

export function MessageBubble({ message, me, grouped, onReply, onEdit, onDelete, onReact }: { message:MessengerMessage; me:User; grouped:boolean; onReply:(m:MessengerMessage)=>void; onEdit:(m:MessengerMessage)=>void; onDelete:(m:MessengerMessage)=>void; onReact:(m:MessengerMessage,emoji:string)=>void }) {
  const own=message.sender.id===me.id;
  return <article className={`message-line ${own?"message-own":""} ${grouped?"message-grouped":""}`}>
    {!own&&!grouped?<UserAvatar user={message.sender} size="xs"/>:<span className="message-avatar-spacer"/>}
    <div className="message-bubble-wrap">{!own&&!grouped?<span className="message-sender">@{message.sender.nickname}</span>:null}<div className={`message-bubble ${message.deleted?"message-deleted":""}`}>
      {message.reply_to?<button className="message-reply-preview" onClick={()=>{}}><strong>@{message.reply_to.sender_nickname}</strong><span>{message.reply_to.deleted?"Сообщение удалено":message.reply_to.text}</span></button>:null}
      {message.deleted?<p className="deleted-copy">Сообщение удалено</p>:<>{message.attachments.length?<div className="message-attachments">{message.attachments.map(asset=>asset.kind==="image"&&asset.url?<a key={asset.id} href={asset.url} target="_blank"><img src={asset.url} alt={asset.original_name||asset.name||"Изображение"}/></a>:asset.kind==="video"&&asset.url?<video key={asset.id} src={asset.url} controls/>:<a className="message-file" key={asset.id} href={asset.url||"#"} target="_blank"><FileText size={18}/><span>{asset.original_name||asset.name||"Файл"}</span></a>)}</div>:null}{message.text?<p>{message.text}</p>:null}</>}
      <span className="message-time">{new Date(message.created_at).toLocaleTimeString("ru-RU",{hour:"2-digit",minute:"2-digit"})}{message.edited_at?" · изм.":""}{own?<span className="message-read-mark">{message.read_by_count>0?" ✓✓":" ✓"}</span>:null}</span>
    </div>
    {!message.deleted?<div className="message-reactions">{message.reactions.map(r=><button key={r.emoji} className={r.reacted_by_me?"active":""} onClick={()=>onReact(message,r.emoji)}>{r.emoji}<span>{r.count}</span></button>)}</div>:null}
    {!message.deleted?<div className="message-actions"><button title="Ответить" onClick={()=>onReply(message)}><Reply size={13}/></button>{QUICK_REACTIONS.map(emoji=><button key={emoji} onClick={()=>onReact(message,emoji)}>{emoji}</button>)}{own?<><button title="Изменить" onClick={()=>onEdit(message)}><Pencil size={12}/></button><button title="Удалить" onClick={()=>onDelete(message)}><Trash2 size={12}/></button></>:null}</div>:null}</div>
  </article>
}
