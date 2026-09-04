"use client";

import {
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import {
  Award,
  Check,
  Gauge,
  LockKeyhole,
  Palette,
  Save,
  Sparkles,
} from "lucide-react";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/app-shell";
import { IdentityBadges } from "@/components/profile/identity-badges";
import { UserAvatar } from "@/components/profile/user-avatar";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi, errorMessage } from "@/lib/client-api";
import type {
  IdentityBadge,
  IdentityFrame,
  MyIdentity,
  User,
} from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

const accents = [
  ["emerald", "Emerald", "Фирменный зелёный"],
  ["jade", "Jade", "Более спокойный нефритовый"],
  ["ice", "Ice", "Холодный технический голубой"],
  ["violet", "Violet", "Редкий фиолетовый акцент"],
] as const;

function pinnedIds(identity: MyIdentity) {
  return identity.owned_badges
    .filter(item => item.pinned)
    .sort((a, b) => a.pin_order - b.pin_order)
    .map(item => item.badge.id);
}

function IdentityEditor({
  user,
  identity,
  frames,
  badges,
  refresh,
}: {
  user: User;
  identity: MyIdentity;
  frames: IdentityFrame[];
  badges: IdentityBadge[];
  refresh: () => Promise<void>;
}) {
  const qc = useQueryClient();
  const [headline, setHeadline] = useState(identity.headline ?? "");
  const [accent, setAccent] =
    useState<MyIdentity["accent"]>(identity.accent);
  const [pins, setPins] = useState<string[]>(() => pinnedIds(identity));

  const afterMutation = async () => {
    await qc.invalidateQueries({ queryKey: ["my-identity"] });
    await refresh();
  };

  const saveProfile = useMutation({
    mutationFn: () =>
      clientApi<MyIdentity>("/identity/me/", {
        method: "PATCH",
        body: JSON.stringify({ headline, accent }),
      }),
    onSuccess: afterMutation,
  });

  const equip = useMutation({
    mutationFn: (frameId: string | null) =>
      clientApi<MyIdentity>("/identity/me/frame/", {
        method: "PUT",
        body: JSON.stringify({ frame_id: frameId }),
      }),
    onSuccess: afterMutation,
  });

  const savePins = useMutation({
    mutationFn: () =>
      clientApi<MyIdentity>("/identity/me/badges/", {
        method: "PUT",
        body: JSON.stringify({ badge_ids: pins }),
      }),
    onSuccess: afterMutation,
  });

  const ownedFrameIds = useMemo(
    () => new Set(identity.owned_frames.map(item => item.frame.id)),
    [identity.owned_frames],
  );

  const ownedBadgeMap = useMemo(
    () =>
      new Map(
        identity.owned_badges.map(item => [item.badge.id, item]),
      ),
    [identity.owned_badges],
  );

  const previewUser: User = {
    ...user,
    identity: {
      ...user.identity,
      ...identity,
    },
  };

  const error =
    saveProfile.error ||
    equip.error ||
    savePins.error;

  function togglePin(id: string) {
    setPins(current =>
      current.includes(id)
        ? current.filter(item => item !== id)
        : current.length < 3
          ? [...current, id]
          : current,
    );
  }

  return (
    <AppShell>
      <section className="page-head">
        <div>
          <div className="eyebrow">ПРОФИЛЬ / IDENTITY</div>
          <h1>Стиль и достижения</h1>
          <p>
            Рамки и бейджи выдаются системой за активность. Никакого
            пользовательского CSS — только безопасные дизайн-токены Night Iris.
          </p>
        </div>
      </section>

      <section className="identity-hero identity-panel">
        <div className="identity-preview">
          <UserAvatar user={previewUser} size="xl" />
          <div>
            <strong>@{user.nickname}</strong>
            <span>
              {headline ||
                "Короткая строка под именем пока не задана."}
            </span>
            <IdentityBadges badges={identity.badges} />
          </div>
        </div>

        <div className="identity-metrics">
          <div>
            <Gauge size={16} />
            <strong>{identity.reputation}</strong>
            <span>репутация</span>
          </div>
          <div>
            <Sparkles size={16} />
            <strong>{identity.level}</strong>
            <span>уровень</span>
          </div>
          <div>
            <Award size={16} />
            <strong>{identity.owned_badges.length}</strong>
            <span>достижений</span>
          </div>
        </div>
      </section>

      <section className="settings-card">
        <h2>Профильный акцент</h2>

        <label>
          Строка под именем
          <input
            maxLength={90}
            value={headline}
            onChange={event =>
              setHeadline(event.target.value)
            }
            placeholder="Например: Backend · embedded · RF"
          />
        </label>

        <div className="accent-grid">
          {accents.map(([value, name, description]) => (
            <button
              type="button"
              key={value}
              className={`accent-choice identity-accent-${value} ${
                accent === value ? "selected" : ""
              }`}
              onClick={() => setAccent(value)}
            >
              <span className="accent-swatch" />
              <strong>{name}</strong>
              <small>{description}</small>
              {accent === value ? <Check size={14} /> : null}
            </button>
          ))}
        </div>

        <div className="editor-actions">
          <button
            className="primary-button"
            disabled={saveProfile.isPending}
            onClick={() => saveProfile.mutate()}
          >
            <Save size={14} />
            {saveProfile.isPending
              ? "Сохраняем…"
              : "Сохранить стиль"}
          </button>
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-title-row">
          <div>
            <h2>Рамки аватара</h2>
            <p>
              Открываются автоматически, когда выполняется условие.
            </p>
          </div>
          <Palette size={18} />
        </div>

        <div className="frame-grid">
          {frames.map(frame => {
            const owned = ownedFrameIds.has(frame.id);
            const equipped =
              identity.equipped_frame?.id === frame.id;

            return (
              <article
                className={`frame-card ${
                  equipped ? "selected" : ""
                }`}
                key={frame.id}
              >
                <div className="frame-card-preview">
                  <UserAvatar
                    user={{
                      ...previewUser,
                      identity: {
                        ...previewUser.identity,
                        equipped_frame: frame,
                      },
                    }}
                    size="lg"
                  />
                </div>

                <div className="frame-card-copy">
                  <div>
                    <strong>{frame.name}</strong>
                    <span
                      className={`tier-chip tier-${frame.tier}`}
                    >
                      {frame.tier}
                    </span>
                  </div>
                  <p>{frame.description}</p>
                  <small>
                    {frame.unlock_type === "reputation"
                      ? `Нужно ${frame.unlock_value} репутации`
                      : frame.unlock_type === "badge"
                        ? `Нужен бейдж ${frame.required_badge_slug}`
                        : frame.unlock_type === "staff"
                          ? "Только команда форума"
                          : "Доступна всем"}
                  </small>
                </div>

                <button
                  disabled={!owned || equip.isPending}
                  className={
                    equipped
                      ? "secondary-button compact-button"
                      : "primary-button compact-button"
                  }
                  onClick={() => equip.mutate(frame.id)}
                >
                  {owned ? (
                    equipped ? (
                      "Выбрана"
                    ) : (
                      "Выбрать"
                    )
                  ) : (
                    <>
                      <LockKeyhole size={12} /> Закрыта
                    </>
                  )}
                </button>
              </article>
            );
          })}
        </div>
      </section>

      <section className="settings-card">
        <div className="settings-title-row">
          <div>
            <h2>Бейджи</h2>
            <p>
              Можно закрепить до трёх достижений в публичном профиле.
            </p>
          </div>
          <Award size={18} />
        </div>

        <div className="achievement-grid">
          {badges.map(badge => {
            const owned = ownedBadgeMap.get(badge.id);
            const pinned = pins.includes(badge.id);

            return (
              <button
                type="button"
                disabled={!owned}
                onClick={() => togglePin(badge.id)}
                className={`achievement-card ${
                  owned ? "owned" : "locked"
                } ${pinned ? "selected" : ""}`}
                key={badge.id}
              >
                <div className="achievement-top">
                  <span
                    className={`tier-chip tier-${badge.tier}`}
                  >
                    {badge.tier}
                  </span>
                  {pinned ? (
                    <Check size={14} />
                  ) : !owned ? (
                    <LockKeyhole size={13} />
                  ) : null}
                </div>

                <strong>{badge.name}</strong>
                <p>{badge.description}</p>
                <small>
                  {owned
                    ? `Получен ${new Date(
                        owned.awarded_at,
                      ).toLocaleDateString("ru-RU")}`
                    : "Ещё не получен"}
                </small>
              </button>
            );
          })}
        </div>

        <div className="editor-actions">
          <span className="form-help">
            Закреплено {pins.length}/3
          </span>
          <button
            className="primary-button"
            disabled={savePins.isPending}
            onClick={() => savePins.mutate()}
          >
            <Save size={14} />
            {savePins.isPending
              ? "Сохраняем…"
              : "Сохранить бейджи"}
          </button>
        </div>
      </section>

      {error ? (
        <div className="form-error">
          {errorMessage(error)}
        </div>
      ) : null}
    </AppShell>
  );
}

export default function IdentityPage() {
  const { user, loading, refresh } = useAuth();

  const identity = useQuery({
    queryKey: ["my-identity"],
    queryFn: () =>
      clientApi<MyIdentity>("/identity/me/"),
    enabled: Boolean(user),
  });

  const frames = useQuery({
    queryKey: ["identity-frames"],
    queryFn: () =>
      clientApi<
        { results?: IdentityFrame[] } | IdentityFrame[]
      >("/identity/frames/"),
  });

  const badges = useQuery({
    queryKey: ["identity-badges"],
    queryFn: () =>
      clientApi<
        { results?: IdentityBadge[] } | IdentityBadge[]
      >("/identity/badges/"),
  });

  if (loading) {
    return (
      <AppShell>
        <LoadingBlock />
      </AppShell>
    );
  }

  if (!user) {
    return (
      <AppShell>
        <EmptyState
          title="Нужен аккаунт"
          text="Персонализация профиля доступна после входа."
          action={{ href: "/login", label: "Войти" }}
        />
      </AppShell>
    );
  }

  if (identity.isLoading) {
    return (
      <AppShell>
        <LoadingBlock />
      </AppShell>
    );
  }

  if (!identity.data) {
    return (
      <AppShell>
        <div className="error-panel">
          Не удалось загрузить систему идентичности.
        </div>
      </AppShell>
    );
  }

  const allFrames = Array.isArray(frames.data)
    ? frames.data
    : frames.data?.results ?? [];

  const allBadges = Array.isArray(badges.data)
    ? badges.data
    : badges.data?.results ?? [];

  const serverStateKey = [
    identity.data.updated_at ?? "initial",
    identity.data.accent,
    identity.data.equipped_frame?.id ?? "none",
    pinnedIds(identity.data).join(","),
  ].join(":");

  return (
    <IdentityEditor
      key={serverStateKey}
      user={user}
      identity={identity.data}
      frames={allFrames}
      badges={allBadges}
      refresh={refresh}
    />
  );
}
