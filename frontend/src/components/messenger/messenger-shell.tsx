"use client";

import Link from "next/link";
import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Archive,
  ArrowLeft,
  BellOff,
  Info,
  MessageCircle,
  Mic,
  Paperclip,
  Pin,
  Plus,
  Search,
  Send,
  Square,
  X,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { ChatInfoPanel } from "@/components/messenger/chat-info-panel";
import { ConversationAvatar } from "@/components/messenger/conversation-avatar";
import { MessageBubble } from "@/components/messenger/message-bubble";
import { NewChatPanel } from "@/components/messenger/new-chat-panel";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi, errorMessage } from "@/lib/client-api";
import { uploadMediaFile } from "@/lib/media-upload";
import {
  activityLabel,
  activityStateForFile,
  chatStageStyle,
  chatThemeClass,
  formatPresence,
  messageScaleClass,
  wallpaperClass,
} from "@/lib/messenger-ui";
import type {
  MediaAsset,
  MessengerActivityState,
  MessengerConversation,
  MessengerMessage,
  MessengerMessagesPage,
  MessengerSocketEvent,
} from "@/lib/types";
import { useMessengerSocket } from "@/hooks/use-messenger-socket";
import { useAuth } from "@/providers/auth-provider";

type ActivityEntry = { nickname: string; state: MessengerActivityState; userId: string };
type ListTab = "all" | "unread" | "archive";

export function MessengerShell({ initialConversationId }: { initialConversationId?: string }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();

  const [newChat, setNewChat] = useState(false);
  const [text, setText] = useState("");
  const [reply, setReply] = useState<MessengerMessage | null>(null);
  const [attachments, setAttachments] = useState<MediaAsset[]>([]);
  const [uploading, setUploading] = useState<number | null>(null);
  const [activities, setActivities] = useState<Record<string, Record<string, ActivityEntry>>>({});
  const [listSearch, setListSearch] = useState("");
  const [listTab, setListTab] = useState<ListTab>("all");
  const [infoOpen, setInfoOpen] = useState(false);
  const [chatSearchOpen, setChatSearchOpen] = useState(false);
  const [chatSearch, setChatSearch] = useState("");
  const [recording, setRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const [voiceError, setVoiceError] = useState("");

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recordingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const typingTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const activityExpiry = useRef<Record<string, ReturnType<typeof setTimeout>>>({});
  const endRef = useRef<HTMLDivElement | null>(null);

  const conversations = useQuery({
    queryKey: ["messenger-conversations"],
    queryFn: () => clientApi<MessengerConversation[]>("/messenger/conversations/?archived=1"),
    enabled: Boolean(user),
    refetchInterval: 30000,
  });

  const availableConversations = useMemo(() => {
    const q = listSearch.trim().toLocaleLowerCase("ru-RU");
    return (conversations.data ?? []).filter(conversation => {
      if (listTab === "archive" && !conversation.is_archived) return false;
      if (listTab !== "archive" && conversation.is_archived) return false;
      if (listTab === "unread" && conversation.unread_count < 1) return false;
      if (!q) return true;
      const haystack = `${conversation.display_title} ${conversation.last_message?.text ?? ""}`.toLocaleLowerCase("ru-RU");
      return haystack.includes(q);
    });
  }, [conversations.data, listSearch, listTab]);

  const selectedId = initialConversationId || availableConversations[0]?.id || conversations.data?.find(c => !c.is_archived)?.id;
  const selected = conversations.data?.find(conversation => conversation.id === selectedId);

  const messages = useQuery({
    queryKey: ["messenger-messages", selectedId],
    queryFn: () => clientApi<MessengerMessagesPage>(`/messenger/conversations/${selectedId}/messages/?limit=100`),
    enabled: Boolean(user && selectedId),
  });

  const searchResults = useQuery({
    queryKey: ["messenger-message-search", selectedId, chatSearch],
    queryFn: () => clientApi<MessengerMessagesPage>(`/messenger/conversations/${selectedId}/messages/?limit=40&q=${encodeURIComponent(chatSearch.trim())}`),
    enabled: Boolean(user && selectedId && chatSearchOpen && chatSearch.trim().length >= 2),
  });

  const handleEvent = (event: MessengerSocketEvent) => {
    if (event.type === "activity" && event.conversation_id && event.user_id && event.user_id !== user?.id) {
      const conversationId = event.conversation_id;
      const userId = event.user_id;
      const state = event.state ?? "none";
      const key = `${conversationId}:${userId}`;

      if (activityExpiry.current[key]) clearTimeout(activityExpiry.current[key]);
      setActivities(current => {
        const conversation = { ...(current[conversationId] ?? {}) };
        if (state === "none") delete conversation[userId];
        else conversation[userId] = { nickname: event.nickname ?? "", state, userId };
        return { ...current, [conversationId]: conversation };
      });

      if (state !== "none") {
        activityExpiry.current[key] = setTimeout(() => {
          setActivities(current => {
            const conversation = { ...(current[conversationId] ?? {}) };
            delete conversation[userId];
            return { ...current, [conversationId]: conversation };
          });
        }, 6500);
      }
      return;
    }

    if (
      event.type === "presence" ||
      event.type.startsWith("message.") ||
      event.type.startsWith("conversation.")
    ) {
      qc.invalidateQueries({ queryKey: ["messenger-conversations"] });
      qc.invalidateQueries({ queryKey: ["messenger-unread"] });
      if (event.conversation_id) {
        qc.invalidateQueries({ queryKey: ["messenger-messages", event.conversation_id] });
        qc.invalidateQueries({ queryKey: ["messenger-message-search", event.conversation_id] });
      }
    }
  };

  const { connected, sendActivity, sendTyping } = useMessengerSocket(handleEvent, Boolean(user));

  useEffect(() => {
    if (!selectedId || typeof window === "undefined") return;
    setText(window.localStorage.getItem(`night-iris:draft:${selectedId}`) ?? "");
    setReply(null);
    setAttachments([]);
    setInfoOpen(false);
    setChatSearchOpen(false);
    setChatSearch("");
  }, [selectedId]);

  const send = useMutation({
    mutationFn: () => clientApi<MessengerMessage>(`/messenger/conversations/${selectedId}/messages/`, {
      method: "POST",
      body: JSON.stringify({
        client_id: crypto.randomUUID(),
        text,
        reply_to_id: reply?.id || null,
        attachment_ids: attachments.map(asset => asset.id),
      }),
    }),
    onSuccess: () => {
      if (selectedId && typeof window !== "undefined") window.localStorage.removeItem(`night-iris:draft:${selectedId}`);
      setText("");
      setReply(null);
      setAttachments([]);
      if (selectedId) sendActivity(selectedId, "none");
      qc.invalidateQueries({ queryKey: ["messenger-messages", selectedId] });
      qc.invalidateQueries({ queryKey: ["messenger-conversations"] });
    },
  });

  const read = useMutation({
    mutationFn: (messageId?: string) => clientApi(`/messenger/conversations/${selectedId}/read/`, {
      method: "POST",
      body: JSON.stringify({ message_id: messageId || null }),
    }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["messenger-conversations"] });
      qc.invalidateQueries({ queryKey: ["messenger-unread"] });
    },
  });

  const edit = useMutation({
    mutationFn: ({ message, nextText }: { message: MessengerMessage; nextText: string }) => clientApi(`/messenger/messages/${message.id}/`, {
      method: "PATCH",
      body: JSON.stringify({ text: nextText }),
    }),
    onSettled: () => qc.invalidateQueries({ queryKey: ["messenger-messages", selectedId] }),
  });

  const remove = useMutation({
    mutationFn: (message: MessengerMessage) => clientApi(`/messenger/messages/${message.id}/`, { method: "DELETE" }),
    onSettled: () => {
      qc.invalidateQueries({ queryKey: ["messenger-messages", selectedId] });
      qc.invalidateQueries({ queryKey: ["messenger-conversations"] });
    },
  });

  const reaction = useMutation({
    mutationFn: ({ message, emoji, active }: { message: MessengerMessage; emoji: string; active: boolean }) => clientApi(
      `/messenger/messages/${message.id}/reaction/`,
      active
        ? { method: "DELETE", body: JSON.stringify({ emoji }) }
        : { method: "PUT", body: JSON.stringify({ emoji }) },
    ),
    onMutate: async ({ message, emoji, active }) => {
      const key = ["messenger-messages", selectedId];
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData<MessengerMessagesPage>(key);
      qc.setQueryData<MessengerMessagesPage>(key, old => {
        if (!old) return old;
        return {
          ...old,
          results: old.results.map(item => {
            if (item.id !== message.id) return item;
            const reactions = [...item.reactions];
            const index = reactions.findIndex(value => value.emoji === emoji);
            if (active) {
              if (index < 0) return item;
              const current = reactions[index];
              const count = Math.max(0, current.count - 1);
              if (count === 0) reactions.splice(index, 1);
              else reactions[index] = { ...current, count, reacted_by_me: false };
            } else if (index >= 0) {
              reactions[index] = { ...reactions[index], count: reactions[index].count + 1, reacted_by_me: true };
            } else {
              reactions.push({ emoji, count: 1, reacted_by_me: true });
            }
            return { ...item, reactions };
          }),
        };
      });
      return { previous };
    },
    onError: (_error, _vars, context) => {
      if (context?.previous) qc.setQueryData(["messenger-messages", selectedId], context.previous);
    },
    onSettled: () => qc.invalidateQueries({ queryKey: ["messenger-messages", selectedId] }),
  });

  const pin = useMutation({
    mutationFn: (message: MessengerMessage | null) => clientApi<MessengerConversation>(`/messenger/conversations/${selectedId}/pinned/`, {
      method: "PUT",
      body: JSON.stringify({ message_id: message?.id ?? null }),
    }),
    onSuccess: data => {
      qc.setQueryData<MessengerConversation[]>(["messenger-conversations"], old => old?.map(item => item.id === data.id ? data : item));
      qc.invalidateQueries({ queryKey: ["messenger-messages", selectedId] });
      qc.invalidateQueries({ queryKey: ["messenger-conversations"] });
    },
  });

  useEffect(() => {
    const last = messages.data?.results.at(-1);
    if (last && selectedId) read.mutate(last.id);
    endRef.current?.scrollIntoView({ behavior: "smooth" });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [messages.data?.results.length, selectedId]);

  useEffect(() => () => {
    if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    const recorder = mediaRecorderRef.current;
    if (recorder && recorder.state !== "inactive") recorder.stop();
    mediaStreamRef.current?.getTracks().forEach(track => track.stop());
  }, []);

  if (!loading && !user) {
    return <AppShell wide><EmptyState icon={MessageCircle} title="Мессенджер доступен после входа" text="Личные и групповые чаты Night Iris синхронизируются через общий API и WebSocket." action={{ href: "/login", label: "Войти" }}/></AppShell>;
  }
  if (!user) return <AppShell wide><LoadingBlock/></AppShell>;

  const onType = (value: string) => {
    setText(value);
    if (!selectedId) return;
    if (typeof window !== "undefined") window.localStorage.setItem(`night-iris:draft:${selectedId}`, value);
    sendTyping(selectedId, Boolean(value.trim()));
    if (typingTimer.current) clearTimeout(typingTimer.current);
    typingTimer.current = setTimeout(() => sendTyping(selectedId, false), 1400);
  };

  const upload = async (file: File) => {
    if (!selectedId) return;
    const state = activityStateForFile(file);
    setUploading(0);
    sendActivity(selectedId, state);
    try {
      const asset = await uploadMediaFile(file, progress => setUploading(progress.percent));
      setAttachments(current => [...current, asset]);
    } finally {
      setUploading(null);
      sendActivity(selectedId, "none");
    }
  };

  const startVoiceRecording = async () => {
    if (!selectedId || recording) return;
    setVoiceError("");
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
      setVoiceError("Запись голоса не поддерживается этим браузером.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaStreamRef.current = stream;
      const preferred = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"].find(type => MediaRecorder.isTypeSupported(type));
      const recorder = new MediaRecorder(stream, preferred ? { mimeType: preferred } : undefined);
      audioChunksRef.current = [];
      mediaRecorderRef.current = recorder;
      recorder.ondataavailable = event => { if (event.data.size) audioChunksRef.current.push(event.data); };
      recorder.onstop = async () => {
        const mime = recorder.mimeType || "audio/webm";
        const extension = mime.includes("mp4") ? "m4a" : "webm";
        const blob = new Blob(audioChunksRef.current, { type: mime });
        audioChunksRef.current = [];
        if (!blob.size || !selectedId) return;
        sendActivity(selectedId, "uploading_file");
        setUploading(0);
        try {
          const file = new File([blob], `voice-${Date.now()}.${extension}`, { type: mime });
          const asset = await uploadMediaFile(file, progress => setUploading(progress.percent));
          setAttachments(current => [...current, asset]);
        } catch {
          setVoiceError("Не удалось загрузить голосовое сообщение.");
        } finally {
          setUploading(null);
          sendActivity(selectedId, "none");
        }
      };
      recorder.start(250);
      setRecording(true);
      setRecordingSeconds(0);
      sendActivity(selectedId, "recording_voice");
      recordingTimerRef.current = setInterval(() => setRecordingSeconds(value => value + 1), 1000);
    } catch {
      setVoiceError("Нет доступа к микрофону.");
    }
  };

  const stopVoiceRecording = () => {
    if (!recording) return;
    if (recordingTimerRef.current) clearInterval(recordingTimerRef.current);
    recordingTimerRef.current = null;
    setRecording(false);
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    mediaStreamRef.current?.getTracks().forEach(track => track.stop());
    mediaStreamRef.current = null;
  };

  const selectedActivity = selectedId ? Object.values(activities[selectedId] ?? {})[0] : undefined;
  const otherMember = selected?.kind === "direct" ? selected.members.find(member => member.user.id !== user.id) : undefined;
  const statusText = selectedActivity
    ? activityLabel(selectedActivity.state, selected?.kind === "group" ? selectedActivity.nickname : undefined)
    : selected?.kind === "direct"
      ? formatPresence(otherMember)
      : selected
        ? `${selected.members.length} участников · ${selected.members.filter(member => member.online).length} в сети`
        : "";
  const canPin = Boolean(selected && (selected.kind === "direct" || selected.members.find(member => member.user.id === user.id)?.role !== "member"));

  return (
    <AppShell wide>
      <section className={`messenger-layout messenger-polished ${initialConversationId ? "messenger-conversation-route" : "messenger-list-route"} ${infoOpen && selected ? "messenger-info-open" : ""}`}>
        <aside className={`messenger-sidebar ${initialConversationId ? "mobile-chat-open" : ""}`}>
          <div className="messenger-title">
            <div><div className="eyebrow">NIGHT IRIS</div><h1>Messenger</h1></div>
            <button className="primary-icon-button" onClick={() => setNewChat(true)} title="Новый чат"><Plus size={18}/></button>
          </div>

          <div className="messenger-search-box">
            <Search size={15}/>
            <input value={listSearch} onChange={event => setListSearch(event.target.value)} placeholder="Поиск чатов"/>
            {listSearch ? <button onClick={() => setListSearch("")}><X size={13}/></button> : null}
          </div>

          <div className="messenger-list-tabs">
            <button className={listTab === "all" ? "active" : ""} onClick={() => setListTab("all")}>Все</button>
            <button className={listTab === "unread" ? "active" : ""} onClick={() => setListTab("unread")}>Новые</button>
            <button className={listTab === "archive" ? "active" : ""} onClick={() => setListTab("archive")}><Archive size={12}/> Архив</button>
          </div>

          <div className="messenger-connection"><span className={connected ? "online" : ""}/>{connected ? "синхронизация в реальном времени" : "переподключение…"}</div>

          {newChat ? (
            <NewChatPanel
              onClose={() => setNewChat(false)}
              onCreated={conversation => {
                setNewChat(false);
                qc.invalidateQueries({ queryKey: ["messenger-conversations"] });
                router.push(`/messages/${conversation.id}`);
              }}
            />
          ) : (
            <div className="conversation-list">
              {conversations.isLoading ? <LoadingBlock/> : availableConversations.length ? availableConversations.map(conversation => {
                const active = selectedId === conversation.id;
                const activity = Object.values(activities[conversation.id] ?? {})[0];
                return (
                  <Link href={`/messages/${conversation.id}`} key={conversation.id} className={`conversation-row ${active ? "active" : ""}`}>
                    <ConversationAvatar conversation={conversation} me={user} size="sm"/>
                    <span className="conversation-copy">
                      <strong>{conversation.display_title}{conversation.is_muted ? <BellOff size={10}/> : null}</strong>
                      <small className={activity ? "conversation-activity" : ""}>
                        {activity
                          ? activityLabel(activity.state, conversation.kind === "group" ? activity.nickname : undefined)
                          : conversation.last_message
                            ? `${conversation.last_message.sender_id === user.id ? "Вы: " : ""}${conversation.last_message.text}`
                            : "Чат создан"}
                      </small>
                    </span>
                    <span className="conversation-meta">
                      <time>{conversation.last_message_at ? formatConversationTime(conversation.last_message_at) : ""}</time>
                      {conversation.unread_count ? <b>{conversation.unread_count > 99 ? "99+" : conversation.unread_count}</b> : null}
                    </span>
                  </Link>
                );
              }) : (
                <div className="messenger-empty-list"><MessageCircle/><strong>{listSearch ? "Ничего не найдено" : "Здесь пока тихо"}</strong><span>{listSearch ? "Попробуйте другой запрос." : "Начните личный чат или создайте группу."}</span>{!listSearch ? <button onClick={() => setNewChat(true)}>Новый чат</button> : null}</div>
              )}
            </div>
          )}
        </aside>

        <main className={`messenger-chat ${selected ? "has-chat" : ""} ${selected ? chatThemeClass(selected.appearance) : ""}`}>
          {selected ? (
            <>
              <header className="chat-header">
                <Link href="/messages" className="mobile-chat-back"><ArrowLeft size={18}/></Link>
                <ConversationAvatar conversation={selected} me={user} size="sm"/>
                <button className="chat-header-identity" onClick={() => setInfoOpen(true)}>
                  <strong>{selected.display_title}</strong>
                  <span className={otherMember?.online || selectedActivity ? "active-status" : ""}>{statusText}</span>
                </button>
                <div className="chat-header-actions">
                  <button className={`icon-button messenger-flat-button ${chatSearchOpen ? "active" : ""}`} title="Поиск в чате" onClick={() => setChatSearchOpen(value => !value)}><Search size={17}/></button>
                  <button className={`icon-button messenger-flat-button ${infoOpen ? "active" : ""}`} title="Информация о чате" onClick={() => setInfoOpen(value => !value)}><Info size={17}/></button>
                </div>
              </header>

              {chatSearchOpen ? (
                <div className="chat-search-bar">
                  <Search size={15}/><input autoFocus value={chatSearch} onChange={event => setChatSearch(event.target.value)} placeholder="Найти сообщение…"/>
                  {searchResults.data ? <span>{searchResults.data.results.length}</span> : null}
                  <button onClick={() => { setChatSearchOpen(false); setChatSearch(""); }}><X size={15}/></button>
                </div>
              ) : null}

              {chatSearchOpen && chatSearch.trim().length >= 2 && searchResults.data?.results.length ? (
                <div className="chat-search-results">
                  {searchResults.data.results.slice().reverse().map(message => (
                    <button key={message.id} onClick={() => document.getElementById(`message-${message.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })}>
                      <strong>@{message.sender.nickname}</strong><span>{message.text || "Вложение"}</span><time>{new Date(message.created_at).toLocaleDateString("ru-RU")}</time>
                    </button>
                  ))}
                </div>
              ) : null}

              {selected.pinned_message ? (
                <div className="chat-pinned-bar">
                  <button onClick={() => document.getElementById(`message-${selected.pinned_message?.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })}>
                    <Pin size={14}/><span><strong>Закреплённое сообщение</strong><small>@{selected.pinned_message.sender_nickname}: {selected.pinned_message.text}</small></span>
                  </button>
                  {canPin ? <button className="chat-pinned-close" title="Открепить" onClick={() => pin.mutate(null)}><X size={14}/></button> : null}
                </div>
              ) : null}

              <div
                className={`message-stage ${wallpaperClass(selected.appearance)} ${messageScaleClass(selected.appearance)} ${selected.appearance?.wallpaper_blur ? "messenger-wallpaper-blur" : ""}`}
                style={chatStageStyle(selected.appearance)}
              >
                <div className="message-wallpaper"/>
                <div className="message-wallpaper-dim"/>
                <div className="message-scroll">
                  {messages.isLoading ? <LoadingBlock/> : messages.data?.results.map((message, index) => {
                    const previous = messages.data!.results[index - 1];
                    const grouped = Boolean(
                      previous &&
                      previous.sender.id === message.sender.id &&
                      sameDay(previous.created_at, message.created_at) &&
                      new Date(message.created_at).getTime() - new Date(previous.created_at).getTime() < 5 * 60 * 1000
                    );
                    const showDate = !previous || !sameDay(previous.created_at, message.created_at);
                    return (
                      <Fragment key={message.id}>
                        {showDate ? <div className="message-date-separator"><span>{formatMessageDay(message.created_at)}</span></div> : null}
                        <MessageBubble
                          message={message}
                          me={user}
                          grouped={grouped}
                          canPin={canPin}
                          onReply={setReply}
                          onEdit={current => {
                            const value = window.prompt("Изменить сообщение", current.text);
                            if (value !== null) edit.mutate({ message: current, nextText: value });
                          }}
                          onDelete={current => {
                            if (window.confirm("Удалить сообщение для всех участников?")) remove.mutate(current);
                          }}
                          onToggleReaction={(current, emoji, active) => reaction.mutate({ message: current, emoji, active })}
                          onPin={current => pin.mutate(current)}
                        />
                      </Fragment>
                    );
                  })}
                  <div ref={endRef}/>
                </div>
              </div>

              <footer className="chat-composer">
                {reply ? (
                  <div className="composer-reply">
                    <span className="composer-reply-icon">↩</span>
                    <span><strong>@{reply.sender.nickname}</strong>{reply.text || "Вложение"}</span>
                    <button onClick={() => setReply(null)}><X size={13}/></button>
                  </div>
                ) : null}

                {attachments.length ? (
                  <div className="composer-attachments">
                    {attachments.map(asset => (
                      <span key={asset.id}>{asset.kind === "image" ? "🖼" : asset.kind === "video" ? "🎬" : "📎"} {asset.original_name || asset.name}<button onClick={() => setAttachments(current => current.filter(value => value.id !== asset.id))}><X size={10}/></button></span>
                    ))}
                  </div>
                ) : null}

                <div className="composer-shell">
                  <div className="composer-tools">
                    <label className="composer-attach" title="Прикрепить файл">
                      <Paperclip size={19}/>{uploading !== null ? <b>{uploading}%</b> : null}
                      <input type="file" onChange={event => { const file = event.target.files?.[0]; if (file) void upload(file); event.currentTarget.value = ""; }}/>
                    </label>
                    <button type="button" className={`composer-voice ${recording ? "recording" : ""}`} title={recording ? "Остановить запись" : "Голосовое сообщение"} onClick={() => recording ? stopVoiceRecording() : void startVoiceRecording()}>
                      {recording ? <Square size={14}/> : <Mic size={18}/>}
                    </button>
                  </div>
                  <textarea
                    rows={1}
                    value={text}
                    onChange={event => onType(event.target.value)}
                    onKeyDown={event => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        if ((text.trim() || attachments.length) && !send.isPending) send.mutate();
                      }
                    }}
                    placeholder={recording ? `Запись голоса · ${formatDuration(recordingSeconds)}` : "Сообщение"}
                    disabled={recording}
                  />
                  <button className="composer-send" disabled={(!text.trim() && !attachments.length) || send.isPending} onClick={() => send.mutate()}><Send size={18}/></button>
                </div>
                <div className="composer-hint"><span>{connected ? "● realtime" : "○ reconnecting"}</span><span>Enter — отправить · Shift+Enter — новая строка</span></div>
                {voiceError ? <div className="composer-error">{voiceError}</div> : null}
                {send.error ? <div className="composer-error">{errorMessage(send.error)}</div> : null}
              </footer>
            </>
          ) : (
            <div className="messenger-chat-empty">
              <div className="messenger-empty-mark"><MessageCircle size={34}/></div>
              <h2>Night Iris Messenger</h2>
              <p>Личные сообщения, группы, быстрые реакции и синхронизация в реальном времени — в одном спокойном пространстве.</p>
              <button className="primary-button" onClick={() => setNewChat(true)}><Plus size={15}/>Новый чат</button>
            </div>
          )}
        </main>

        {infoOpen && selected ? <ChatInfoPanel conversation={selected} me={user} onClose={() => setInfoOpen(false)}/> : null}
      </section>
    </AppShell>
  );
}

function sameDay(left: string, right: string) {
  return new Date(left).toDateString() === new Date(right).toDateString();
}

function formatMessageDay(value: string) {
  const date = new Date(value);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) return "Сегодня";
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === yesterday.toDateString()) return "Вчера";
  return date.toLocaleDateString("ru-RU", { day: "numeric", month: "long", year: date.getFullYear() === now.getFullYear() ? undefined : "numeric" });
}

function formatConversationTime(value: string) {
  const date = new Date(value);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) return date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  const diff = Math.floor((now.getTime() - date.getTime()) / 86400000);
  if (diff < 6) return date.toLocaleDateString("ru-RU", { weekday: "short" });
  return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "2-digit" });
}

function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60);
  const rest = seconds % 60;
  return `${minutes}:${String(rest).padStart(2, "0")}`;
}
