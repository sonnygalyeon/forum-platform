import type { CSSProperties } from "react";
import type { MessengerActivityState, MessengerAppearance, MessengerMember } from "@/lib/types";

export const REACTION_PALETTE = ["👍","❤️","🔥","😂","👏","🤔","😮","😢","🎉","👀","💯","🤝"];

export const CHAT_THEMES = [
  { id: "iris", label: "Iris", color: "#20d691" },
  { id: "ocean", label: "Ocean", color: "#4aa8ff" },
  { id: "violet", label: "Violet", color: "#9b7cff" },
  { id: "amber", label: "Amber", color: "#f1b44c" },
  { id: "rose", label: "Rose", color: "#ef7094" },
  { id: "mono", label: "Mono", color: "#9da7a2" },
] as const;

export const WALLPAPERS = [
  { id: "iris-grid", label: "Iris Grid" },
  { id: "midnight", label: "Midnight" },
  { id: "aurora", label: "Aurora" },
  { id: "paper", label: "Paper" },
  { id: "graphite", label: "Graphite" },
  { id: "none", label: "Без фона" },
] as const;

export function activityLabel(state: MessengerActivityState | undefined, nickname?: string) {
  const who = nickname ? `${nickname} ` : "";
  switch (state) {
    case "typing": return `${who}печатает…`;
    case "uploading_file": return `${who}отправляет файл…`;
    case "uploading_photo": return `${who}отправляет фото…`;
    case "uploading_video": return `${who}отправляет видео…`;
    case "recording_voice": return `${who}записывает голосовое…`;
    case "choosing_sticker": return `${who}выбирает реакцию…`;
    default: return "";
  }
}

export function formatPresence(member?: MessengerMember) {
  if (!member) return "";
  if (member.online) return "в сети";
  if (!member.last_seen_at) return "не в сети";

  const date = new Date(member.last_seen_at);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.max(0, Math.floor(diff / 60000));

  if (minutes < 1) return "был(а) только что";
  if (minutes < 60) return `был(а) ${minutes} мин. назад`;
  if (date.toDateString() === now.toDateString()) {
    return `был(а) сегодня в ${date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}`;
  }
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) {
    return `был(а) вчера в ${date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" })}`;
  }
  return `был(а) ${date.toLocaleDateString("ru-RU", { day: "2-digit", month: "short" })}`;
}

export function activityStateForFile(file: File): MessengerActivityState {
  if (file.type.startsWith("image/")) return "uploading_photo";
  if (file.type.startsWith("video/")) return "uploading_video";
  return "uploading_file";
}

export function chatStageStyle(appearance: MessengerAppearance | null | undefined): CSSProperties {
  const customUrl = appearance?.wallpaper === "custom" ? appearance.wallpaper_asset?.url : null;
  return {
    ["--messenger-wallpaper-url" as string]: customUrl ? `url("${customUrl}")` : "none",
    ["--messenger-wallpaper-dim" as string]: String((appearance?.wallpaper_dim ?? 10) / 100),
  } as CSSProperties;
}

export function chatThemeClass(appearance: MessengerAppearance | null | undefined) {
  return `messenger-theme-${appearance?.chat_theme ?? "iris"}`;
}

export function wallpaperClass(appearance: MessengerAppearance | null | undefined) {
  return `messenger-wallpaper-${appearance?.wallpaper ?? "iris-grid"}`;
}

export function messageScaleClass(appearance: MessengerAppearance | null | undefined) {
  return `messenger-scale-${appearance?.message_scale ?? "normal"}`;
}
