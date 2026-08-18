"use client";

import { X } from "lucide-react";
import { useEffect, useState } from "react";

export function MetricCard({ label, value, detail, tone = "normal" }: { label:string; value:number|string; detail?:string; tone?:"normal"|"warning"|"danger" }) {
  return <div className={`admin-metric metric-${tone}`}><span>{label}</span><strong>{value}</strong>{detail ? <small>{detail}</small> : null}</div>;
}

export function StatusBadge({ value }: { value:string }) {
  const normalized = value.toLowerCase();
  const tone = ["published","active","resolved","done","ok"].includes(normalized) ? "good" : ["open","reviewing","pending"].includes(normalized) ? "warn" : ["hidden","inactive","failed"].includes(normalized) ? "bad" : "neutral";
  return <span className={`admin-status status-${tone}`}>{value}</span>;
}

export function AdminEmpty({ title, text }: { title:string; text:string }) { return <div className="admin-empty"><h3>{title}</h3><p>{text}</p></div>; }

export function ReasonDialog({ open, title, confirmLabel, onClose, onConfirm }: { open:boolean; title:string; confirmLabel:string; onClose:()=>void; onConfirm:(reason:string)=>Promise<void> }) {
  const [reason,setReason] = useState(""); const [busy,setBusy]=useState(false);
  useEffect(()=>{ if(open) setReason(""); },[open]); if(!open) return null;
  return <div className="admin-modal-backdrop" onMouseDown={onClose}><div className="admin-modal" onMouseDown={e=>e.stopPropagation()}><button className="admin-modal-close" onClick={onClose}><X size={17}/></button><div className="eyebrow">ПОДТВЕРЖДЕНИЕ</div><h2>{title}</h2><label>Причина<textarea rows={5} value={reason} onChange={e=>setReason(e.target.value)} placeholder="Кратко объясните действие. Причина попадёт в журнал модерации."/></label><div className="admin-modal-actions"><button className="secondary-button" onClick={onClose}>Отмена</button><button className="primary-button" disabled={busy} onClick={async()=>{setBusy(true);try{await onConfirm(reason);onClose();}finally{setBusy(false)}}}>{busy?"Сохраняем…":confirmLabel}</button></div></div></div>;
}
