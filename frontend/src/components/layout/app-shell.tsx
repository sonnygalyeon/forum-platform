import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { MobileNav } from "./mobile-nav";

export function AppShell({ children }: { children: React.ReactNode }) {
  return <><Header/><div className="shell"><Sidebar/><main className="main-content enter-soft">{children}</main></div><MobileNav/></>;
}
