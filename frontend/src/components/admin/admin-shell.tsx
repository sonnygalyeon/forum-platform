"use client";

import Link from "next/link";
import { Activity, ChevronLeft, FileWarning, Gauge, History, LayoutList, MessageSquareWarning, ShieldCheck, UsersRound } from "lucide-react";
import { usePathname } from "next/navigation";
import { NightIrisMark } from "@/components/brand/night-iris-mark";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { useAuth } from "@/providers/auth-provider";
import { AdminGate } from "./admin-gate";

const items = [
  { href: "/admin", label: "Обзор", icon: Gauge },
  { href: "/admin/users", label: "Пользователи", icon: UsersRound },
  { href: "/admin/content", label: "Контент", icon: LayoutList },
  { href: "/admin/reports", label: "Жалобы", icon: MessageSquareWarning },
  { href: "/admin/communities", label: "Сообщества", icon: FileWarning },
  { href: "/admin/audit", label: "Журнал действий", icon: History },
  { href: "/admin/system", label: "Система", icon: Activity },
];

export function AdminShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { user } = useAuth();
  return <AdminGate><div className="admin-root">
    <header className="admin-header"><Link href="/admin"><NightIrisMark compact /></Link><div className="admin-header-title"><ShieldCheck size={16}/><span>Панель управления</span></div><div className="admin-header-actions"><ThemeToggle/><span className="admin-identity">@{user?.nickname}</span><Link className="secondary-button compact-button" href="/"><ChevronLeft size={14}/> На форум</Link></div></header>
    <div className="admin-layout"><aside className="admin-sidebar"><div className="eyebrow">УПРАВЛЕНИЕ</div><nav>{items.map(({href,label,icon:Icon}) => { const active = href === "/admin" ? pathname === href : pathname.startsWith(href); return <Link key={href} href={href} className={`admin-nav-item ${active ? "admin-nav-active" : ""}`}><Icon size={17}/><span>{label}</span></Link>; })}</nav><div className="admin-sidebar-foot"><span className="status-dot"/>Staff-only API<br/><small>Удаление контента не используется</small></div></aside><main className="admin-main enter-soft">{children}</main></div>
  </div></AdminGate>;
}
