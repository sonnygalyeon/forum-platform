"use client";

import { useNotificationSocket } from "@/hooks/use-notification-socket";
import { useAuth } from "@/providers/auth-provider";

export function NotificationRealtimeSync() {
  const { user } = useAuth();
  useNotificationSocket(Boolean(user));
  return null;
}
