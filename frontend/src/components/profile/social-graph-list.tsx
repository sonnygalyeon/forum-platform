"use client";

import Link from "next/link";
import { UserMinus, UserPlus, UsersRound } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { IdentityBadges } from "@/components/profile/identity-badges";
import { UserAvatar } from "@/components/profile/user-avatar";
import { clientApi } from "@/lib/client-api";
import type { SocialGraphConnection, SocialRecommendation } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

function isRecommendation(item: SocialGraphConnection | SocialRecommendation): item is SocialRecommendation {
  return "recommendation_reasons" in item;
}

export function SocialGraphList({
  items,
  empty,
}: {
  items: Array<SocialGraphConnection | SocialRecommendation>;
  empty: string;
}) {
  const { user: me } = useAuth();
  const qc = useQueryClient();

  const follow = useMutation({
    mutationFn: ({ userId, method }: { userId: string; method: "PUT" | "DELETE" }) =>
      clientApi("/users/" + userId + "/follow/", { method }),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ["user", variables.userId] });
      qc.invalidateQueries({ queryKey: ["social-summary", variables.userId] });
      qc.invalidateQueries({ queryKey: ["social-recommendations"] });
      qc.invalidateQueries({ queryKey: ["social-followers"] });
      qc.invalidateQueries({ queryKey: ["social-following"] });
      qc.invalidateQueries({ queryKey: ["social-mutuals"] });
    },
  });

  if (!items.length) return <div className="inline-empty">{empty}</div>;

  return (
    <div className="social-user-list">
      {items.map((item) => {
        const user = item.user;
        const own = me?.id === user.id;
        const pending = follow.isPending && follow.variables?.userId === user.id;
        return (
          <article className="social-user-card social-graph-card" key={user.id}>
            <Link href={"/users/" + user.id} className="social-graph-person">
              <UserAvatar user={user} size="md"/>
              <div className="social-graph-copy">
                <strong>{[user.first_name, user.last_name].filter(Boolean).join(" ") || user.nickname}</strong>
                <span>@{user.nickname}{user.identity.headline ? " · " + user.identity.headline : ""}</span>
                <IdentityBadges badges={user.identity.badges} compact/>
              </div>
            </Link>

            <div className="social-graph-context">
              <div className="social-graph-signals">
                {item.is_mutual ? <span className="soft-pill">Взаимная подписка</span> : item.follows_you ? <span className="soft-pill">Подписан на вас</span> : null}
                {item.mutual_count > 0 ? <span><UsersRound size={12}/>{item.mutual_count} общих подписок</span> : null}
                {item.shared_community_count > 0 ? <span>{item.shared_community_count} общих сообществ</span> : null}
                {item.shared_tag_count > 0 ? <span>{item.shared_tag_count} общих интересов</span> : null}
                {isRecommendation(item) ? item.recommendation_reasons.slice(0, 2).map((reason) => <span key={reason.code}>{reason.label}</span>) : null}
              </div>
              <div className="social-user-rep">
                <strong>{user.identity.reputation}</strong>
                <span>rep · lvl {user.identity.level}</span>
              </div>
              {!own && me ? (
                <button
                  className={item.is_following ? "secondary-button compact-button" : "primary-button compact-button"}
                  disabled={pending}
                  onClick={() => follow.mutate({ userId: user.id, method: item.is_following ? "DELETE" : "PUT" })}
                >
                  {item.is_following ? <><UserMinus size={13}/>Отписаться</> : <><UserPlus size={13}/>Подписаться</>}
                </button>
              ) : null}
            </div>
          </article>
        );
      })}
    </div>
  );
}
