"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { PublicationEngagement, PublicationReactionKind } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

const reactions: Array<{ kind: PublicationReactionKind; symbol: string; label: string }> = [
  { kind: "heart", symbol: "♥", label: "Нравится" },
  { kind: "insightful", symbol: "💡", label: "Полезная мысль" },
  { kind: "useful", symbol: "✓", label: "Практично" },
  { kind: "curious", symbol: "◉", label: "Интересно" },
];

export function PublicationEngagementBar({ publicationId }: { publicationId: string }) {
  const { user } = useAuth();
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: ["publication-engagement", publicationId],
    queryFn: () => clientApi<PublicationEngagement>("/publications/" + publicationId + "/engagement/"),
    refetchOnWindowFocus: true,
  });

  const reaction = useMutation({
    mutationFn: async (kind: PublicationReactionKind) => {
      if (query.data?.my_reaction === kind) {
        return clientApi<PublicationEngagement>("/publications/" + publicationId + "/reaction/", {
          method: "DELETE",
        });
      }
      return clientApi<PublicationEngagement>("/publications/" + publicationId + "/reaction/", {
        method: "PUT",
        body: JSON.stringify({ kind }),
      });
    },
    onSuccess: (data) => {
      qc.setQueryData(["publication-engagement", publicationId], data);
      void qc.invalidateQueries({ queryKey: ["home-feed"] });
      void qc.invalidateQueries({ queryKey: ["community-publications"] });
    },
  });

  if (query.isLoading || !query.data) return null;
  const data = query.data;

  return (
    <div className="publication-engagement">
      <div className="publication-reactions" aria-label="Реакции на публикацию">
        {reactions.map((item) => {
          const active = data.my_reaction === item.kind;
          const count = data.reactions[item.kind] ?? 0;
          return (
            <button
              key={item.kind}
              type="button"
              className={"reaction-button " + (active ? "active" : "")}
              disabled={!user || !data.can_react || reaction.isPending}
              onClick={() => reaction.mutate(item.kind)}
              title={!user ? "Войдите, чтобы реагировать" : !data.can_react ? "Реакция недоступна" : item.label}
              aria-pressed={active}
            >
              <span aria-hidden="true">{item.symbol}</span>
              <span>{item.label}</span>
              {count ? <b>{count}</b> : null}
            </button>
          );
        })}
      </div>
      <div className="engagement-summary">
        <span>{data.reaction_total} реакций</span>
        <span>{data.comment_count} комментариев</span>
        <span>{data.bookmark_count} сохранений</span>
      </div>
      {reaction.isError ? <div className="form-error">{errorMessage(reaction.error)}</div> : null}
    </div>
  );
}
