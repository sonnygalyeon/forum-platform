"use client";

import { useQuery } from "@tanstack/react-query";
import { clientApi } from "@/lib/client-api";
import { useAuth } from "@/providers/auth-provider";

export function MessengerUnreadBadge({ compact = false }: { compact?: boolean }) {
  const { user } = useAuth();
  const query = useQuery({
    queryKey: ["messenger-unread"],
    queryFn: () => clientApi<{ unread_count: number }>("/messenger/unread-count/"),
    enabled: Boolean(user),
    refetchInterval: 30000,
  });
  const count = query.data?.unread_count ?? 0;
  if (!count) return null;
  return <span className={`messenger-global-unread ${compact ? "compact" : ""}`}>{count > 99 ? "99+" : count}</span>;
}
