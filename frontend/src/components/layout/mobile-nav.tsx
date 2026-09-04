"use client";

import Link from "next/link";
import { Compass, Home, MessageCircle, Plus, UserRound, UsersRound } from "lucide-react";
import { usePathname } from "next/navigation";
import { useAuth } from "@/providers/auth-provider";
import { MessengerUnreadBadge } from "@/components/messenger/unread-badge";

export function MobileNav() {
  const path = usePathname();
  const { user } = useAuth();
  const items = user ? [
    ["/", "Лента", Home], ["/discover", "Открыть", Compass], ["/new", "Создать", Plus], ["/messages", "Чаты", MessageCircle], ["/profile", "Профиль", UserRound],
  ] as const : [["/", "Лента", Home], ["/discover", "Открыть", Compass], ["/communities", "Группы", UsersRound], ["/login", "Войти", UserRound]] as const;
  return <nav className="mobile-nav">{items.map(([href,label,Icon]) => <Link href={href} key={href} className={`mobile-nav-item ${path === href ? "mobile-nav-active" : ""}`}><span className="mobile-nav-icon-wrap"><Icon size={20}/>{href === "/messages" ? <MessengerUnreadBadge compact/> : null}</span><span>{label}</span></Link>)}</nav>;
}
