import { MessengerExperience } from "@/components/messenger/messenger-experience";

export default async function ConversationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <MessengerExperience initialConversationId={id}/>;
}
