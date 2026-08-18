import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { AuthProvider } from "@/providers/auth-provider";

export const metadata: Metadata = {
  title: "Night Iris Forum",
  description: "Техническое сообщество для глубоких обсуждений.",
  icons: { icon: "/night-iris-app-icon.png" },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="ru" suppressHydrationWarning><body><QueryProvider><AuthProvider>{children}</AuthProvider></QueryProvider></body></html>;
}
