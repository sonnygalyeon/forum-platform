export function LoadingBlock({ label = "Загрузка…" }: { label?: string }) { return <div className="loading-block"><span className="spinner"/>{label}</div>; }
