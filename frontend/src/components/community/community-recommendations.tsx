"use client";

import Link from "next/link";
import { BellPlus, Sparkles, UsersRound } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { clientApi } from "@/lib/client-api";
import type { CommunityRecommendation, Page } from "@/lib/types";

export function CommunityRecommendations(){
  const qc=useQueryClient();
  const recommendations=useQuery({
    queryKey:["community-recommendations"],
    queryFn:()=>clientApi<Page<CommunityRecommendation>>("/community-recommendations/?page_size=6"),
  });
  const subscribe=useMutation({
    mutationFn:(communityId:string)=>clientApi("/communities/"+communityId+"/subscription/",{method:"PUT"}),
    onSuccess:()=>{
      qc.invalidateQueries({queryKey:["community-recommendations"]});
      qc.invalidateQueries({queryKey:["communities"]});
      qc.invalidateQueries({queryKey:["home-feed"]});
    },
  });

  if(recommendations.isLoading||!recommendations.data?.results.length)return null;

  return <section className="section-block">
    <div className="section-heading">
      <h2><Sparkles size={18}/>Сообщества для вас</h2>
      <span>по вашим связям и интересам</span>
    </div>
    <div className="community-recommendation-grid">
      {recommendations.data.results.map(item=><article className="community-recommendation-card" key={item.community.id}>
        <Link href={"/communities/"+item.community.id} className="community-recommendation-main">
          <div className="community-card-icon"><UsersRound size={19}/></div>
          <div>
            <strong>{item.community.name}</strong>
            <span>/{item.community.slug}</span>
            <p>{item.community.description||"Описание пока не заполнено."}</p>
          </div>
        </Link>
        <div className="community-recommendation-reasons">
          {item.recommendation_reasons.map(reason=><span key={reason.code}>{reason.label}</span>)}
        </div>
        <footer>
          <span>{item.community.subscriber_count} подписчиков</span>
          <button
            className="primary-button compact-button"
            disabled={subscribe.isPending&&subscribe.variables===item.community.id}
            onClick={()=>subscribe.mutate(item.community.id)}
          ><BellPlus size={13}/>Подписаться</button>
        </footer>
      </article>)}
    </div>
  </section>;
}
