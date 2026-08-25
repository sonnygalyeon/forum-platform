"use client";

import { useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, Bell, BellOff, FileText, ImagePlus, Link2, Paintbrush, Pin, PinOff, ShieldCheck, UsersRound, X } from "lucide-react";
import { ConversationAvatar } from "@/components/messenger/conversation-avatar";
import { UserAvatar } from "@/components/profile/user-avatar";
import { clientApi, errorMessage } from "@/lib/client-api";
import { uploadMediaFile } from "@/lib/media-upload";
import { CHAT_THEMES, WALLPAPERS, formatPresence } from "@/lib/messenger-ui";
import type { MessengerConversation, MessengerSharedContent, User } from "@/lib/types";

type SharedTab = "media" | "files" | "links";

export function ChatInfoPanel({ conversation, me, onClose }: { conversation: MessengerConversation; me: User; onClose: () => void }) {
  const qc = useQueryClient();
  const [uploading, setUploading] = useState<number | null>(null);
  const [avatarUploading, setAvatarUploading] = useState<number | null>(null);
  const [sharedTab, setSharedTab] = useState<SharedTab>("media");
  const [editingGroup, setEditingGroup] = useState(false);
  const [groupTitle, setGroupTitle] = useState(conversation.title);
  const [groupDescription, setGroupDescription] = useState(conversation.description || "");
  const fileRef = useRef<HTMLInputElement | null>(null);
  const avatarRef = useRef<HTMLInputElement | null>(null);
  const appearance = conversation.appearance;
  const other = conversation.kind === "direct" ? conversation.members.find(m => m.user.id !== me.id) : undefined;
  const myMembership = conversation.members.find(m => m.user.id === me.id);
  const isOwner = myMembership?.role === "owner";
  const canManageGroup = conversation.kind === "group" && myMembership?.role !== "member";

  const update = useMutation({
    mutationFn: (payload: Record<string, unknown>) => clientApi<MessengerConversation>(`/messenger/conversations/${conversation.id}/`, { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: data => {
      qc.setQueryData<MessengerConversation[]>(["messenger-conversations"], old => old?.map(item => item.id === data.id ? data : item));
      qc.invalidateQueries({ queryKey: ["messenger-conversations"] });
    },
  });

  const roleUpdate = useMutation({
    mutationFn: ({ userId, role }: { userId:string; role:"admin"|"member" }) => clientApi<MessengerConversation>(`/messenger/conversations/${conversation.id}/members/${userId}/role/`, { method:"PATCH", body:JSON.stringify({role}) }),
    onSuccess: data => {
      qc.setQueryData<MessengerConversation[]>(["messenger-conversations"], old => old?.map(item => item.id === data.id ? data : item));
      qc.invalidateQueries({queryKey:["messenger-conversations"]});
    },
  });

  const shared = useQuery({
    queryKey: ["messenger-shared", conversation.id, sharedTab],
    queryFn: () => clientApi<MessengerSharedContent>(`/messenger/conversations/${conversation.id}/shared/?type=${sharedTab}`),
  });

  const uploadWallpaper = async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    setUploading(0);
    try {
      const asset = await uploadMediaFile(file, progress => setUploading(progress.percent));
      await update.mutateAsync({ wallpaper_asset_id: asset.id });
    } finally { setUploading(null); }
  };

  const uploadAvatar = async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    setAvatarUploading(0);
    try {
      const asset = await uploadMediaFile(file, progress => setAvatarUploading(progress.percent));
      await update.mutateAsync({ avatar_asset_id: asset.id });
    } finally { setAvatarUploading(null); }
  };

  return <aside className="messenger-info-panel">
    <header className="messenger-info-head"><div><span className="eyebrow">CHAT / DETAILS</span><strong>Информация</strong></div><button className="icon-button messenger-flat-button" onClick={onClose}><X size={17}/></button></header>
    <div className="messenger-info-scroll">
      <section className="messenger-profile-summary">
        <button className={`messenger-avatar-edit ${canManageGroup ? "editable" : ""}`} onClick={() => canManageGroup && avatarRef.current?.click()}>
          <ConversationAvatar conversation={conversation} me={me} size="lg"/>
          {canManageGroup ? <span>{avatarUploading === null ? <ImagePlus size={13}/> : `${avatarUploading}%`}</span> : null}
        </button>
        <input ref={avatarRef} hidden type="file" accept="image/*" onChange={e=>{const f=e.target.files?.[0]; if(f) void uploadAvatar(f); e.currentTarget.value="";}}/>
        <h3>{conversation.display_title}</h3>
        <p>{conversation.kind === "direct" ? formatPresence(other) : `${conversation.members.length} участников · ${conversation.members.filter(m => m.online).length} в сети`}</p>
        {conversation.description ? <small className="messenger-group-description">{conversation.description}</small> : null}
        {canManageGroup ? <button className="messenger-inline-link" onClick={()=>setEditingGroup(v=>!v)}>Изменить группу</button> : null}
      </section>

      {editingGroup && canManageGroup ? <section className="messenger-group-editor">
        <input value={groupTitle} onChange={e=>setGroupTitle(e.target.value)} maxLength={120} placeholder="Название группы"/>
        <textarea value={groupDescription} onChange={e=>setGroupDescription(e.target.value)} maxLength={500} placeholder="Описание группы" rows={3}/>
        <button className="primary-button" disabled={groupTitle.trim().length<2||update.isPending} onClick={()=>update.mutate({title:groupTitle,description:groupDescription})}>Сохранить</button>
      </section> : null}

      <section className="messenger-info-actions">
        <button onClick={() => update.mutate({ is_muted: !conversation.is_muted })}>{conversation.is_muted ? <Bell size={16}/> : <BellOff size={16}/>}<span>{conversation.is_muted ? "Включить уведомления" : "Без звука"}</span></button>
        <button onClick={() => update.mutate({ is_pinned: !conversation.is_pinned })}>{conversation.is_pinned ? <PinOff size={16}/> : <Pin size={16}/>}<span>{conversation.is_pinned ? "Открепить чат" : "Закрепить чат"}</span></button>
        <button onClick={() => update.mutate({ is_archived: !conversation.is_archived })}><Archive size={16}/><span>{conversation.is_archived ? "Вернуть из архива" : "В архив"}</span></button>
      </section>

      <section className="messenger-settings-section">
        <div className="messenger-settings-title"><Paintbrush size={15}/><div><strong>Оформление чата</strong><span>Настройки видны только вам</span></div></div>
        <label className="messenger-setting-label">Акцент</label>
        <div className="chat-theme-grid">{CHAT_THEMES.map(theme => <button key={theme.id} type="button" className={appearance?.chat_theme === theme.id ? "active" : ""} title={theme.label} onClick={() => update.mutate({ chat_theme: theme.id })}><span style={{ background: theme.color }}/><small>{theme.label}</small></button>)}</div>
        <label className="messenger-setting-label">Фон</label>
        <div className="wallpaper-grid">
          {WALLPAPERS.map(wallpaper => <button key={wallpaper.id} type="button" className={`wallpaper-preview wallpaper-${wallpaper.id} ${appearance?.wallpaper === wallpaper.id ? "active" : ""}`} onClick={() => update.mutate({ wallpaper: wallpaper.id })}><span>{wallpaper.label}</span></button>)}
          <button className={`wallpaper-preview wallpaper-custom ${appearance?.wallpaper === "custom" ? "active" : ""}`} onClick={() => fileRef.current?.click()}><ImagePlus size={17}/><span>{uploading === null ? "Своя картинка" : `${uploading}%`}</span></button>
          <input ref={fileRef} hidden type="file" accept="image/*" onChange={event=>{const file=event.target.files?.[0];if(file)void uploadWallpaper(file);event.currentTarget.value="";}}/>
        </div>
        <div className="messenger-range-row"><label htmlFor="wallpaper-dim">Затемнение</label><span>{appearance?.wallpaper_dim ?? 10}%</span></div>
        <input id="wallpaper-dim" className="messenger-range" type="range" min="0" max="70" value={appearance?.wallpaper_dim ?? 10} onChange={e=>update.mutate({wallpaper_dim:Number(e.target.value)})}/>
        <label className="messenger-toggle-row"><span><strong>Размытие фона</strong><small>Полезно для фотографий</small></span><input type="checkbox" checked={appearance?.wallpaper_blur ?? false} onChange={e=>update.mutate({wallpaper_blur:e.target.checked})}/></label>
        <label className="messenger-setting-label">Размер сообщений</label>
        <div className="messenger-segmented">{(["small","normal","large"] as const).map(scale=><button key={scale} className={appearance?.message_scale===scale?"active":""} onClick={()=>update.mutate({message_scale:scale})}>{scale==="small"?"Мелко":scale==="normal"?"Обычно":"Крупно"}</button>)}</div>
      </section>

      <section className="messenger-settings-section">
        <div className="messenger-settings-title"><FileText size={15}/><div><strong>Общие материалы</strong><span>Последние 100 элементов</span></div></div>
        <div className="messenger-shared-tabs"><button className={sharedTab==="media"?"active":""} onClick={()=>setSharedTab("media")}>Медиа</button><button className={sharedTab==="files"?"active":""} onClick={()=>setSharedTab("files")}>Файлы</button><button className={sharedTab==="links"?"active":""} onClick={()=>setSharedTab("links")}>Ссылки</button></div>
        <div className={`messenger-shared-grid ${sharedTab}`}>
          {shared.data?.results.length ? shared.data.results.map((item,index)=> sharedTab==="links" ? <a key={`${item.message_id}-${index}`} href={item.url} target="_blank" rel="noreferrer"><Link2 size={13}/><span>{item.url}</span></a> : item.asset ? (item.asset.kind==="image"&&item.asset.url ? <a className="shared-image" key={`${item.message_id}-${index}`} href={item.asset.url} target="_blank" rel="noreferrer"><img src={item.asset.url} alt={item.asset.name||"media"}/></a> : <a key={`${item.message_id}-${index}`} href={item.asset.url||"#"} target="_blank" rel="noreferrer"><FileText size={14}/><span>{item.asset.name||"Файл"}</span></a>) : null) : <small className="messenger-shared-empty">Пока ничего нет</small>}
        </div>
      </section>

      <section className="messenger-settings-section">
        <div className="messenger-settings-title"><UsersRound size={15}/><div><strong>{conversation.kind === "group" ? "Участники" : "Собеседник"}</strong><span>{conversation.members.length} в этом чате</span></div></div>
        <div className="messenger-member-list">{conversation.members.filter(member => member.user.id !== me.id || conversation.kind === "group").map(member => <div key={member.user.id} className="messenger-member-row"><span className="messenger-member-avatar-wrap"><UserAvatar user={member.user} size="sm"/><i className={member.online?"online":""}/></span><span><strong>@{member.user.nickname}</strong><small>{member.online?"в сети":formatPresence(member)}</small></span>{member.role!=="member"?<b>{member.role}</b>:null}{isOwner && member.user.id!==me.id && member.role!=="owner" ? <button className="messenger-role-button" title={member.role==="admin"?"Снять администратора":"Назначить администратором"} onClick={()=>roleUpdate.mutate({userId:member.user.id,role:member.role==="admin"?"member":"admin"})}><ShieldCheck size={12}/></button>:null}</div>)}</div>
      </section>
      {update.error || roleUpdate.error ? <div className="composer-error">{errorMessage(update.error || roleUpdate.error)}</div> : null}
    </div>
  </aside>;
}
