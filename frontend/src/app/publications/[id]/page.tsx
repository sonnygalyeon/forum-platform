"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Bookmark, BookmarkCheck, Edit3, History, MessageSquareText } from "lucide-react";
import { AppShell } from "@/components/layout/app-shell";
import { ContentBlocks } from "@/components/content/content-blocks";
import { CommentItem } from "@/components/discussion/comment-item";
import { CommentComposer } from "@/components/discussion/comment-composer";
import { UserAvatar } from "@/components/profile/user-avatar";
import { ReportButton } from "@/components/trust/report-button";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { Comment, CommentBlock, CursorPage, Publication } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

type BookmarkState = { bookmarked: boolean };

export default function PublicationPage() {
  const params = useParams<{id:string}>();
  const id = params.id;
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const publication = useQuery({ queryKey:["publication",id], queryFn:()=>clientApi<Publication>(`/publications/${id}/`) });
  const comments = useQuery({ queryKey:["comments",id], queryFn:()=>clientApi<CursorPage<Comment>>(`/publications/${id}/comments/`) });
  const bookmark = useQuery({ queryKey:["bookmark",id], queryFn:()=>clientApi<BookmarkState>(`/publications/${id}/bookmark/`), enabled:Boolean(user) });
  const create = useMutation({ mutationFn:(content:CommentBlock[])=>clientApi<Comment>(`/publications/${id}/comments/`,{method:"POST",body:JSON.stringify({content})}), onSuccess:()=>queryClient.invalidateQueries({queryKey:["comments",id]}) });
  const toggleBookmark = useMutation({
    mutationFn: async () => {
      const bookmarked = bookmark.data?.bookmarked ?? false;
      await clientApi(`/publications/${id}/bookmark/`, { method: bookmarked ? "DELETE" : "PUT" });
      return !bookmarked;
    },
    onSuccess: (bookmarked) => {
      queryClient.setQueryData<BookmarkState>(["bookmark",id], { bookmarked });
      void queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
    },
  });
  if (publication.isLoading) return <AppShell><LoadingBlock/></AppShell>;
  if (publication.isError || !publication.data) return <AppShell><div className="error-panel">Публикация не найдена или скрыта.</div></AppShell>;
  const p = publication.data;
  return <AppShell>
    <article className="publication-detail">
      <div className="publication-author-line"><Link href={`/users/${p.author.id}`} className="author-link"><UserAvatar user={p.author} size="sm"/><span><strong>@{p.author.nickname}</strong><small>{new Date(p.created_at).toLocaleString("ru-RU")}{p.is_edited?` · изменено · rev.${p.revision}`:""}</small></span></Link><div className="publication-tools">{user?<button type="button" className="secondary-button compact-button" disabled={toggleBookmark.isPending} onClick={()=>toggleBookmark.mutate()}>{bookmark.data?.bookmarked?<BookmarkCheck size={14}/>:<Bookmark size={14}/>} {bookmark.data?.bookmarked?"Сохранено":"Сохранить"}</button>:null}{p.can_edit?<Link href={`/publications/${p.id}/edit`} className="secondary-button compact-button"><Edit3 size={14}/> Редактировать</Link>:null}{!p.can_edit ? <ReportButton targetType="publication" targetId={p.id}/> : null}<Link href={`/publications/${p.id}/revisions`} className="icon-button" aria-label="История"><History size={16}/></Link></div></div>
      <div className="meta-row"><span className="status-chip">{p.type === "topic" ? "Вопрос" : p.type === "article" ? "Статья" : "Пост"}</span>{p.community?<Link href={`/communities/${p.community.id}`}>/{p.community.slug}</Link>:null}</div>
      {p.title?<h1>{p.title}</h1>:null}
      <div className="tags">{p.tags.map(t=><span className="tag" key={t.id}>{t.name}</span>)}</div>
      <ContentBlocks blocks={p.content} media={p.media}/>
    </article>
    <section className="discussion-section">
      <div className="section-heading"><h2><MessageSquareText size={19}/> {p.type === "topic" ? "Ответы" : "Обсуждение"}</h2><span>{comments.data?.results.length ?? 0} на странице</span></div>
      {comments.isLoading?<LoadingBlock/>:comments.data?.results.length?<div className="comment-list">{comments.data.results.map(c=><CommentItem key={c.id} comment={c} publicationId={id}/>)}</div>:<div className="inline-empty">{p.type === "topic" ? "Ответов пока нет." : "Комментариев пока нет."}</div>}
      {user?<div className="root-comment-form"><CommentComposer label={p.type === "topic" ? "Ваш ответ" : "Новый комментарий"} placeholder={p.type === "topic" ? "Предложите решение, добавьте код или пояснение…" : "Добавьте комментарий…"} busy={create.isPending} onSubmit={async blocks=>{await create.mutateAsync(blocks)}}/>{create.isError?<div className="form-error">{errorMessage(create.error)}</div>:null}</div>:<div className="login-hint"><Link href="/login">Войдите</Link>, чтобы участвовать в обсуждении.</div>}
    </section>
  </AppShell>;
}
