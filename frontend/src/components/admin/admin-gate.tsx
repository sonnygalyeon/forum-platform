"use client";

import Link from "next/link";
import { LockKeyhole } from "lucide-react";
import { LoadingBlock } from "@/components/ui/loading";
import { useAuth } from "@/providers/auth-provider";

export function AdminGate({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="admin-gate-state"><LoadingBlock /></div>;
  if (!user) return <div className="admin-gate-state"><LockKeyhole size={30}/><h1>Требуется авторизация</h1><p>Войдите под учётной записью сотрудника.</p><Link className="primary-button" href="/login">Войти</Link></div>;
  if (!user.is_staff) return <div className="admin-gate-state"><LockKeyhole size={30}/><h1>Нет доступа</h1><p>Этот раздел доступен только сотрудникам Night Iris.</p><Link className="secondary-button" href="/">Вернуться на форум</Link></div>;
  return <>{children}</>;
}
