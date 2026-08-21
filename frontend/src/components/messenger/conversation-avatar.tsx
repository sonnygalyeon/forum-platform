import { UsersRound } from "lucide-react";
import type { MessengerConversation, User } from "@/lib/types";
import { UserAvatar } from "@/components/profile/user-avatar";

export function ConversationAvatar({ conversation, me, size = "md" }: { conversation: MessengerConversation; me: User | null; size?: "sm"|"md"|"lg" }) {
  if (conversation.kind === "group") return <span className={`messenger-group-avatar messenger-group-avatar-${size}`}><UsersRound size={size === "lg" ? 24 : 18}/></span>;
  const other = conversation.members.find(member => member.user.id !== me?.id)?.user;
  return other ? <UserAvatar user={other} size={size === "lg" ? "lg" : size === "sm" ? "sm" : "md"}/> : <span className="messenger-group-avatar"><UsersRound size={18}/></span>;
}
