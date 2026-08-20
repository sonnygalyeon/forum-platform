"use client";

import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { PublicationEditorForm } from "@/components/editor/publication-editor-form";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { PenSquare } from "lucide-react";
import { useAuth } from "@/providers/auth-provider";

export default function NewPublicationPage() {
  const router = useRouter();
  const { user, loading } = useAuth();
  if (loading) return <AppShell><LoadingBlock/></AppShell>;
  if (!user) return <AppShell><EmptyState icon={PenSquare} title="Нужен аккаунт" text="Создавать публикации могут только зарегистрированные пользователи." action={{href:"/login",label:"Войти"}}/></AppShell>;
  return <AppShell><section className="page-head"><div><div className="eyebrow">СОЗДАНИЕ / STRUCTURED BLOCKS</div><h1>Новая публикация</h1><p>Текст, код, цитаты и медиа хранятся отдельными структурированными блоками. HTML в базе не сохраняется.</p></div></section><PublicationEditorForm mode="create" onSaved={(publication) => router.push(`/publications/${publication.id}`)}/></AppShell>;
}
