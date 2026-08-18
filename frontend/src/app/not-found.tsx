import Link from "next/link";
import { NightIrisMark } from "@/components/brand/night-iris-mark";
export default function NotFound(){return <main className="not-found"><NightIrisMark/><h1>404</h1><p>Такой страницы в Night Iris нет.</p><Link href="/" className="primary-button">На главную</Link></main>}
