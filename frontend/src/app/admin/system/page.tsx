"use client";
import { useQuery } from "@tanstack/react-query";
import { Database,HardDrive,RadioTower,RefreshCw } from "lucide-react";
import { StatusBadge } from "@/components/admin/admin-ui";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi,errorMessage } from "@/lib/client-api";
type Ready={status:string;checks:Record<string,string>};
const icons:Record<string,React.ReactNode>={database:<Database/>,redis:<RadioTower/>,object_storage:<HardDrive/>};
export default function AdminSystemPage(){const q=useQuery({queryKey:["admin","ready"],queryFn:()=>clientApi<Ready>("/ready/"),refetchInterval:15000,retry:false});return <><div className="admin-page-head"><div><div className="eyebrow">ИНФРАСТРУКТУРА</div><h1>Состояние системы</h1><p>Readiness backend-проверок. Страница автоматически обновляется каждые 15 секунд.</p></div><button className="secondary-button compact-button" onClick={()=>q.refetch()}><RefreshCw size={14}/> Проверить</button></div>{q.isLoading?<LoadingBlock/>:q.error?<div className="error-panel">{errorMessage(q.error)}</div>:<><div className="admin-system-summary"><div><span>Общий статус</span><strong>{q.data?.status}</strong></div><StatusBadge value={q.data?.status??"unknown"}/></div><div className="admin-system-grid">{Object.entries(q.data?.checks??{}).map(([name,value])=><article key={name}><div className="system-icon">{icons[name]??<RadioTower/>}</div><div><strong>{name.replace("_"," ")}</strong><span>readiness check</span></div><StatusBadge value={value}/></article>)}</div></>}</>}
