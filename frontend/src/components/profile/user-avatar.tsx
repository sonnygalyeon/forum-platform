import type { User } from "@/lib/types";

export function UserAvatar({
  user,
  size = "md",
  className = "",
}: {
  user: Pick<User, "nickname" | "avatar" | "identity">;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
}) {
  const initials = user.nickname.slice(0, 2).toUpperCase();
  const frame = user.identity?.equipped_frame?.style_token ?? "none";
  const accent = user.identity?.accent ?? "emerald";
  return (
    <span className={`user-avatar user-avatar-${size} identity-frame identity-frame-${frame} identity-accent-${accent} ${className}`.trim()}>
      <span className={`avatar avatar-${size} avatar-face`}>
        {user.avatar?.url ? <img src={user.avatar.url} alt={`Аватар @${user.nickname}`} /> : initials}
      </span>
    </span>
  );
}
