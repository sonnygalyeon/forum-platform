import Link from "next/link";
import { CheckCircle2, MessageSquareReply } from "lucide-react";
import type { Comment } from "@/lib/types";

function excerpt(comment: Comment) {
  return comment.content.map(block => block.type === "code" ? block.code : block.text).join(" ").replace(/\s+/g," ").trim().slice(0,240);
}

export function AnswerCard({ answer }: { answer: Comment }) {
  const publication = answer.publication;
  return <article className={`answer-card ${answer.is_accepted?"answer-card-accepted":""}`}><div className="answer-card-score"><strong>{answer.score}</strong><span>голосов</span></div><div><div className="meta-row">{answer.is_accepted?<span className="status-chip"><CheckCircle2 size={11}/> принят</span>:<span><MessageSquareReply size={11}/> ответ</span>}<time>{new Date(answer.created_at).toLocaleDateString("ru-RU")}</time></div><Link className="answer-card-title" href={publication?`/publications/${publication.id}`:`/publications/${answer.publication_id}`}>{publication?.title||"Открыть обсуждение"}</Link><p>{excerpt(answer)||"Ответ без текстового превью"}</p></div></article>;
}
