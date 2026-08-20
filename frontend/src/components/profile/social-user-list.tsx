import Link from "next/link";
import { IdentityBadges } from "@/components/profile/identity-badges";
import { UserAvatar } from "@/components/profile/user-avatar";
import type { SocialUserEdge } from "@/lib/types";

export function SocialUserList({ edges, empty }: { edges: SocialUserEdge[]; empty: string }) {
  if (!edges.length) return <div className="inline-empty">{empty}</div>;
  return <div className="social-user-list">{edges.map(({user})=><Link className="social-user-card" href={`/users/${user.id}`} key={user.id}><UserAvatar user={user} size="md"/><div><strong>{[user.first_name,user.last_name].filter(Boolean).join(" ")||user.nickname}</strong><span>@{user.nickname}{user.identity.headline?` · ${user.identity.headline}`:""}</span><IdentityBadges badges={user.identity.badges} compact/></div><div className="social-user-rep"><strong>{user.identity.reputation}</strong><span>rep · lvl {user.identity.level}</span></div></Link>)}</div>;
}
