export function NightIrisMark({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`night-brand ${compact ? "night-brand-compact" : ""}`} aria-label="Night Iris Forum">
      <span className="brand-mark" aria-hidden="true">
        <svg viewBox="0 0 64 64" fill="none">
          <path d="M8 32c7-10 15-15 24-15s17 5 24 15c-7 10-15 15-24 15S15 42 8 32Z" stroke="currentColor" strokeWidth="2.4"/>
          <circle cx="32" cy="32" r="8" stroke="currentColor" strokeWidth="2.4"/>
          <circle cx="32" cy="32" r="2.5" fill="currentColor"/>
          <path d="M32 7v6M32 51v6M12 15l4 4M48 45l4 4M52 15l-4 4M16 45l-4 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
      </span>
      <span className="brand-copy"><strong>NIGHT IRIS</strong><small>FORUM</small></span>
    </div>
  );
}
