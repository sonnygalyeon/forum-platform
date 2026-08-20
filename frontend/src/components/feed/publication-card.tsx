import Link from "next/link";
import { MessageSquareText } from "lucide-react";
import type { Publication } from "@/lib/types";
import { UserAvatar } from "@/components/profile/user-avatar";

const labels = { post: "Пост", article: "Статья", topic: "Вопрос" } as const;

export function PublicationCard({ publication }: { publication: Publication }) {
  const title = publication.title || publication.excerpt.slice(0, 90) || "Публикация";
  return (
    <article className="topic-card">
      <div className="card-main">
        <div className="meta-row author-meta">
          <Link href={`/users/${publication.author.id}`} className="author-link"><UserAvatar user={publication.author} size="xs"/><span>@{publication.author.nickname}</span></Link>
          <span className="status-chip">{labels[publication.type]}</span>
          <time>{new Date(publication.created_at).toLocaleDateString("ru-RU")}</time>
          {publication.community ? <><span>•</span><Link href={`/communities/${publication.community.id}`}>/{publication.community.slug}</Link></> : null}
        </div>
        <Link href={`/publications/${publication.id}`} className="topic-title">{title}</Link>
        {publication.excerpt ? <p className="excerpt">{publication.excerpt}</p> : null}
        <div className="card-footer"><div className="tags">{publication.tags.map(tag => <span className="tag" key={tag.id}>{tag.name}</span>)}</div><span className="muted-inline"><MessageSquareText size={13}/> {publication.comment_count ?? 0}</span></div>
      </div>
      <div className="iris-ornament"><span/><span/><span/></div>
    </article>
  );
}
