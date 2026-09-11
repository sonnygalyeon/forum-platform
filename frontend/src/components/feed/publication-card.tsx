import Link from "next/link";
import { Heart, MessageSquareText, Sparkles } from "lucide-react";

import { UserAvatar } from "@/components/profile/user-avatar";
import { FeedFeedbackControl } from "@/components/feed/feed-feedback-control";
import type { Publication } from "@/lib/types";

const labels = { post: "Пост", article: "Статья", topic: "Вопрос" } as const;

type FeedAwarePublication = Publication & {
  feed_score?: number;
  feed_base_score?: number;
  reaction_total?: number;
  is_exploration?: boolean;
  recommendation_reasons?: Array<{ code: string; label: string }>;
  quality_adjustments?: Array<{ code: string; label: string; delta: number }>;
};

export function PublicationCard({ publication, feedFeedback = false }: { publication: Publication; feedFeedback?: boolean }) {
  const feedPublication = publication as FeedAwarePublication;
  const title = publication.title || publication.excerpt.slice(0, 90) || "Публикация";
  const reasons = feedPublication.recommendation_reasons ?? [];

  return (
    <article className="topic-card">
      <div className="card-main">
        {reasons.length ? (
          <div className="meta-row" aria-label="Почему публикация в ленте">
            <Sparkles size={13} aria-hidden="true" />
            {reasons.slice(0, 2).map((reason) => (
              <span className="status-chip" key={reason.code}>{reason.label}</span>
            ))}
          </div>
        ) : null}

        {feedFeedback ? <div className="feed-card-topline"><FeedFeedbackControl publicationId={publication.id}/></div> : null}

        <div className="meta-row author-meta">
          <Link href={`/users/${publication.author.id}`} className="author-link">
            <UserAvatar user={publication.author} size="xs" />
            <span>@{publication.author.nickname}</span>
          </Link>
          <span className="status-chip">{labels[publication.type]}</span>
          <time>{new Date(publication.created_at).toLocaleDateString("ru-RU")}</time>
          {publication.community ? (
            <>
              <span>•</span>
              <Link href={`/communities/${publication.community.id}`}>/{publication.community.slug}</Link>
            </>
          ) : null}
        </div>

        <Link href={`/publications/${publication.id}`} className="topic-title">{title}</Link>
        {publication.excerpt ? <p className="excerpt">{publication.excerpt}</p> : null}

        <div className="card-footer">
          <div className="tags">
            {publication.tags.map((tag) => (
              <Link
                className="tag"
                href={`/search?scope=publications&tag=${encodeURIComponent(tag.slug)}`}
                key={tag.id}
              >
                {tag.name}
              </Link>
            ))}
          </div>
          <div className="feed-engagement-inline">{feedPublication.reaction_total ? <span className="muted-inline"><Heart size={13}/> {feedPublication.reaction_total}</span> : null}<span className="muted-inline"><MessageSquareText size={13} /> {publication.comment_count ?? 0}</span></div>
        </div>
      </div>
      <div className="iris-ornament"><span /><span /><span /></div>
    </article>
  );
}
