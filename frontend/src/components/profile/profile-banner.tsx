import type { User } from "@/lib/types";

export function ProfileBanner({ user }: { user: Pick<User, "banner" | "identity"> }) {
  const accent = user.identity?.accent ?? "emerald";
  return (
    <div
      className={`profile-banner identity-accent-${accent}`}
      style={user.banner?.url ? { backgroundImage: `linear-gradient(180deg, transparent, rgba(5,10,9,.35)), url(${user.banner.url})` } : undefined}
    >
      {!user.banner?.url ? <div className="profile-rings" /> : null}
    </div>
  );
}
