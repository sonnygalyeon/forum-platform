"use client";

import { FormEvent, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Compass, Search, SlidersHorizontal, Sparkles } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { EmptyState } from "@/components/ui/empty-state";
import { LoadingBlock } from "@/components/ui/loading";
import { SearchCommunities, SearchPublications, SearchTags, SearchUsers } from "@/components/search/search-results";
import { clientApi } from "@/lib/client-api";
import type { DiscoveryResponse, SearchResponse, SearchScope } from "@/lib/types";

const scopes: Array<{ value: SearchScope; label: string }> = [
  { value: "all", label: "Все" },
  { value: "publications", label: "Публикации" },
  { value: "users", label: "Люди" },
  { value: "communities", label: "Сообщества" },
  { value: "tags", label: "Теги" },
];

function SectionTitle({ title, count }: { title: string; count?: number }) {
  return <div className="section-heading search-section-heading"><h2>{title}</h2>{typeof count === "number" ? <span>{count}</span> : null}</div>;
}


function SearchForm({
  initialValue,
  onSearch,
}: {
  initialValue: string;
  onSearch: (value: string) => void;
}) {
  const [input, setInput] = useState(initialValue);

  function submit(event: FormEvent) {
    event.preventDefault();
    onSearch(input.trim());
  }

  return (
    <form className="search-main-form" onSubmit={submit}>
      <Search size={19} />
      <input
        value={input}
        onChange={event => setInput(event.target.value)}
        placeholder="Например: django redis cache"
        autoFocus
      />
      <button className="primary-button" type="submit">
        Найти
      </button>
    </form>
  );
}

export function SearchExperience() {
  const router = useRouter();
  const params = useSearchParams();
  const queryText = params.get("q") ?? "";
  const scope = (params.get("scope") as SearchScope | null) ?? "all";
  const type = params.get("type") ?? "";
  const date = params.get("date") ?? "any";
  const sort = params.get("sort") ?? "relevance";
  const accepted = params.get("accepted") ?? "";
  const tag = params.get("tag") ?? "";

  const searchUrl = useMemo(() => {
    const next = new URLSearchParams();
    if (queryText) next.set("q", queryText);
    next.set("scope", scope);
    if (type) next.set("type", type);
    if (date !== "any") next.set("date", date);
    if (sort !== "relevance") next.set("sort", sort);
    if (accepted) next.set("accepted", accepted);
    if (tag) next.set("tag", tag);
    return `/search/?${next.toString()}`;
  }, [queryText, scope, type, date, sort, accepted, tag]);

  const hasSearchState = Boolean(queryText || tag);
  const search = useQuery({
    queryKey: ["search", searchUrl],
    queryFn: () => clientApi<SearchResponse>(searchUrl),
    enabled: hasSearchState,
  });
  const discovery = useQuery({
    queryKey: ["discover"],
    queryFn: () => clientApi<DiscoveryResponse>("/discover/"),
    enabled: !hasSearchState,
  });

  function push(changes: Record<string, string | null>) {
    const next = new URLSearchParams(params.toString());
    for (const [key, value] of Object.entries(changes)) {
      if (!value || (key === "scope" && value === "all") || (key === "date" && value === "any") || (key === "sort" && value === "relevance")) next.delete(key);
      else next.set(key, value);
    }
    router.push(`/search${next.toString() ? `?${next.toString()}` : ""}`);
  }

  return (
    <>
      <section className="search-hero">
        <div>
          <div className="eyebrow">NIGHT IRIS / DISCOVERY</div>
          <h1>Найти нужный сигнал</h1>
          <p>Полнотекстовый поиск по публикациям, людям, сообществам и тегам. Фильтры не прячут структуру форума — они помогают быстро сузить контекст.</p>
        </div>
        <Compass size={32} />
      </section>

      <SearchForm
        key={queryText}
        initialValue={queryText}
        onSearch={value =>
          push({ q: value || null, tag: null })
        }
      />

      {hasSearchState ? (
        <>
          <div className="search-tabs" role="tablist">
            {scopes.map((item) => {
              const count = search.data?.counts[item.value === "all" ? "publications" : item.value as keyof SearchResponse["counts"]];
              return <button key={item.value} className={scope === item.value ? "active" : ""} onClick={() => push({ scope: item.value })}>{item.label}{item.value !== "all" && typeof count === "number" ? <span>{count}</span> : null}</button>;
            })}
          </div>

          {(scope === "all" || scope === "publications") ? (
            <div className="search-filters">
              <span className="search-filter-label"><SlidersHorizontal size={14}/> Фильтры</span>
              <label>Тип<select value={type} onChange={(event) => push({ type: event.target.value || null })}><option value="">Любой</option><option value="topic">Topic</option><option value="article">Article</option><option value="post">Post</option></select></label>
              <label>Период<select value={date} onChange={(event) => push({ date: event.target.value })}><option value="any">За всё время</option><option value="day">24 часа</option><option value="week">7 дней</option><option value="month">30 дней</option><option value="year">Год</option></select></label>
              <label>Сортировка<select value={sort} onChange={(event) => push({ sort: event.target.value })}><option value="relevance">По релевантности</option><option value="latest">Сначала новые</option></select></label>
              <label>Ответ<select value={accepted} onChange={(event) => push({ accepted: event.target.value || null })}><option value="">Не важно</option><option value="yes">Есть принятый</option><option value="no">Без принятого</option></select></label>
              {tag ? <button type="button" className="filter-chip active" onClick={() => push({ tag: null })}>#{tag} ×</button> : null}
            </div>
          ) : null}

          {search.isLoading ? <LoadingBlock /> : search.isError ? <div className="error-panel">Поиск временно недоступен.</div> : search.data ? (
            <div className="search-results-stack">
              {scope === "all" || scope === "publications" ? <section className="section-block"><SectionTitle title="Публикации" count={search.data.counts.publications}/><SearchPublications items={search.data.publications}/></section> : null}
              {scope === "all" || scope === "users" ? <section className="section-block"><SectionTitle title="Люди" count={search.data.counts.users}/><SearchUsers items={search.data.users}/></section> : null}
              {scope === "all" || scope === "communities" ? <section className="section-block"><SectionTitle title="Сообщества" count={search.data.counts.communities}/><SearchCommunities items={search.data.communities}/></section> : null}
              {scope === "all" || scope === "tags" ? <section className="section-block"><SectionTitle title="Теги" count={search.data.counts.tags}/><SearchTags items={search.data.tags}/></section> : null}
              {Object.values(search.data.counts).every((count) => count === 0) ? <EmptyState icon={Search} title="Ничего не нашли" text="Попробуйте изменить формулировку, убрать фильтр или поискать по тегу."/> : null}
            </div>
          ) : null}
        </>
      ) : (
        discovery.isLoading ? <LoadingBlock /> : discovery.data ? (
          <div className="discovery-stack">
            <section className="section-block"><SectionTitle title="Популярные теги"/><SearchTags items={discovery.data.popular_tags}/></section>
            <section className="section-block"><SectionTitle title="Темы без принятого ответа"/><SearchPublications items={discovery.data.open_topics}/></section>
            <section className="section-block"><SectionTitle title="Активные сообщества"/><SearchCommunities items={discovery.data.active_communities}/></section>
            <section className="section-block"><SectionTitle title="Участники с репутацией"/><SearchUsers items={discovery.data.top_users}/></section>
          </div>
        ) : <EmptyState icon={Sparkles} title="Discovery пока пуст" text="Когда на форуме появится больше контента, здесь будут теги, открытые вопросы, сообщества и участники."/>
      )}
    </>
  );
}
