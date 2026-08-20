import Link from "next/link";
import { Hash, UsersRound } from "lucide-react";
import { PublicationCard } from "@/components/feed/publication-card";
import { SocialUserList } from "@/components/profile/social-user-list";
import type { Community, Publication, SearchTag, User } from "@/lib/types";

export function SearchPublications({ items }: { items: Publication[] }) {
  if (!items.length) return <div className="inline-empty">Публикаций не найдено.</div>;
  return <div className="feed-list">{items.map((publication) => <PublicationCard key={publication.id} publication={publication} />)}</div>;
}

export function SearchUsers({ items }: { items: User[] }) {
  return <SocialUserList edges={items.map((user) => ({ user }))} empty="Пользователей не найдено." />;
}

export function SearchCommunities({ items }: { items: Community[] }) {
  if (!items.length) return <div className="inline-empty">Сообществ не найдено.</div>;
  return (
    <div className="community-grid search-community-grid">
      {items.map((community) => (
        <Link href={`/communities/${community.id}`} className="community-card" key={community.id}>
          <div className="community-card-icon"><UsersRound size={20} /></div>
          <div>
            <h2>{community.name}</h2>
            <span>/{community.slug}</span>
            <p>{community.description || "Описание пока не заполнено."}</p>
          </div>
          <footer>
            <span>{community.subscriber_count} подписчиков</span>
            <span>{community.publication_count} публикаций</span>
          </footer>
        </Link>
      ))}
    </div>
  );
}

export function SearchTags({ items }: { items: SearchTag[] }) {
  if (!items.length) return <div className="inline-empty">Тегов не найдено.</div>;
  return (
    <div className="tag-cloud">
      {items.map((tag) => (
        <Link href={`/search?scope=publications&tag=${encodeURIComponent(tag.slug)}`} className="tag-discovery-card" key={tag.id}>
          <Hash size={14} />
          <span>{tag.name}</span>
          <small>{tag.publication_count}</small>
        </Link>
      ))}
    </div>
  );
}
