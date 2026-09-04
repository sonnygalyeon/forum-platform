"use client";

import Link from "next/link";
import { Bell, Bookmark, Compass, FileEdit, Flag, Home, MessageCircle, PlusSquare, Search, ShieldCheck, UsersRound, UserRound } from "lucide-react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { MessengerUnreadBadge } from "@/components/messenger/unread-badge";

const publicItems = [
  { href: "/", label: "Лента", icon: Home },
  { href: "/discover", label: "Открыть", icon: Compass },
  { href: "/search", label: "Поиск", icon: Search },
  { href: "/communities", label: "Сообщества", icon: UsersRound },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = user ? [
    ...publicItems,
    { href: "/new", label: "Создать", icon: PlusSquare },
    { href: "/saved", label: "Сохранённое", icon: Bookmark },
    { href: "/drafts", label: "Черновики", icon: FileEdit },
    { href: "/messages", label: "Сообщения", icon: MessageCircle },
    { href: "/notifications", label: "Уведомления", icon: Bell },
    { href: "/profile", label: "Профиль", icon: UserRound },
    { href: "/reports", label: "Мои обращения", icon: Flag },
    ...(user.is_staff ? [{ href: "/admin", label: "Админка", icon: ShieldCheck }] : []),
  ] : publicItems;
  return <aside className="sidebar"><div className="eyebrow">НАВИГАЦИЯ</div><nav>{items.map(({href,label,icon:Icon}) => <Link key={href} href={href} className={`nav-item ${pathname === href || (href!=="/"&&pathname.startsWith(href)) ? "nav-item-active" : ""}`}><Icon size={17}/>{label}{href === "/messages" ? <MessengerUnreadBadge compact/> : null}</Link>)}</nav><div className="sidebar-note"><span className="status-dot"/> Night Iris 0.9 beta<br/><small>API-first · structured knowledge + realtime</small></div></aside>;
}
