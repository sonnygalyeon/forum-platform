import type { ContentBlock } from "@/lib/types";

export function ContentBlocks({ blocks }: { blocks?: ContentBlock[] }) {
  if (!blocks?.length) return null;

  return (
    <div className="rich-content">
      {blocks.map((block, index) => {
        if (block.type === "paragraph") {
          return <p key={index}>{block.text}</p>;
        }

        if (block.type === "quote") {
          return <blockquote key={index}>{block.text}</blockquote>;
        }

        if (block.type === "heading") {
          const Tag = (`h${block.level}`) as "h1" | "h2" | "h3" | "h4";
          return <Tag key={index}>{block.text}</Tag>;
        }

        if (block.type === "code") {
          return (
            <pre className="code-block" key={index}>
              <code>{block.code}</code>
            </pre>
          );
        }

        if (
          block.type === "image" ||
          block.type === "video" ||
          block.type === "attachment"
        ) {
          return (
            <div className="media-placeholder" key={index}>
              Медиа-вложение: {block.caption?.trim() || block.type}
            </div>
          );
        }

        return null;
      })}
    </div>
  );
}
