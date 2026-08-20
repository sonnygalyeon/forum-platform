import { Award, BadgeCheck, CircleDot, FileText, Link2, MessageSquare, ShieldCheck, Sparkles, UsersRound } from "lucide-react";
import type { OwnedBadge } from "@/lib/types";

const icons = {
  iris: CircleDot,
  file: FileText,
  message: MessageSquare,
  check: BadgeCheck,
  users: UsersRound,
  spark: Sparkles,
  link: Link2,
  shield: ShieldCheck,
} as const;

export function IdentityBadges({ badges, compact = false }: { badges?: OwnedBadge[]; compact?: boolean }) {
  if (!badges?.length) return null;
  return <div className={`identity-badges ${compact ? "identity-badges-compact" : ""}`}>
    {badges.map(({ badge }) => {
      const Icon = icons[badge.icon_key as keyof typeof icons] ?? Award;
      return <span key={badge.id} className={`identity-badge badge-tier-${badge.tier}`} title={badge.description}>
        <Icon size={compact ? 11 : 13}/><span>{badge.name}</span>
      </span>;
    })}
  </div>;
}
