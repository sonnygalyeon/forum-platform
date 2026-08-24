"use client";

import { FileText, Pencil, Pin, Reply, Trash2 } from "lucide-react";
import type { MessengerMessage, User } from "@/lib/types";
import { UserAvatar } from "@/components/profile/user-avatar";
import { ReactionPicker } from "@/components/messenger/reaction-picker";

export function MessageBubble({
  message,
  me,
  grouped,
  canPin,
  onReply,
  onEdit,
  onDelete,
  onToggleReaction,
  onPin,
}: {
  message: MessengerMessage;
  me: User;
  grouped: boolean;
  canPin: boolean;
  onReply: (message: MessengerMessage) => void;
  onEdit: (message: MessengerMessage) => void;
  onDelete: (message: MessengerMessage) => void;
  onToggleReaction: (message: MessengerMessage, emoji: string, active: boolean) => void;
  onPin: (message: MessengerMessage) => void;
}) {
  const own = message.sender.id === me.id;

  return (
    <article
      id={`message-${message.id}`}
      className={`message-line ${own ? "message-own" : ""} ${grouped ? "message-grouped" : ""} ${message.pinned ? "message-is-pinned" : ""}`}
    >
      {!own && !grouped ? <UserAvatar user={message.sender} size="xs"/> : <span className="message-avatar-spacer"/>}
      <div className="message-bubble-wrap">
        {!own && !grouped ? <span className="message-sender">@{message.sender.nickname}</span> : null}
        <div className={`message-bubble ${message.deleted ? "message-deleted" : ""}`}>
          {message.pinned ? <span className="message-pin-badge"><Pin size={10}/> закреплено</span> : null}
          {message.reply_to ? (
            <button
              className="message-reply-preview"
              onClick={() => document.getElementById(`message-${message.reply_to?.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })}
            >
              <strong>@{message.reply_to.sender_nickname}</strong>
              <span>{message.reply_to.deleted ? "Сообщение удалено" : message.reply_to.text}</span>
            </button>
          ) : null}

          {message.deleted ? (
            <p className="deleted-copy">Сообщение удалено</p>
          ) : (
            <>
              {message.attachments.length ? (
                <div className="message-attachments">
                  {message.attachments.map(asset =>
                    asset.kind === "image" && asset.url ? (
                      <a key={asset.id} href={asset.url} target="_blank" rel="noreferrer" className="message-image-link">
                        <img src={asset.url} alt={asset.original_name || asset.name || "Изображение"}/>
                      </a>
                    ) : asset.kind === "video" && asset.url ? (
                      <video key={asset.id} src={asset.url} controls/>
                    ) : asset.content_type?.startsWith("audio/") && asset.url ? (
                      <div className="message-audio" key={asset.id}>
                        <audio src={asset.url} controls preload="metadata"/>
                        <span>Голосовое сообщение</span>
                      </div>
                    ) : (
                      <a className="message-file" key={asset.id} href={asset.url || "#"} target="_blank" rel="noreferrer">
                        <span className="message-file-icon"><FileText size={18}/></span>
                        <span><strong>{asset.original_name || asset.name || "Файл"}</strong><small>{formatBytes(asset.size_bytes)}</small></span>
                      </a>
                    )
                  )}
                </div>
              ) : null}
              {message.text ? <p>{message.text}</p> : null}
            </>
          )}

          <span className="message-time">
            {message.edited_at ? <span className="message-edited-label">изм.</span> : null}
            {new Date(message.created_at).toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}
            {own ? <span className={`message-read-mark ${message.read_by_count > 0 ? "read" : ""}`}>{message.read_by_count > 0 ? "✓✓" : "✓"}</span> : null}
          </span>
        </div>

        {!message.deleted ? (
          <div className={`message-reactions ${message.reactions.length ? "" : "message-reactions-empty"}`}>
            {message.reactions.map(reaction => (
              <button
                key={reaction.emoji}
                className={reaction.reacted_by_me ? "active" : ""}
                onClick={() => onToggleReaction(message, reaction.emoji, reaction.reacted_by_me)}
              >
                <span className="reaction-emoji">{reaction.emoji}</span><span>{reaction.count}</span>
              </button>
            ))}
            <ReactionPicker compact onPick={emoji => onToggleReaction(message, emoji, false)}/>
          </div>
        ) : null}

        {!message.deleted ? (
          <div className="message-actions">
            <button title="Ответить" onClick={() => onReply(message)}><Reply size={14}/></button>
            <ReactionPicker compact onPick={emoji => onToggleReaction(message, emoji, false)}/>
            {canPin ? <button title="Закрепить" onClick={() => onPin(message)}><Pin size={13}/></button> : null}
            {own ? (
              <>
                <button title="Изменить" onClick={() => onEdit(message)}><Pencil size={13}/></button>
                <button title="Удалить" onClick={() => onDelete(message)}><Trash2 size={13}/></button>
              </>
            ) : null}
          </div>
        ) : null}
      </div>
    </article>
  );
}

function formatBytes(value?: number | null) {
  if (!value) return "";
  if (value < 1024) return `${value} B`;
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`;
  if (value < 1024 ** 3) return `${(value / 1024 ** 2).toFixed(1)} MB`;
  return `${(value / 1024 ** 3).toFixed(1)} GB`;
}
