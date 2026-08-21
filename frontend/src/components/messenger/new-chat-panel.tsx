"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, Search, UsersRound, X } from "lucide-react";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { MessengerConversation, User } from "@/lib/types";
import { UserAvatar } from "@/components/profile/user-avatar";

export function NewChatPanel({ onClose, onCreated }: { onClose:()=>void; onCreated:(conversation:MessengerConversation)=>void }) {
  const [q,setQ]=useState(""); const [group,setGroup]=useState(false); const [title,setTitle]=useState(""); const [selected,setSelected]=useState<string[]>([]);
  const users=useQuery({queryKey:["messenger-users",q],queryFn:()=>clientApi<User[]>(`/messenger/users/?q=${encodeURIComponent(q)}`)});
  const direct=useMutation({mutationFn:(id:string)=>clientApi<MessengerConversation>("/messenger/conversations/direct/",{method:"POST",body:JSON.stringify({user_id:id})}),onSuccess:onCreated});
  const createGroup=useMutation({mutationFn:()=>clientApi<MessengerConversation>("/messenger/conversations/groups/",{method:"POST",body:JSON.stringify({title,member_ids:selected})}),onSuccess:onCreated});
  const error=direct.error||createGroup.error;
  return <div className="new-chat-panel"><div className="messenger-panel-head"><div><strong>{group?"Новая группа":"Новый чат"}</strong><span>{group?"Выберите участников":"Найдите пользователя Night Iris"}</span></div><button className="icon-button" onClick={onClose}><X size={16}/></button></div>
    <div className="messenger-mode-tabs"><button className={!group?"active":""} onClick={()=>setGroup(false)}>Личный чат</button><button className={group?"active":""} onClick={()=>setGroup(true)}><UsersRound size={13}/>Группа</button></div>
    {group?<input className="messenger-group-title" value={title} onChange={e=>setTitle(e.target.value)} placeholder="Название группы" maxLength={120}/>:null}
    <label className="messenger-search-input"><Search size={14}/><input value={q} onChange={e=>setQ(e.target.value)} placeholder="Никнейм или имя…"/></label>
    <div className="messenger-user-picker">{users.data?.map(user=>{const active=selected.includes(user.id);return <button key={user.id} onClick={()=>group?setSelected(v=>active?v.filter(id=>id!==user.id):[...v,user.id]):direct.mutate(user.id)}><UserAvatar user={user} size="sm"/><span><strong>@{user.nickname}</strong><small>{[user.first_name,user.last_name].filter(Boolean).join(" ")||"Night Iris member"}</small></span>{group?<span className={`member-check ${active?"selected":""}`}>{active?<Check size={12}/>:null}</span>:null}</button>})}</div>
    {error?<div className="form-error">{errorMessage(error)}</div>:null}
    {group?<button className="primary-button messenger-create-group" disabled={selected.length<1||title.trim().length<2||createGroup.isPending} onClick={()=>createGroup.mutate()}><UsersRound size={15}/>{createGroup.isPending?"Создаём…":`Создать группу · ${selected.length+1}`}</button>:null}
  </div>
}
