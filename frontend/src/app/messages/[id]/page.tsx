import { MessengerShell } from "@/components/messenger/messenger-shell";
export default async function ConversationPage({params}:{params:Promise<{id:string}>}){const {id}=await params;return <MessengerShell initialConversationId={id}/>}
