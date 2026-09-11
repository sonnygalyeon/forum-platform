"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MoreHorizontal, X } from "lucide-react";
import { useState } from "react";

import { clientApi, errorMessage } from "@/lib/client-api";
import type { CursorPage, FeedFeedbackReason, Publication } from "@/lib/types";


const options: Array<{ reason: FeedFeedbackReason; label: string; hint: string }> = [
  {
    reason: "not_interested",
    label: "Не интересно",
    hint: "Реже показывать похожие темы.",
  },
  {
    reason: "too_repetitive",
    label: "Слишком много похожего",
    hint: "Разбавить этого автора или сообщество.",
  },
  {
    reason: "already_seen",
    label: "Уже видел",
    hint: "Просто убрать эту публикацию.",
  },
];

export function FeedFeedbackControl({ publicationId }: { publicationId: string }) {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);

  const removeFromCachedFeed = () => {
    qc.setQueriesData<CursorPage<Publication>>(
      { queryKey: ["home-feed"] },
      (current) => current
        ? { ...current, results: current.results.filter((item) => item.id !== publicationId) }
        : current,
    );
  };

  const feedback = useMutation({
    mutationFn: (reason: FeedFeedbackReason) => clientApi<{ reason: FeedFeedbackReason }>(
      "/publications/" + publicationId + "/feed-feedback/",
      {
        method: "PUT",
        body: JSON.stringify({ reason }),
      },
    ),
    onSuccess: () => {
      setOpen(false);
      removeFromCachedFeed();
      void qc.invalidateQueries({ queryKey: ["home-feed"] });
    },
  });

  return (
    <div className="feed-feedback-control">
      <button
        type="button"
        className="icon-button feed-feedback-trigger"
        aria-label="Настроить ленту"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        {open ? <X size={15}/> : <MoreHorizontal size={16}/>}
      </button>

      {open ? (
        <div className="feed-feedback-menu">
          <strong>Настроить ленту</strong>
          {options.map((option) => (
            <button
              type="button"
              key={option.reason}
              disabled={feedback.isPending}
              onClick={() => feedback.mutate(option.reason)}
            >
              <span>{option.label}</span>
              <small>{option.hint}</small>
            </button>
          ))}
          {feedback.isError ? <div className="form-error">{errorMessage(feedback.error)}</div> : null}
        </div>
      ) : null}
    </div>
  );
}
