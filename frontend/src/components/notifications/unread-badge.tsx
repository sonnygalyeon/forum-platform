"use client";

import { useQuery } from "@tanstack/react-query";
import { clientApi } from "@/lib/client-api";
import { useAuth } from "@/providers/auth-provider";

export function NotificationUnreadBadge({ compact = false }: { compact?: boolean }) {
  const { user } = useAuth();
  const query = useQuery({
    queryKey: ["notification-unread"],
    queryFn: () => clientApi<{ unread_count: number }>("/notifications/center/unread-count/"),
    enabled: Boolean(user),
    refetchInterval: 10000,
    refetchOnWindowFocus: true,
  });
  const count = query.data?.unread_count ?? 0;
  if (!count) return null;
  return <span className={`messenger-global-unread ${compact ? "compact" : ""}`}>{count > 99 ? "99+" : count}</span>;
}
