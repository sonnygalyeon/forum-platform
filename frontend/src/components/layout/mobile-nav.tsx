"use client";

import Link from "next/link";
import { Bell, Home, Plus, Search, UserRound, UsersRound } from "lucide-react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";

export function MobileNav() {
  const path = usePathname();
  const { user } = useAuth();
  const items = user ? [
    ["/", "Лента", Home], ["/search", "Поиск", Search], ["/new", "Создать", Plus], ["/notifications", "События", Bell], ["/profile", "Профиль", UserRound],
  ] as const : [["/", "Лента", Home], ["/search", "Поиск", Search], ["/communities", "Группы", UsersRound], ["/login", "Войти", UserRound]] as const;
  return <nav className="mobile-nav">{items.map(([href,label,Icon]) => <Link href={href} key={href} className={`mobile-nav-item ${path === href ? "mobile-nav-active" : ""}`}><Icon size={20}/><span>{label}</span></Link>)}</nav>;
}
