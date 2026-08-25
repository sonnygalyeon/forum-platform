"use client";

import { Bell, BellRing, Eye, LockKeyhole, UsersRound, Volume2, X } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { MessengerSettings } from "@/lib/types";

const PRIVACY = [
  ["everyone", "Все"],
  ["following", "Мои подписки"],
  ["nobody", "Никто"],
] as const;

export function MessengerSettingsPanel({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const query = useQuery({ queryKey: ["messenger-settings"], queryFn: () => clientApi<MessengerSettings>("/messenger/settings/") });
  const update = useMutation({
    mutationFn: (payload: Partial<MessengerSettings>) => clientApi<MessengerSettings>("/messenger/settings/", { method: "PATCH", body: JSON.stringify(payload) }),
    onSuccess: data => qc.setQueryData(["messenger-settings"], data),
  });
  const settings = query.data;

  const requestBrowserPermission = async () => {
    if (typeof Notification === "undefined") return;
    const permission = await Notification.requestPermission();
    if (permission === "granted") update.mutate({ browser_notifications: true });
  };

  return <div className="messenger-settings-overlay">
    <aside className="messenger-settings-panel">
      <header><div><span className="eyebrow">MESSENGER / SETTINGS</span><strong>Настройки</strong></div><button className="icon-button messenger-flat-button" onClick={onClose}><X size={17}/></button></header>
      <div className="messenger-settings-scroll">
        {!settings ? <div className="messenger-settings-loading">Загрузка…</div> : <>
          <section>
            <div className="messenger-settings-title"><BellRing size={16}/><div><strong>Уведомления</strong><span>Для браузера и будущих мобильных клиентов</span></div></div>
            <label className="messenger-toggle-row"><span><strong>Browser notifications</strong><small>Показывать новые сообщения, когда вкладка в фоне</small></span><input type="checkbox" checked={settings.browser_notifications} onChange={e=>update.mutate({browser_notifications:e.target.checked})}/></label>
            <label className="messenger-toggle-row"><span><strong>Звук</strong><small>Короткий сигнал для новых сообщений</small></span><input type="checkbox" checked={settings.notification_sound} onChange={e=>update.mutate({notification_sound:e.target.checked})}/></label>
            <label className="messenger-toggle-row"><span><strong>Предпросмотр</strong><small>Показывать имя чата в уведомлении</small></span><input type="checkbox" checked={settings.notification_preview} onChange={e=>update.mutate({notification_preview:e.target.checked})}/></label>
            {typeof window !== "undefined" && "Notification" in window && Notification.permission !== "granted" ? <button className="secondary-button messenger-permission-button" onClick={requestBrowserPermission}><Bell size={14}/>Разрешить уведомления браузера</button> : null}
          </section>

          <section>
            <div className="messenger-settings-title"><LockKeyhole size={16}/><div><strong>Приватность</strong><span>Одинаковые правила будут использовать Web, Android и iOS</span></div></div>
            <PrivacyRow icon={<Bell size={14}/>} label="Кто может писать мне" value={settings.who_can_message} onChange={value=>update.mutate({who_can_message:value})}/>
            <PrivacyRow icon={<UsersRound size={14}/>} label="Кто может добавлять в группы" value={settings.who_can_add_to_groups} onChange={value=>update.mutate({who_can_add_to_groups:value})}/>
            <PrivacyRow icon={<Eye size={14}/>} label="Кто видит мой онлайн" value={settings.who_can_see_presence} onChange={value=>update.mutate({who_can_see_presence:value})}/>
          </section>

          <section className="messenger-core-note"><Volume2 size={15}/><p><strong>Core v2</strong><br/>Состояние сообщений, черновики и пропущенные realtime-события теперь синхронизируются через сервер.</p></section>
        </>}
        {update.error ? <div className="composer-error">{errorMessage(update.error)}</div> : null}
      </div>
    </aside>
  </div>;
}

function PrivacyRow({icon,label,value,onChange}:{icon:React.ReactNode;label:string;value:MessengerSettings["who_can_message"];onChange:(value:MessengerSettings["who_can_message"])=>void}) {
  return <label className="messenger-privacy-row"><span>{icon}{label}</span><select value={value} onChange={e=>onChange(e.target.value as MessengerSettings["who_can_message"])}>{PRIVACY.map(([id,text])=><option key={id} value={id}>{text}</option>)}</select></label>;
}
