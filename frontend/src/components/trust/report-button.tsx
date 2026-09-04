"use client";

import { Flag, Send, X } from "lucide-react";
import { FormEvent, useState } from "react";
import { clientApi, errorMessage } from "@/lib/client-api";
import { useAuth } from "@/providers/auth-provider";

type TargetType = "publication" | "comment" | "user";
type ReportReason = "spam" | "harassment" | "hate" | "violence" | "illegal" | "personal_data" | "copyright" | "other";

const reasons: Array<[ReportReason, string]> = [
  ["spam", "Спам или реклама"],
  ["harassment", "Оскорбления или преследование"],
  ["hate", "Ненависть"],
  ["violence", "Насилие или угрозы"],
  ["illegal", "Незаконный контент"],
  ["personal_data", "Персональные данные"],
  ["copyright", "Нарушение авторских прав"],
  ["other", "Другое"],
];

export function ReportButton({ targetType, targetId, compact = true }: { targetType: TargetType; targetId: string; compact?: boolean }) {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [reason, setReason] = useState<ReportReason>("spam");
  const [details, setDetails] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [sent, setSent] = useState(false);

  if (!user) return null;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      await clientApi("/reports/", {
        method: "POST",
        body: JSON.stringify({ target_type: targetType, target_id: targetId, reason, details }),
      });
      setSent(true);
      setOpen(false);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button type="button" className={compact ? "icon-button trust-report-trigger" : "secondary-button trust-report-trigger"} onClick={() => { setOpen(true); setError(""); }} title={sent ? "Жалоба уже отправлена" : "Пожаловаться"} disabled={sent}>
        <Flag size={compact ? 15 : 14}/>{compact ? null : sent ? "Отправлено" : "Пожаловаться"}
      </button>
      {open ? (
        <div className="trust-dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target) setOpen(false); }}>
          <form className="trust-dialog" onSubmit={submit}>
            <div className="trust-dialog-head"><div><div className="eyebrow">REPORT / TRUST</div><h2>Сообщить о проблеме</h2></div><button type="button" className="icon-button" onClick={() => setOpen(false)}><X size={16}/></button></div>
            <p>Жалоба попадёт в очередь модерации. Автор контента не увидит, кто её отправил.</p>
            <label>Причина<select value={reason} onChange={(event) => setReason(event.target.value as ReportReason)}>{reasons.map(([value,label]) => <option value={value} key={value}>{label}</option>)}</select></label>
            <label>Комментарий <span className="optional">{reason === "other" ? "обязательно" : "необязательно"}</span><textarea rows={4} maxLength={5000} value={details} onChange={(event) => setDetails(event.target.value)} required={reason === "other"} placeholder="Коротко опишите, что именно нарушает правила."/></label>
            {error ? <div className="form-error">{error}</div> : null}
            <div className="editor-actions"><span className="form-help">Повторная активная жалоба на тот же объект не создаётся.</span><button className="primary-button" disabled={busy}><Send size={14}/>{busy ? "Отправляем…" : "Отправить жалобу"}</button></div>
          </form>
        </div>
      ) : null}
    </>
  );
}
