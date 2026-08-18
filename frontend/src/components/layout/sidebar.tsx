"use client";

import Link from "next/link";
import { Bell, Home, PlusSquare, ShieldCheck, UsersRound, UserRound } from "lucide-react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";

const publicItems = [
  { href: "/", label: "Лента", icon: Home },
  { href: "/communities", label: "Сообщества", icon: UsersRound },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const items = user ? [...publicItems,
    { href: "/new", label: "Создать", icon: PlusSquare },
    { href: "/notifications", label: "Уведомления", icon: Bell },
    { href: "/profile", label: "Профиль", icon: UserRound },
    ...(user.is_staff ? [{ href: "/admin", label: "Админка", icon: ShieldCheck }] : []),
  ] : publicItems;
  return <aside className="sidebar"><div className="eyebrow">НАВИГАЦИЯ</div><nav>{items.map(({href,label,icon:Icon}) => (
    <Link key={href} href={href} className={`nav-item ${pathname === href ? "nav-item-active" : ""}`}><Icon size={17}/>{label}</Link>
  ))}</nav><div className="sidebar-note"><span className="status-dot"/> Реальные данные API<br/><small>Демо-контент отключён</small></div></aside>;
}
