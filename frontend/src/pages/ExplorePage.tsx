import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Layers, Search } from "lucide-react";
import { ExploreClusterMap } from "../components/ExploreClusterMap";
import { getClusterMap, getClusters } from "../lib/api";
import { messageFromFetchError } from "../lib/apiErrors";
import { normalizeNameForPath } from "../lib/format";
import { compactNumber } from "../lib/format";
import type { ClusterCard } from "../types/api";

function clusterMatches(cluster: ClusterCard, q: string): boolean {
  const lower = q.toLowerCase().trim();
  if (!lower) return true;
  if (cluster.auto_name.toLowerCase().includes(lower)) return true;
  for (const g of cluster.top_genres ?? []) {
    if (g.toLowerCase().includes(lower)) return true;
  }
  for (const ex of cluster.examples ?? []) {
    if (ex.toLowerCase().includes(lower)) return true;
  }
  for (const t of cluster.distinctive_tags ?? []) {
    if (t.tag.toLowerCase().includes(lower)) return true;
  }
  return false;
}

function formatLift(value: number): string {
  if (!Number.isFinite(value)) return "–";
  if (value >= 100) return `${compactNumber(Math.round(value))}×`;
  if (value >= 10) return `${value.toFixed(1)}×`;
  return `${value.toFixed(2)}×`;
}

export function ExplorePage() {
  const [filter, setFilter] = useState("");
  const [focusClusterId, setFocusClusterId] = useState<number | null>(null);
  const cardRefs = useRef<Map<number, HTMLDivElement | null>>(new Map());

  const clusters = useQuery({
    queryKey: ["clusters"],
    queryFn: getClusters,
  });

  const map = useQuery({
    queryKey: ["cluster-map"],
    queryFn: getClusterMap,
    retry: 2,
  });

  const mapDetail = map.isError ? messageFromFetchError(map.error) : undefined;

  const data = clusters.data ?? [];
  const visible = useMemo(() => data.filter((c) => clusterMatches(c, filter)), [data, filter]);
  const totalCatalog = useMemo(() => data.reduce((s, c) => s + c.size, 0), [data]);

  useEffect(() => {
    if (focusClusterId === null) return;
    window.requestAnimationFrame(() => {
      const el = cardRefs.current.get(focusClusterId);
      el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    });
  }, [focusClusterId]);

  return (
    <div className="page explore-page">
      <section className="section explore-hero">
        <div className="explore-hero-copy">
          <p className="explore-tagline">
            <Layers size={16} aria-hidden /> Explore hidden genres
          </p>
          <h1>KMeans latent clusters</h1>
          <p className="muted explore-lead">
            Each bubble is thousands of Steam games partitioned in LSA feature space — not store
            tags. Browse the PCA map, skim lift-heavy tags per cluster, and jump straight into titles.
          </p>
          <div className="explore-hero-metrics">
            <div>
              <strong>{clusters.isLoading ? "…" : data.length}</strong>
              <span className="muted">clusters fitted</span>
            </div>
            <div>
              <strong>{clusters.isLoading ? "…" : totalCatalog.toLocaleString()}</strong>
              <span className="muted">catalog games labeled</span>
            </div>
            <Link to="/search" className="text-link explore-inline-link">
              Find a game · browse catalog
            </Link>
          </div>
        </div>
      </section>

      <section className="section explore-split">
        <div className="explore-pane explore-pane-map">
          <div className="section-head explore-map-head">
            <h2>Latent topology</h2>
            <p className="muted">
              Hover for titles; click dots or centroid rings to focus a cluster card. Axes compress
              the full latent vector — nearby points tend to share tags and tone.
            </p>
          </div>
          <ExploreClusterMap
            data={map.data}
            isLoading={map.isLoading}
            hasError={map.isError}
            errorDetail={mapDetail}
            highlightClusterId={focusClusterId}
            onSelectCluster={setFocusClusterId}
          />
          {map.isError ? (
            <div className="explore-map-actions">
              <button type="button" className="pill subtle" disabled={map.isFetching} onClick={() => map.refetch()}>
                {map.isFetching ? "Loading…" : "Retry cluster map"}
              </button>
            </div>
          ) : null}
        </div>

        <div className="explore-pane explore-pane-list">
          <div className="explore-controls">
            <label className="explore-search">
              <Search size={18} aria-hidden />
              <input
                type="search"
                placeholder="Filter by latent name, Steam genre, examples, tags…"
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                aria-label="Filter clusters"
              />
            </label>

            {!clusters.isLoading && data.length ? (
              <div className="explore-chip-rail" role="tablist" aria-label="Focus cluster">
                <button
                  type="button"
                  className={`explore-mini-chip ${focusClusterId === null ? "is-on" : ""}`}
                  onClick={() => setFocusClusterId(null)}
                >
                  All
                </button>
                {(filter ? visible : data).map((c) => (
                  <button
                    type="button"
                    key={c.cluster_id}
                    className={`explore-mini-chip ${focusClusterId === c.cluster_id ? "is-on" : ""}`}
                    onClick={() =>
                      setFocusClusterId((prev) => (prev === c.cluster_id ? null : c.cluster_id))
                    }
                  >
                    #{c.cluster_id} · {(c.auto_name ?? "").slice(0, 42)}
                    {(c.auto_name ?? "").length > 42 ? "…" : ""}
                  </button>
                ))}
              </div>
            ) : null}
          </div>

          {clusters.isError ? (
            <p role="alert" className="explore-alert">
              Could not load cluster cards. Confirm the FastAPI `/discover/clusters` route is reachable.
            </p>
          ) : null}

          <div className="cluster-row explore-cluster-cards">
            {clusters.isLoading
              ? Array.from({ length: 6 }).map((_, i) => (
                  <article key={i} className="cluster-card explore-cluster-card explore-cluster-card--busy">
                    <div className="skeleton-line long" />
                    <div className="skeleton-line medium" />
                    <div className="explore-skeleton-chips">
                      <div className="skeleton-line short" />
                      <div className="skeleton-line short" />
                    </div>
                  </article>
                ))
              : null}

            {!clusters.isLoading &&
              visible.map((cluster) => {
                const tags = [...(cluster.distinctive_tags ?? [])].sort((a, b) => b.lift - a.lift);
                const genres = cluster.top_genres ?? [];
                const isActive = focusClusterId === cluster.cluster_id;
                const isDimmed = focusClusterId !== null && !isActive;

                return (
                  <article
                    key={cluster.cluster_id}
                    ref={(el) => {
                      cardRefs.current.set(cluster.cluster_id, el);
                    }}
                    id={`explore-cluster-${cluster.cluster_id}`}
                    data-cluster-id={cluster.cluster_id}
                    className={`cluster-card explore-cluster-card ${isActive ? "is-focused" : ""} ${isDimmed ? "is-dimmed" : ""}`}
                  >
                    <div className="explore-card-top">
                      <span className="explore-cluster-id">#{cluster.cluster_id}</span>
                      <h3>{cluster.auto_name}</h3>
                    </div>
                    <p className="muted explore-card-meta">
                      {cluster.size.toLocaleString()} games · avg popularity{" "}
                      <strong>{cluster.avg_popularity.toFixed(3)}</strong>
                    </p>

                    {genres.length ? (
                      <div className="chip-row explore-genre-row">
                        {genres.slice(0, 5).map((g) => (
                          <span className="chip subtle" key={g}>
                            {g}
                          </span>
                        ))}
                      </div>
                    ) : null}

                    <div className="explore-lift-grid">
                      {tags.slice(0, 6).map((t) => (
                        <span key={`${cluster.cluster_id}-${t.tag}`} className="explore-lift-pill">
                          <span>{t.tag}</span>
                          <small className="muted">{formatLift(t.lift)}</small>
                          <small className="muted">{t.count}×</small>
                        </span>
                      ))}
                    </div>

                    <div className="explore-example-row">
                      {(cluster.examples ?? []).slice(0, 8).map((title) => (
                        <Link
                          key={title}
                          to={`/game/${normalizeNameForPath(title)}`}
                          className="explore-example-link"
                        >
                          {title}
                        </Link>
                      ))}
                    </div>

                    <div className="explore-card-actions">
                      <button
                        type="button"
                        className="text-link"
                        onClick={() =>
                          setFocusClusterId((p) =>
                            p === cluster.cluster_id ? null : cluster.cluster_id
                          )
                        }
                      >
                        {focusClusterId === cluster.cluster_id ? "Clear spotlight" : "Spotlight map"}
                      </button>
                      {cluster.examples?.[0] ? (
                        <Link
                          to={`/game/${normalizeNameForPath(cluster.examples[0])}`}
                          className="text-link"
                        >
                          Open flagship example →
                        </Link>
                      ) : null}
                    </div>
                  </article>
                );
              })}
          </div>

          {!clusters.isLoading && visible.length === 0 ? (
            <p className="muted">No clusters match that filter.</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}
