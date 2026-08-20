import { Download, FileText } from "lucide-react";
import type { ContentBlock, PublicationMedia } from "@/lib/types";

function humanBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB", "TB"];
  let value = bytes / 1024;
  let index = 0;
  while (value >= 1024 && index < units.length - 1) {
    value /= 1024;
    index += 1;
  }
  return `${value.toFixed(value >= 10 ? 1 : 2)} ${units[index]}`;
}

export function ContentBlocks({ blocks, media = [] }: { blocks?: ContentBlock[]; media?: PublicationMedia[] }) {
  if (!blocks?.length) return null;
  const mediaById = new Map(media.map((item) => [item.asset_id, item]));

  return (
    <div className="rich-content">
      {blocks.map((block, index) => {
        if (block.type === "paragraph") return <p key={index}>{block.text}</p>;
        if (block.type === "quote") return <blockquote key={index}>{block.text}</blockquote>;
        if (block.type === "heading") {
          const Tag = (`h${block.level}`) as "h1" | "h2" | "h3" | "h4";
          return <Tag key={index}>{block.text}</Tag>;
        }
        if (block.type === "code") return <pre className="code-block" key={index}><div className="code-language">{block.language || "code"}</div><code>{block.code}</code></pre>;

        const asset = mediaById.get(block.asset_id);
        if (block.type === "image") {
          return <figure className="content-media" key={index}>{asset?.url ? <img src={asset.url} alt={block.caption || asset.name}/>:<div className="media-unavailable">Изображение недоступно</div>}{block.caption?<figcaption>{block.caption}</figcaption>:null}</figure>;
        }
        if (block.type === "video") {
          return <figure className="content-media" key={index}>{asset?.url ? <video controls preload="metadata" src={asset.url}/>:<div className="media-unavailable">Видео недоступно</div>}{block.caption?<figcaption>{block.caption}</figcaption>:null}</figure>;
        }
        return <a className="attachment-card" key={index} href={asset?.url ?? undefined} target="_blank" rel="noreferrer"><span className="attachment-icon"><FileText size={20}/></span><span><strong>{block.caption || asset?.name || "Вложение"}</strong><small>{asset ? `${asset.content_type} · ${humanBytes(asset.size_bytes)}` : "Файл"}</small></span><Download size={17}/></a>;
      })}
    </div>
  );
}
