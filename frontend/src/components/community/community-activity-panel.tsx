"use client";

import Link from "next/link";
import { MessageCircle, PenLine, Sparkles, TrendingUp, UsersRound } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { UserAvatar } from "@/components/profile/user-avatar";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi } from "@/lib/client-api";
import type { CommunityActivityItem, CommunityActivitySummary, CommunityContributor, Page } from "@/lib/types";

const roleLabels:Record<string,string>={owner:"Владелец",moderator:"Модератор",editor:"Редактор",subscriber:"Подписчик"};

function relativeDate(value:string){
  const diff=Math.max(0,Date.now()-new Date(value).getTime());
  const minutes=Math.floor(diff/60000);
  if(minutes<1)return "только что";
  if(minutes<60)return minutes+" мин";
  const hours=Math.floor(minutes/60);
  if(hours<24)return hours+" ч";
  const days=Math.floor(hours/24);
  return days+" д";
}

export function CommunityActivityPanel({communityId}:{communityId:string}){
  const summary=useQuery({
    queryKey:["community-activity-summary",communityId],
    queryFn:()=>clientApi<CommunityActivitySummary>("/communities/"+communityId+"/activity/summary/"),
  });
  const contributors=useQuery({
    queryKey:["community-contributors",communityId],
    queryFn:()=>clientApi<Page<CommunityContributor>>("/communities/"+communityId+"/contributors/?page_size=6"),
  });
  const activity=useQuery({
    queryKey:["community-activity",communityId],
    queryFn:()=>clientApi<Page<CommunityActivityItem>>("/communities/"+communityId+"/activity/?page_size=12"),
  });

  if(summary.isLoading)return <LoadingBlock/>;

  return <section className="community-activity-shell">
    {summary.data?<>
      <div className="section-heading">
        <h2><TrendingUp size={18}/>Активность сообщества</h2>
        <span>последние 7 дней</span>
      </div>
      <div className="community-activity-metrics">
        <div><strong>{summary.data.publications_7d}</strong><span>публикаций</span></div>
        <div><strong>{summary.data.comments_7d}</strong><span>ответов и комментариев</span></div>
        <div><strong>{summary.data.active_contributors_7d}</strong><span>активных участников</span></div>
        <div><strong>+{summary.data.new_subscribers_7d}</strong><span>новых подписчиков</span></div>
      </div>
      {summary.data.top_tags.length?<div className="community-activity-tags">
        {summary.data.top_tags.map(tag=><Link key={tag.id} href={"/search?scope=publications&tag="+encodeURIComponent(tag.slug)}>#{tag.name}<span>{tag.publication_count}</span></Link>)}
      </div>:null}
    </>:null}

    <div className="community-activity-grid">
      <div className="community-activity-column">
        <div className="section-heading"><h3><UsersRound size={16}/>Активные участники</h3><span>30 дней</span></div>
        {contributors.isLoading?<LoadingBlock/>:contributors.data?.results.length?
          <div className="community-contributor-list">{contributors.data.results.map(item=>
            <Link href={"/users/"+item.user.id} key={item.user.id} className="community-contributor">
              <UserAvatar user={item.user} size="sm"/>
              <div><strong>@{item.user.nickname}{item.role?" · "+(roleLabels[item.role]??item.role):""}</strong><span>{item.publication_count} публ. · {item.comment_count} комм.{item.accepted_answer_count?" · "+item.accepted_answer_count+" принятых":""}</span></div>
              <b>{item.activity_score}</b>
            </Link>
          )}</div>:<div className="inline-empty">За последние 30 дней активных участников пока нет.</div>}
      </div>

      <div className="community-activity-column">
        <div className="section-heading"><h3><Sparkles size={16}/>Что происходит</h3><span>последнее</span></div>
        {activity.isLoading?<LoadingBlock/>:activity.data?.results.length?
          <div className="community-timeline">{activity.data.results.map(item=>
            <Link
              key={item.type+"-"+item.id}
              className="community-timeline-item"
              href={"/publications/"+item.publication.id+(item.comment?"#comment-"+item.comment.id:"")}
            >
              <span className="community-timeline-icon">{item.type==="publication"?<PenLine size={14}/>:<MessageCircle size={14}/>}</span>
              <div>
                <strong>@{item.actor.nickname} {item.type==="publication"?"опубликовал":"ответил"}</strong>
                <span>{item.comment?.excerpt||item.publication.title||"Публикация без заголовка"}</span>
              </div>
              <time>{relativeDate(item.created_at)}</time>
            </Link>
          )}</div>:<div className="inline-empty">Активности пока нет.</div>}
      </div>
    </div>
  </section>;
}
