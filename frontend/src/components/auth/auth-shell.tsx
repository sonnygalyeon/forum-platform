import Link from "next/link";
import { NightIrisMark } from "@/components/brand/night-iris-mark";
import { ThemeToggle } from "@/components/layout/theme-toggle";

export function AuthShell({ title, subtitle, children, footer }: {title:string; subtitle:string; children:React.ReactNode; footer:React.ReactNode}) {
  return <main className="auth-page"><div className="auth-top"><Link href="/"><NightIrisMark/></Link><ThemeToggle/></div><section className="auth-card enter-soft"><div className="auth-orbit"/><div className="eyebrow">NIGHT IRIS / ACCOUNT</div><h1>{title}</h1><p className="auth-subtitle">{subtitle}</p>{children}<div className="auth-footer">{footer}</div></section></main>;
}
