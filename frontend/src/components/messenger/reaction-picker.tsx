"use client";

import { useEffect, useRef, useState } from "react";
import { SmilePlus } from "lucide-react";
import { REACTION_PALETTE } from "@/lib/messenger-ui";

export function ReactionPicker({
  onPick,
  compact = false,
}: {
  onPick: (emoji: string) => void;
  compact?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: MouseEvent) => {
      if (!ref.current?.contains(event.target as Node)) setOpen(false);
    };
    window.addEventListener("mousedown", close);
    return () => window.removeEventListener("mousedown", close);
  }, [open]);

  return (
    <div className="reaction-picker" ref={ref}>
      <button
        type="button"
        className={compact ? "reaction-picker-trigger compact" : "reaction-picker-trigger"}
        title="Добавить реакцию"
        onClick={() => setOpen(value => !value)}
      >
        <SmilePlus size={compact ? 13 : 15}/>
      </button>
      {open ? (
        <div className="reaction-picker-popover">
          {REACTION_PALETTE.map(emoji => (
            <button
              type="button"
              key={emoji}
              onClick={() => {
                onPick(emoji);
                setOpen(false);
              }}
            >
              {emoji}
            </button>
          ))}
        </div>
      ) : null}
    </div>
  );
}
