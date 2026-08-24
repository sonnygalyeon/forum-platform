import { Header } from "./header";
import { Sidebar } from "./sidebar";
import { MobileNav } from "./mobile-nav";

export function AppShell({ children, wide = false }: { children: React.ReactNode; wide?: boolean }) {
  return <><Header/><div className="shell"><Sidebar/><main className={`main-content enter-soft ${wide ? "main-content-wide" : ""}`}>{children}</main></div><MobileNav/></>;
}
