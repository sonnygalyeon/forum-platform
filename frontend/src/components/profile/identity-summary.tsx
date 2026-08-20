import { Gauge, Sparkles } from "lucide-react";
import type { UserIdentity } from "@/lib/types";
import { IdentityBadges } from "./identity-badges";

export function IdentitySummary({ identity }: { identity: UserIdentity }) {
  return <div className="identity-summary">
    <div className="identity-score"><Gauge size={14}/><strong>{identity.reputation}</strong><span>репутация</span></div>
    <div className="identity-score"><Sparkles size={14}/><strong>{identity.level}</strong><span>уровень</span></div>
    <IdentityBadges badges={identity.badges}/>
  </div>;
}
