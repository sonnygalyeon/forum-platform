"use client";

import { X } from "lucide-react";
import { useState } from "react";

export function MetricCard({
  label,
  value,
  detail,
  tone = "normal",
}: {
  label: string;
  value: number | string;
  detail?: string;
  tone?: "normal" | "warning" | "danger";
}) {
  return (
    <div className={`admin-metric metric-${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

export function StatusBadge({ value }: { value: string }) {
  const normalized = value.toLowerCase();
  const tone = [
    "published",
    "active",
    "resolved",
    "done",
    "ok",
  ].includes(normalized)
    ? "good"
    : ["open", "reviewing", "pending"].includes(normalized)
      ? "warn"
      : ["hidden", "inactive", "failed"].includes(normalized)
        ? "bad"
        : "neutral";

  return (
    <span className={`admin-status status-${tone}`}>
      {value}
    </span>
  );
}

export function AdminEmpty({
  title,
  text,
}: {
  title: string;
  text: string;
}) {
  return (
    <div className="admin-empty">
      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

type ReasonDialogProps = {
  open: boolean;
  title: string;
  confirmLabel: string;
  onClose: () => void;
  onConfirm: (reason: string) => Promise<void>;
};

function ReasonDialogContent({
  title,
  confirmLabel,
  onClose,
  onConfirm,
}: Omit<ReasonDialogProps, "open">) {
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);

  async function confirm() {
    setBusy(true);
    try {
      await onConfirm(reason);
      onClose();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="admin-modal-backdrop"
      onMouseDown={onClose}
    >
      <div
        className="admin-modal"
        onMouseDown={event => event.stopPropagation()}
      >
        <button
          className="admin-modal-close"
          onClick={onClose}
        >
          <X size={17} />
        </button>

        <div className="eyebrow">ПОДТВЕРЖДЕНИЕ</div>
        <h2>{title}</h2>

        <label>
          Причина
          <textarea
            rows={5}
            value={reason}
            onChange={event =>
              setReason(event.target.value)
            }
            placeholder="Кратко объясните действие. Причина попадёт в журнал модерации."
          />
        </label>

        <div className="admin-modal-actions">
          <button
            className="secondary-button"
            onClick={onClose}
          >
            Отмена
          </button>
          <button
            className="primary-button"
            disabled={busy}
            onClick={confirm}
          >
            {busy ? "Сохраняем…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export function ReasonDialog(props: ReasonDialogProps) {
  if (!props.open) return null;

  return (
    <ReasonDialogContent
      title={props.title}
      confirmLabel={props.confirmLabel}
      onClose={props.onClose}
      onConfirm={props.onConfirm}
    />
  );
}
