import type { LucideIcon } from "lucide-react";
import Link from "next/link";

export function EmptyState({ icon: Icon, title, text, action }: { icon?: LucideIcon; title: string; text: string; action?: {href:string; label:string} }) {
  return <div className="empty-state">{Icon ? <div className="empty-icon"><Icon size={25}/></div> : null}<h2>{title}</h2><p>{text}</p>{action ? <Link href={action.href} className="primary-button">{action.label}</Link> : null}</div>;
}
