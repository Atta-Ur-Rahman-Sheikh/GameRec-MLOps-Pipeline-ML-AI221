import { useMutation, useQuery } from "@tanstack/react-query";
import { ChevronDown, Filter, RotateCcw, Search, Sparkles, Wand2 } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { GameCard } from "../components/GameCard";
import { PreferenceForm } from "../components/PreferenceForm";
import { SkeletonCard } from "../components/SkeletonCard";
import type { GameViewModel } from "../lib/api";
import { getUserRecommendations, searchGames } from "../lib/api";

const GENRE_FILTERS = ["Action", "RPG", "Indie", "Adventure", "Strategy", "Simulation"] as const;
const PLATFORM_FILTERS = ["PC", "PlayStation", "Xbox", "Switch"] as const;

const QUICK_TERMS = ["RPG", "Indie horror", "Racing co-op", "Strategy", "Metroidvania", "Souls"];

type SortOption = "popularity" | "rating" | "name";

function gameGenresText(game: GameViewModel): string {
  const { genres } = game;
  return (Array.isArray(genres) ? genres : [String(genres)])
    .join(" ")
    .toLowerCase();
}

function matchesPlatformFilter(game: GameViewModel, label: string): boolean {
  const hay = game.platforms.join(" ").toLowerCase();
  const l = label.toLowerCase();
  if (l === "pc") {
    return (
      hay.includes("pc") ||
      hay.includes("windows") ||
      hay.includes("linux") ||
      hay.includes("macos") ||
      hay.includes(" mac")
    );
  }
  if (l === "playstation") {
    return hay.includes("playstation") || hay.includes("ps vita") || /\bps\b/.test(hay);
  }
  if (l === "xbox") return hay.includes("xbox");
  if (l === "switch") return hay.includes("switch") || hay.includes("nintendo");
  return hay.includes(l);
}

function filterCatalog(
  games: GameViewModel[],
  genres: Set<string>,
  platforms: Set<string>
): GameViewModel[] {
  return games.filter((game) => {
    if (genres.size > 0) {
      const text = gameGenresText(game);
      const ok = [...genres].some((g) => text.includes(g.toLowerCase()));
      if (!ok) return false;
    }
    if (platforms.size > 0) {
      const ok = [...platforms].some((p) => matchesPlatformFilter(game, p));
      if (!ok) return false;
    }
    return true;
  });
}

function sortGames(games: GameViewModel[], sortBy: SortOption): GameViewModel[] {
  const copy = [...games];
  if (sortBy === "popularity") {
    copy.sort((a, b) => b.popularity - a.popularity);
  } else if (sortBy === "rating") {
    copy.sort((a, b) => (b.rating ?? 0) - (a.rating ?? 0));
  } else {
    copy.sort((a, b) => a.name.localeCompare(b.name));
  }
  return copy;
}

export function SearchPage() {
  const [params, setParams] = useSearchParams();
  const query = (params.get("q") ?? "").trim();
  const [localQuery, setLocalQuery] = useState(query);
  const [sortBy, setSortBy] = useState<SortOption>("popularity");
  const [selectedGenres, setSelectedGenres] = useState<Set<string>>(() => new Set());
  const [selectedPlatforms, setSelectedPlatforms] = useState<Set<string>>(() => new Set());
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [personalOpen, setPersonalOpen] = useState(false);
  const personalAnchorRef = useRef<HTMLDetailsElement | null>(null);

  useEffect(() => {
    setLocalQuery(query);
  }, [query]);

  useEffect(() => {
    setPersonalOpen(false);
  }, [query]);

  const search = useQuery({
    queryKey: ["search", query],
    queryFn: () => searchGames(query, 30),
    enabled: query.length > 0,
  });

  const recommend = useMutation({
    mutationFn: getUserRecommendations,
  });

  const title = query ? `Results for "${query}"` : "Browse catalog";

  const filteredSorted = useMemo(() => {
    const raw = search.data ?? [];
    const filtered = filterCatalog(raw, selectedGenres, selectedPlatforms);
    return sortGames(filtered, sortBy);
  }, [search.data, selectedGenres, selectedPlatforms, sortBy]);

  const toggleGenre = (g: string) => {
    setSelectedGenres((prev) => {
      const next = new Set(prev);
      if (next.has(g)) next.delete(g);
      else next.add(g);
      return next;
    });
  };

  const togglePlatform = (p: string) => {
    setSelectedPlatforms((prev) => {
      const next = new Set(prev);
      if (next.has(p)) next.delete(p);
      else next.add(p);
      return next;
    });
  };

  const activeFilterCount = selectedGenres.size + selectedPlatforms.size;

  const clearFilters = () => {
    setSelectedGenres(new Set());
    setSelectedPlatforms(new Set());
    setSortBy("popularity");
  };

  const submitSearch = (event: React.FormEvent) => {
    event.preventDefault();
    const next = localQuery.trim();
    setParams(next ? { q: next } : {});
  };

  const openPersonalSection = () => {
    setPersonalOpen(true);
    requestAnimationFrame(() => {
      personalAnchorRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  return (
    <div className="page browse-page">
      <section className="browse-layout">
        <button
          type="button"
          className="browse-filters-toggle"
          aria-expanded={filtersOpen}
          aria-controls="browse-filters"
          onClick={() => setFiltersOpen((open) => !open)}
        >
          <Filter size={16} strokeWidth={2.25} />
          <span>Filters</span>
          {activeFilterCount > 0 ? <span className="browse-filter-badge">{activeFilterCount}</span> : null}
        </button>

        <aside
          id="browse-filters"
          className={`filters-sidebar ${filtersOpen ? "is-open" : ""}`}
        >
          <div className="filters-sidebar-head">
            <h2 className="filters-title">Refine</h2>
            {activeFilterCount > 0 ? (
              <button type="button" className="browse-clear-filters" onClick={clearFilters}>
                <RotateCcw size={14} />
                Clear
              </button>
            ) : null}
          </div>
          <p className="filters-hint muted">Narrow results from your current search. Filters apply after results load.</p>

          <details open className="filter-group">
            <summary>Genres</summary>
            <div className="filter-list">
              {GENRE_FILTERS.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`filter-item ${selectedGenres.has(item) ? "is-active" : ""}`}
                  onClick={() => toggleGenre(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </details>
          <details open className="filter-group">
            <summary>Platforms</summary>
            <div className="filter-list">
              {PLATFORM_FILTERS.map((item) => (
                <button
                  key={item}
                  type="button"
                  className={`filter-item ${selectedPlatforms.has(item) ? "is-active" : ""}`}
                  onClick={() => togglePlatform(item)}
                >
                  {item}
                </button>
              ))}
            </div>
          </details>

          <div className="filters-sidebar-footer muted">
            <Link to="/for-you" className="browse-cross-link">
              Open full preference flow →
            </Link>
          </div>
        </aside>

        <div className="results-panel">
          <header className="browse-results-header">
            <div className="browse-results-titleblock">
              <p className="kicker browse-kicker">
                <Search size={13} aria-hidden /> Catalog
              </p>
              <h1>{title}</h1>
              {query ? (
                <p className="muted browse-subtitle">
                  {search.isLoading
                    ? "Searching…"
                    : search.isError
                      ? ""
                      : `${filteredSorted.length} game${filteredSorted.length === 1 ? "" : "s"} shown${
                          filteredSorted.length !== (search.data?.length ?? 0)
                            ? ` (of ${search.data?.length ?? 0} from search)`
                            : ""
                        }`}
                </p>
              ) : (
                <p className="muted browse-subtitle">Search Steam-backed titles. Use filters once you run a query.</p>
              )}
            </div>
          </header>

          <form className="browse-search-form" onSubmit={submitSearch}>
            <div className="browse-search-shell">
              <Search className="browse-search-icon" size={18} aria-hidden />
              <input
                value={localQuery}
                onChange={(event) => setLocalQuery(event.target.value)}
                placeholder="Games, franchises, moods — e.g. cozy farming, FPS…"
                aria-label="Search games"
              />
              <button type="submit">Search</button>
            </div>
          </form>

          {query ? (
            <div className="browse-toolbar">
              <label className="browse-sort-label browse-sort-label--lead">
                <span>Sort</span>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as SortOption)}
                  className="browse-sort-select"
                  aria-label="Sort results"
                >
                  <option value="popularity">Popularity (model)</option>
                  <option value="rating">User rating</option>
                  <option value="name">Name (A–Z)</option>
                </select>
              </label>
              <button
                type="button"
                className="browse-personal-inline-cta"
                onClick={() => (personalOpen ? setPersonalOpen(false) : openPersonalSection())}
                aria-expanded={personalOpen}
                aria-controls="browse-personal-panel"
              >
                <Wand2 size={15} aria-hidden />
                <span>{personalOpen ? "Hide ML picks" : "ML personal picks"}</span>
                <ChevronDown
                  size={15}
                  aria-hidden
                  className={personalOpen ? "browse-personal-chevron is-open" : "browse-personal-chevron"}
                />
              </button>
            </div>
          ) : null}

          {query && search.isError ? (
            <div className="browse-feedback browse-feedback--error" role="alert">
              <strong>Couldn’t load results.</strong>
              <p className="muted">Check that the API is running, then retry.</p>
              <button type="button" className="ghost-button" onClick={() => search.refetch()}>
                Retry search
              </button>
            </div>
          ) : null}

          {!query ? (
            <div className="browse-empty-state">
              <div className="browse-empty-inner">
                <Sparkles size={28} className="browse-empty-icon" aria-hidden />
                <h2>Start with a query</h2>
                <p className="muted">
                  Results load here after you search. Pick a shortcut or type what you’re in the mood for.
                </p>
                <div className="browse-quick-pills">
                  {QUICK_TERMS.map((term) => (
                    <button
                      key={term}
                      type="button"
                      className="chip browse-quick-pill"
                      onClick={() => {
                        setLocalQuery(term);
                        setParams({ q: term });
                      }}
                    >
                      {term}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : null}

          {query && search.isLoading ? (
            <div className="game-grid dense browse-results-grid">{Array.from({ length: 12 }).map((_, idx) => (
                <SkeletonCard key={idx} />
              ))}
            </div>
          ) : null}

          {query && !search.isLoading && !search.isError ? (
            filteredSorted.length === 0 ? (
              <div className="browse-feedback">
                <p className="muted">
                  {(search.data?.length ?? 0) === 0
                    ? "No titles matched that query. Try different keywords or spelling."
                    : "No titles match these filters — clear filters or loosen your search."}
                </p>
                {activeFilterCount > 0 ? (
                  <button type="button" className="text-link browse-inline-action" onClick={clearFilters}>
                    Clear filters
                  </button>
                ) : null}
              </div>
            ) : (
              <div className="game-grid dense browse-results-grid">
                {filteredSorted.map((game) => (
                  <GameCard game={game} key={game.name} />
                ))}
              </div>
            )
          ) : null}

          {query ? (
            <details
              ref={personalAnchorRef}
              id="browse-personal"
              className="browse-personal-details"
              open={personalOpen}
              onToggle={(event) => {
                setPersonalOpen(event.currentTarget.open);
              }}
            >
              <summary className="browse-personal-summary">
                <span className="browse-personal-summary-main">
                  <Wand2 size={16} aria-hidden />
                  <span className="browse-personal-summary-text">
                    <strong>ML personal picks</strong>
                    <span className="muted browse-personal-summary-sub">
                      Optional — expand to set genres, tags & platforms (same engine as{" "}
                      <Link to="/for-you" onClick={(e) => e.stopPropagation()}>
                        For you
                      </Link>
                      ). Keeps browse results above so you scroll less.
                    </span>
                  </span>
                </span>
                <ChevronDown
                  size={18}
                  aria-hidden
                  className={personalOpen ? "browse-personal-chevron is-open" : "browse-personal-chevron"}
                />
              </summary>
              <div className="browse-personal-body" id="browse-personal-panel">
                <div className="split browse-personal-split">
                  <PreferenceForm
                    onSubmit={(payload) =>
                      recommend.mutate({
                        ...payload,
                        n: 12,
                        min_pop_quantile: 0.4,
                        w_lsa: 0.3,
                        w_text: 0.3,
                        w_pop: 0.4,
                        use_content_richness: true,
                      })
                    }
                  />
                  <div className="panel browse-personal-results">
                    <div className="browse-personal-results-head">
                      <h3 className="browse-personal-results-title">Suggested for your profile</h3>
                      {recommend.isPending ? (
                        <span className="muted browse-inline-hint">Generating…</span>
                      ) : null}
                      {recommend.isError ? (
                        <span className="browse-inline-hint browse-inline-hint--warn">
                          Something went wrong. Try again.
                        </span>
                      ) : null}
                    </div>
                    {!recommend.isPending &&
                    recommend.data !== undefined &&
                    recommend.data.length === 0 ? (
                      <p className="muted browse-personal-placeholder">Submit the form to generate recommendations.</p>
                    ) : null}
                    <div className="game-grid compact browse-personal-grid">
                      {recommend.isPending
                        ? Array.from({ length: 6 }).map((_, idx) => <SkeletonCard key={idx} />)
                        : (recommend.data ?? []).map((game) => (
                            <GameCard key={game.name} game={game} subtitle="Personalized" />
                          ))}
                    </div>
                  </div>
                </div>
              </div>
            </details>
          ) : null}
        </div>
      </section>
    </div>
  );
}
