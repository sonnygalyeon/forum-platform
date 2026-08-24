"use client";

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Archive, Bell, BellOff, ImagePlus, Paintbrush, UsersRound, X } from "lucide-react";
import { ConversationAvatar } from "@/components/messenger/conversation-avatar";
import { UserAvatar } from "@/components/profile/user-avatar";
import { clientApi, errorMessage } from "@/lib/client-api";
import { uploadMediaFile } from "@/lib/media-upload";
import { CHAT_THEMES, WALLPAPERS, formatPresence } from "@/lib/messenger-ui";
import type { MessengerConversation, User } from "@/lib/types";

export function ChatInfoPanel({
  conversation,
  me,
  onClose,
}: {
  conversation: MessengerConversation;
  me: User;
  onClose: () => void;
}) {
  const qc = useQueryClient();
  const [uploading, setUploading] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement | null>(null);
  const appearance = conversation.appearance;
  const other = conversation.kind === "direct" ? conversation.members.find(m => m.user.id !== me.id) : undefined;

  const update = useMutation({
    mutationFn: (payload: Record<string, unknown>) => clientApi<MessengerConversation>(`/messenger/conversations/${conversation.id}/`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }),
    onSuccess: data => {
      qc.setQueryData<MessengerConversation[]>(["messenger-conversations"], old => old?.map(item => item.id === data.id ? data : item));
      qc.invalidateQueries({ queryKey: ["messenger-conversations"] });
    },
  });

  const uploadWallpaper = async (file: File) => {
    if (!file.type.startsWith("image/")) return;
    setUploading(0);
    try {
      const asset = await uploadMediaFile(file, progress => setUploading(progress.percent));
      await update.mutateAsync({ wallpaper_asset_id: asset.id });
    } finally {
      setUploading(null);
    }
  };

  return (
    <aside className="messenger-info-panel">
      <header className="messenger-info-head">
        <div>
          <span className="eyebrow">CHAT / DETAILS</span>
          <strong>Информация</strong>
        </div>
        <button className="icon-button messenger-flat-button" onClick={onClose}><X size={17}/></button>
      </header>

      <div className="messenger-info-scroll">
        <section className="messenger-profile-summary">
          <ConversationAvatar conversation={conversation} me={me} size="lg"/>
          <h3>{conversation.display_title}</h3>
          <p>
            {conversation.kind === "direct"
              ? formatPresence(other)
              : `${conversation.members.length} участников · ${conversation.members.filter(m => m.online).length} в сети`}
          </p>
        </section>

        <section className="messenger-info-actions">
          <button onClick={() => update.mutate({ is_muted: !conversation.is_muted })}>
            {conversation.is_muted ? <Bell size={16}/> : <BellOff size={16}/>}<span>{conversation.is_muted ? "Включить уведомления" : "Без звука"}</span>
          </button>
          <button onClick={() => update.mutate({ is_archived: !conversation.is_archived })}>
            <Archive size={16}/><span>{conversation.is_archived ? "Вернуть из архива" : "В архив"}</span>
          </button>
        </section>

        <section className="messenger-settings-section">
          <div className="messenger-settings-title"><Paintbrush size={15}/><div><strong>Оформление чата</strong><span>Настройки видны только вам</span></div></div>

          <label className="messenger-setting-label">Акцент</label>
          <div className="chat-theme-grid">
            {CHAT_THEMES.map(theme => (
              <button
                key={theme.id}
                type="button"
                className={appearance?.chat_theme === theme.id ? "active" : ""}
                title={theme.label}
                onClick={() => update.mutate({ chat_theme: theme.id })}
              >
                <span style={{ background: theme.color }}/>
                <small>{theme.label}</small>
              </button>
            ))}
          </div>

          <label className="messenger-setting-label">Фон</label>
          <div className="wallpaper-grid">
            {WALLPAPERS.map(wallpaper => (
              <button
                key={wallpaper.id}
                type="button"
                className={`wallpaper-preview wallpaper-${wallpaper.id} ${appearance?.wallpaper === wallpaper.id ? "active" : ""}`}
                onClick={() => update.mutate({ wallpaper: wallpaper.id })}
              >
                <span>{wallpaper.label}</span>
              </button>
            ))}
            <button className={`wallpaper-preview wallpaper-custom ${appearance?.wallpaper === "custom" ? "active" : ""}`} onClick={() => fileRef.current?.click()}>
              <ImagePlus size={17}/><span>{uploading === null ? "Своя картинка" : `${uploading}%`}</span>
            </button>
            <input
              ref={fileRef}
              hidden
              type="file"
              accept="image/*"
              onChange={event => {
                const file = event.target.files?.[0];
                if (file) void uploadWallpaper(file);
                event.currentTarget.value = "";
              }}
            />
          </div>

          <div className="messenger-range-row">
            <label htmlFor="wallpaper-dim">Затемнение</label>
            <span>{appearance?.wallpaper_dim ?? 10}%</span>
          </div>
          <input
            id="wallpaper-dim"
            className="messenger-range"
            type="range"
            min="0"
            max="70"
            value={appearance?.wallpaper_dim ?? 10}
            onChange={event => update.mutate({ wallpaper_dim: Number(event.target.value) })}
          />

          <label className="messenger-toggle-row">
            <span><strong>Размытие фона</strong><small>Полезно для фотографий</small></span>
            <input type="checkbox" checked={appearance?.wallpaper_blur ?? false} onChange={event => update.mutate({ wallpaper_blur: event.target.checked })}/>
          </label>

          <label className="messenger-setting-label">Размер сообщений</label>
          <div className="messenger-segmented">
            {(["small", "normal", "large"] as const).map(scale => (
              <button key={scale} className={appearance?.message_scale === scale ? "active" : ""} onClick={() => update.mutate({ message_scale: scale })}>
                {scale === "small" ? "Мелко" : scale === "normal" ? "Обычно" : "Крупно"}
              </button>
            ))}
          </div>
          {update.error ? <div className="composer-error">{errorMessage(update.error)}</div> : null}
        </section>

        <section className="messenger-settings-section">
          <div className="messenger-settings-title"><UsersRound size={15}/><div><strong>{conversation.kind === "group" ? "Участники" : "Собеседник"}</strong><span>{conversation.members.length} в этом чате</span></div></div>
          <div className="messenger-member-list">
            {conversation.members.filter(member => member.user.id !== me.id || conversation.kind === "group").map(member => (
              <div key={member.user.id} className="messenger-member-row">
                <span className="messenger-member-avatar-wrap"><UserAvatar user={member.user} size="sm"/><i className={member.online ? "online" : ""}/></span>
                <span><strong>@{member.user.nickname}</strong><small>{member.online ? "в сети" : formatPresence(member)}</small></span>
                {member.role !== "member" ? <b>{member.role}</b> : null}
              </div>
            ))}
          </div>
        </section>
      </div>
    </aside>
  );
}
