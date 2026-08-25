import { UsersRound } from "lucide-react";
import type { MessengerConversation, User } from "@/lib/types";
import { UserAvatar } from "@/components/profile/user-avatar";

export function ConversationAvatar({ conversation, me, size = "md" }: { conversation: MessengerConversation; me: User | null; size?: "sm"|"md"|"lg" }) {
  if (conversation.kind === "group") {
    if (conversation.avatar?.url) {
      return <span className={`messenger-group-avatar messenger-group-avatar-${size} has-image`}><img src={conversation.avatar.url} alt={conversation.display_title}/></span>;
    }
    return <span className={`messenger-group-avatar messenger-group-avatar-${size}`}><UsersRound size={size === "lg" ? 24 : 18}/></span>;
  }
  const otherMember = conversation.members.find(member => member.user.id !== me?.id);
  if (!otherMember) return <span className="messenger-group-avatar"><UsersRound size={18}/></span>;
  return (
    <span className="conversation-avatar-presence">
      <UserAvatar user={otherMember.user} size={size === "lg" ? "lg" : size === "sm" ? "sm" : "md"}/>
      <span className={`conversation-online-dot ${otherMember.online ? "online" : ""}`} />
    </span>
  );
}
