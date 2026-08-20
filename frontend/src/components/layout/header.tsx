"use client";

import Link from "next/link";
import { Bell, LogIn, Plus, Search, ShieldCheck, UserRound } from "lucide-react";
import { NightIrisMark } from "@/components/brand/night-iris-mark";
import { UserAvatar } from "@/components/profile/user-avatar";
import { ThemeToggle } from "./theme-toggle";
import { GlobalSearch } from "@/components/search/global-search";
import { useAuth } from "@/providers/auth-provider";

export function Header() {
  const { user, loading } = useAuth();
  return (
    <header className="site-header">
      <div className="header-inner">
        <Link href="/" className="brand-link"><NightIrisMark compact /></Link>
        <nav className="desktop-topnav" aria-label="Основная навигация">
          <Link href="/">Лента</Link>
          <Link href="/communities">Сообщества</Link>
          {user?.is_staff ? <Link href="/admin"><ShieldCheck size={14}/> Админка</Link> : null}
        </nav>
        <div className="header-search-slot"><GlobalSearch /></div>
        <div className="header-actions">
          <Link href="/search" className="icon-button mobile-search-trigger" aria-label="Поиск"><Search size={17}/></Link>
          <ThemeToggle />
          {!loading && user ? (
            <>
              <Link href="/new" className="primary-button compact-button"><Plus size={15}/> Создать</Link>
              <Link href="/notifications" className="icon-button" aria-label="Уведомления"><Bell size={17}/></Link>
              <Link href="/profile" aria-label="Профиль"><UserAvatar user={user} size="sm"/></Link>
            </>
          ) : !loading ? (
            <>
              <Link href="/login" className="secondary-button compact-button"><LogIn size={15}/> Войти</Link>
              <Link href="/register" className="primary-button compact-button"><UserRound size={15}/> Регистрация</Link>
            </>
          ) : null}
        </div>
      </div>
    </header>
  );
}
