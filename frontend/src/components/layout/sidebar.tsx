"use client";

import Link from "next/link";
import { Bell, Home, MessageCircle, PlusSquare, Search, ShieldCheck, UsersRound, UserRound } from "lucide-react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { MessengerUnreadBadge } from "@/components/messenger/unread-badge";

const publicItems = [
  { href: "/", label: "Лента", icon: Home },
  { href: "/search", label: "Поиск", icon: Search },
  { href: "/communities", label: "Сообщества", icon: UsersRound },
];

export function Sidebar() {
  const pathname = usePathname(); const { user } = useAuth();
  const items = user ? [...publicItems,
    { href: "/new", label: "Создать", icon: PlusSquare },
    { href: "/messages", label: "Сообщения", icon: MessageCircle },
    { href: "/notifications", label: "Уведомления", icon: Bell },
    { href: "/profile", label: "Профиль", icon: UserRound },
    ...(user.is_staff ? [{ href: "/admin", label: "Админка", icon: ShieldCheck }] : []),
  ] : publicItems;
  return <aside className="sidebar"><div className="eyebrow">НАВИГАЦИЯ</div><nav>{items.map(({href,label,icon:Icon}) => <Link key={href} href={href} className={`nav-item ${pathname === href || (href!=="/"&&pathname.startsWith(href)) ? "nav-item-active" : ""}`}><Icon size={17}/>{label}{href === "/messages" ? <MessengerUnreadBadge compact/> : null}</Link>)}</nav><div className="sidebar-note"><span className="status-dot"/> Night Iris 0.8.10<br/><small>API-first · structured content</small></div></aside>;
}
