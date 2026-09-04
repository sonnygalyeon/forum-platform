"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Save } from "lucide-react";
import { FormEvent, useState } from "react";
import { clientApi, errorMessage } from "@/lib/client-api";
import type { Community } from "@/lib/types";

export function CommunitySettingsPanel({ community }: { community: Community }) {
  const queryClient = useQueryClient();
  const [name, setName] = useState(community.name);
  const [description, setDescription] = useState(community.description);
  const update = useMutation({
    mutationFn: () => clientApi<Community>(`/communities/${community.id}/`, {
      method: "PATCH",
      body: JSON.stringify({ name: name.trim(), description }),
    }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["community", community.id] }),
        queryClient.invalidateQueries({ queryKey: ["communities"] }),
      ]);
    },
  });

  function submit(event: FormEvent) {
    event.preventDefault();
    if (name.trim().length < 3) return;
    update.mutate();
  }

  return (
    <form className="community-settings-panel" onSubmit={submit}>
      <div className="section-heading"><h2>Настройки сообщества</h2><span>Редактор или владелец</span></div>
      <label>Название<input value={name} onChange={(event) => setName(event.target.value)} minLength={3} maxLength={120}/></label>
      <label>Описание<textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={4} maxLength={5000}/></label>
      {update.isError ? <div className="form-error">{errorMessage(update.error)}</div> : null}
      <button className="primary-button" disabled={update.isPending}><Save size={14}/> {update.isPending ? "Сохраняем…" : "Сохранить"}</button>
    </form>
  );
}
