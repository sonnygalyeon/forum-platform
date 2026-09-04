"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Camera, ImagePlus, Save, Trash2 } from "lucide-react";
import { ChangeEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/layout/app-shell";
import { ProfileBanner } from "@/components/profile/profile-banner";
import { UserAvatar } from "@/components/profile/user-avatar";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { clientApi, errorMessage } from "@/lib/client-api";
import { uploadMediaFile } from "@/lib/media-upload";
import type { NotificationPreferences, User } from "@/lib/types";
import { useAuth } from "@/providers/auth-provider";

type ProfileForm = {
  first_name: string;
  last_name: string;
  bio: string;
  country: string;
  nationality: string;
  interface_language: string;
};

function formFromUser(user: User): ProfileForm {
  return {
    first_name: user.first_name,
    last_name: user.last_name,
    bio: user.bio,
    country: user.country,
    nationality: user.nationality,
    interface_language: user.interface_language ?? "ru",
  };
}

function ProfileEditor({
  user,
  refresh,
}: {
  user: User;
  refresh: () => Promise<void>;
}) {
  const router = useRouter();
  const [form, setForm] = useState<ProfileForm>(() => formFromUser(user));
  const [previewUser, setPreviewUser] = useState<User>(user);
  const [uploading, setUploading] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");

  const prefs = useQuery({
    queryKey: ["notification-preferences"],
    queryFn: () =>
      clientApi<NotificationPreferences>("/notifications/preferences/"),
  });

  const save = useMutation({
    mutationFn: () =>
      clientApi<User>("/users/me/", {
        method: "PATCH",
        body: JSON.stringify({
          ...form,
          country: form.country.toUpperCase(),
          nationality: form.nationality.toUpperCase(),
        }),
      }),
    onSuccess: async () => {
      await refresh();
      router.push("/profile");
    },
  });

  const savePrefs = useMutation({
    mutationFn: (value: NotificationPreferences) =>
      clientApi<NotificationPreferences>("/notifications/preferences/", {
        method: "PATCH",
        body: JSON.stringify(value),
      }),
    onSuccess: () => prefs.refetch(),
  });

  async function uploadProfileImage(
    event: ChangeEvent<HTMLInputElement>,
    kind: "avatar" | "banner",
  ) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      setError("Выберите изображение.");
      return;
    }

    setError("");
    setUploading(kind);

    try {
      const asset = await uploadMediaFile(file, state =>
        setProgress(state.percent),
      );

      const updated = await clientApi<User>("/users/me/", {
        method: "PATCH",
        body: JSON.stringify(
          kind === "avatar"
            ? { avatar_asset_id: asset.id }
            : { banner_asset_id: asset.id },
        ),
      });

      setPreviewUser(updated);
      await refresh();
    } catch (uploadError) {
      setError(errorMessage(uploadError));
    } finally {
      setUploading(null);
      setProgress(0);
    }
  }

  async function clearImage(kind: "avatar" | "banner") {
    const updated = await clientApi<User>("/users/me/", {
      method: "PATCH",
      body: JSON.stringify(
        kind === "avatar"
          ? { avatar_asset_id: null }
          : { banner_asset_id: null },
      ),
    });

    setPreviewUser(updated);
    await refresh();
  }

  return (
    <AppShell>
      <section className="page-head">
        <div>
          <div className="eyebrow">ПРОФИЛЬ / НАСТРОЙКА</div>
          <h1>Оформление и данные</h1>
          <p>
            Аватар и шапка загружаются напрямую в object storage через
            multipart upload.
          </p>
        </div>
      </section>

      <section className="profile-edit-preview">
        <ProfileBanner user={previewUser} />

        <div className="profile-edit-avatar">
          <UserAvatar user={previewUser} size="xl" />
          <label className="media-pick-button">
            <Camera size={15} />
            {uploading === "avatar" ? `${progress}%` : "Сменить аватар"}
            <input
              type="file"
              accept="image/*"
              onChange={event => uploadProfileImage(event, "avatar")}
            />
          </label>

          {previewUser.avatar ? (
            <button
              className="icon-button"
              onClick={() => clearImage("avatar")}
            >
              <Trash2 size={14} />
            </button>
          ) : null}
        </div>

        <div className="banner-actions">
          <label className="secondary-button compact-button">
            <ImagePlus size={14} />
            {uploading === "banner" ? `${progress}%` : "Сменить шапку"}
            <input
              type="file"
              accept="image/*"
              onChange={event => uploadProfileImage(event, "banner")}
            />
          </label>

          {previewUser.banner ? (
            <button
              className="secondary-button compact-button"
              onClick={() => clearImage("banner")}
            >
              <Trash2 size={14} />
              Убрать
            </button>
          ) : null}
        </div>
      </section>

      <section className="settings-card">
        <h2>Основные данные</h2>

        <div className="form-grid">
          <label>
            Имя
            <input
              value={form.first_name}
              onChange={event =>
                setForm(current => ({
                  ...current,
                  first_name: event.target.value,
                }))
              }
            />
          </label>

          <label>
            Фамилия
            <input
              value={form.last_name}
              onChange={event =>
                setForm(current => ({
                  ...current,
                  last_name: event.target.value,
                }))
              }
            />
          </label>
        </div>

        <label>
          О себе
          <textarea
            rows={5}
            maxLength={1000}
            value={form.bio}
            onChange={event =>
              setForm(current => ({
                ...current,
                bio: event.target.value,
              }))
            }
            placeholder="Расскажите, чем вы занимаетесь и что вам интересно."
          />
        </label>

        <div className="form-grid">
          <label>
            Страна
            <input
              maxLength={2}
              value={form.country}
              onChange={event =>
                setForm(current => ({
                  ...current,
                  country: event.target.value.slice(0, 2),
                }))
              }
            />
          </label>

          <label>
            Национальность
            <input
              maxLength={2}
              value={form.nationality}
              onChange={event =>
                setForm(current => ({
                  ...current,
                  nationality: event.target.value.slice(0, 2),
                }))
              }
            />
          </label>
        </div>

        <label>
          Язык интерфейса
          <select
            value={form.interface_language}
            onChange={event =>
              setForm(current => ({
                ...current,
                interface_language: event.target.value,
              }))
            }
          >
            <option value="ru">Русский</option>
            <option value="en">English</option>
            <option value="de">Deutsch</option>
          </select>
        </label>

        {error ? <div className="form-error">{error}</div> : null}
        {save.isError ? (
          <div className="form-error">{errorMessage(save.error)}</div>
        ) : null}

        <div className="editor-actions">
          <button
            className="primary-button"
            onClick={() => save.mutate()}
            disabled={save.isPending}
          >
            <Save size={15} />
            {save.isPending ? "Сохраняем…" : "Сохранить профиль"}
          </button>
        </div>
      </section>

      {prefs.data ? (
        <section className="settings-card">
          <h2>Уведомления</h2>
          <div className="preference-list">
            {(
              [
                [
                  "followed_user_publications",
                  "Публикации авторов, на которых я подписан",
                ],
                [
                  "community_publications",
                  "Новые публикации в сообществах",
                ],
                ["publication_responses", "Ответы на мои публикации"],
                ["comment_replies", "Ответы на мои комментарии"],
                ["accepted_answers", "Принятые ответы"],
                ["new_followers", "Новые подписчики"],
                ["moderation_updates", "Результаты модерации"],
              ] as const
            ).map(([key, label]) => (
              <label className="preference-row" key={key}>
                <span>{label}</span>
                <input
                  type="checkbox"
                  checked={prefs.data[key]}
                  onChange={event =>
                    savePrefs.mutate({
                      ...prefs.data,
                      [key]: event.target.checked,
                    })
                  }
                />
              </label>
            ))}
          </div>
        </section>
      ) : null}
    </AppShell>
  );
}

export default function EditProfilePage() {
  const { user, loading, refresh } = useAuth();

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
          text="Редактирование профиля доступно после входа."
          action={{ href: "/login", label: "Войти" }}
        />
      </AppShell>
    );
  }

  return (
    <ProfileEditor
      key={user.id}
      user={user}
      refresh={refresh}
    />
  );
}
