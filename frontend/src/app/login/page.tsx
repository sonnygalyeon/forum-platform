"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AuthShell } from "@/components/auth/auth-shell";
import { errorMessage, ApiError } from "@/lib/client-api";
import { useAuth } from "@/providers/auth-provider";

export default function LoginPage() {
  const router = useRouter(); const { refresh } = useAuth();
  const [nickname,setNickname]=useState(""); const [password,setPassword]=useState(""); const [error,setError]=useState(""); const [busy,setBusy]=useState(false);
  async function submit(e:FormEvent){e.preventDefault();setBusy(true);setError("");try{const r=await fetch("/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({nickname,password})});const payload=await r.json().catch(()=>null);if(!r.ok) throw new ApiError(r.status,payload);await refresh();router.replace("/");}catch(err){setError(errorMessage(err));}finally{setBusy(false);}}
  return <AuthShell title="Вход" subtitle="Вернитесь к своим подпискам, ответам и обсуждениям." footer={<>Нет аккаунта? <Link href="/register">Зарегистрироваться</Link></>}><form className="form-stack" onSubmit={submit}><label>Никнейм<input value={nickname} onChange={e=>setNickname(e.target.value)} autoComplete="username" required/></label><label>Пароль<input type="password" value={password} onChange={e=>setPassword(e.target.value)} autoComplete="current-password" required/></label>{error?<div className="form-error">{error}</div>:null}<button className="primary-button wide-button" disabled={busy}>{busy?"Входим…":"Войти"}</button></form></AuthShell>;
}
