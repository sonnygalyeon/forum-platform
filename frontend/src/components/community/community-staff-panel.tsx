"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Search, Shield, Trash2, UsersRound } from "lucide-react";
import { useState } from "react";
import { clientApi } from "@/lib/client-api";
import type { CursorPage, SearchResponse, User } from "@/lib/types";

type StaffEntry = { user: User; role: "moderator" | "editor"; added_by: User; created_at: string; updated_at: string };

export function CommunityStaffPanel({ communityId, canManage }: { communityId: string; canManage: boolean }) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const staff = useQuery({
    queryKey: ["community-staff", communityId],
    queryFn: () => clientApi<CursorPage<StaffEntry>>(`/communities/${communityId}/staff/`),
  });
  const users = useQuery({
    queryKey: ["community-staff-search", search],
    queryFn: () => clientApi<SearchResponse>(`/search/?q=${encodeURIComponent(search)}&scope=users`),
    enabled: canManage && search.trim().length >= 2,
  });
  const assign = useMutation({
    mutationFn: ({ userId, role }: { userId: string; role: StaffEntry["role"] }) => clientApi(`/communities/${communityId}/staff/`, { method: "POST", body: JSON.stringify({ user_id: userId, role }) }),
    onSuccess: async () => {
      setSearch("");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["community-staff", communityId] }),
        queryClient.invalidateQueries({ queryKey: ["community", communityId] }),
      ]);
    },
  });
  const remove = useMutation({
    mutationFn: (userId: string) => clientApi(`/communities/${communityId}/staff/${userId}/`, { method: "DELETE" }),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["community-staff", communityId] }),
        queryClient.invalidateQueries({ queryKey: ["community", communityId] }),
      ]);
    },
  });

  return (
    <section className="community-staff-panel">
      <div className="section-heading"><h2><Shield size={18}/> Команда сообщества</h2><span>{staff.data?.results.length ?? 0} назначено</span></div>
      {canManage ? (
        <div className="staff-search">
          <Search size={15}/><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Найти пользователя для роли…"/>
          {users.data?.users.length ? <div className="staff-search-results">{users.data.users.slice(0,5).map((user) => <div key={user.id}><span>@{user.nickname}</span><button type="button" onClick={() => assign.mutate({userId:user.id,role:"moderator"})}>Модератор</button><button type="button" onClick={() => assign.mutate({userId:user.id,role:"editor"})}>Редактор</button></div>)}</div> : null}
        </div>
      ) : null}
      {staff.data?.results.length ? <div className="staff-list">{staff.data.results.map((entry) => <div className="staff-row" key={entry.user.id}><span className="staff-avatar"><UsersRound size={15}/></span><div><strong>@{entry.user.nickname}</strong><small>{entry.role === "moderator" ? "Модератор" : "Редактор"}</small></div>{canManage?<button type="button" className="ghost-danger" aria-label="Удалить роль" onClick={() => remove.mutate(entry.user.id)}><Trash2 size={14}/></button>:null}</div>)}</div> : <div className="inline-empty">Владелец пока управляет сообществом один.</div>}
    </section>
  );
}
