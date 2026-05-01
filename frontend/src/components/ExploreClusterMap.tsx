import { useMemo, useState } from "react";
import type { ClusterMapResponse } from "../types/api";

function clusterHue(clusterId: number): number {
  return ((clusterId * 47 + 311) % 360 + 360) % 360;
}

type TooltipState = {
  title: string;
  subtitle?: string;
  clientX: number;
  clientY: number;
} | null;

type ExploreClusterMapProps = {
  data: ClusterMapResponse | undefined;
  isLoading: boolean;
  hasError: boolean;
  errorDetail?: string;
  highlightClusterId: number | null;
  onSelectCluster: (clusterId: number | null) => void;
};

export function ExploreClusterMap({
  data,
  isLoading,
  hasError,
  errorDetail,
  highlightClusterId,
  onSelectCluster,
}: ExploreClusterMapProps) {
  const [tip, setTip] = useState<TooltipState>(null);

  const centroidById = useMemo(() => {
    const m = new Map<number, ClusterMapResponse["centroids"][0]>();
    for (const c of data?.centroids ?? []) {
      m.set(c.cluster_id, c);
    }
    return m;
  }, [data?.centroids]);

  if (isLoading) {
    return (
      <div className="explore-map-shell scatter-shell explore-map-shell--busy" aria-busy="true">
        <div className="explore-map-placeholder" />
        <p className="muted explore-map-caption">Projecting latent space …</p>
      </div>
    );
  }

  if (hasError || !data?.points?.length) {
    return (
      <div className="explore-map-shell scatter-shell explore-map-shell--empty">
        <p className="muted">
          {hasError ? (
            <>
              Cluster map could not load.{" "}
              {errorDetail ? <span className="explore-map-error-msg">{errorDetail}</span> : null}{" "}
              Cards below still summarize each cluster.
            </>
          ) : (
            <>Map response had no plotted points.</>
          )}
        </p>
      </div>
    );
  }

  const [ev1, ev2] = data.explained_variance_ratio;

  const handleBackdropClick = () => {
    setTip(null);
    onSelectCluster(null);
  };

  return (
    <div className="explore-map-shell scatter-shell">
      <div className="explore-map-header">
        <span className="explore-map-kicker">2D PCA of LSA rows</span>
        <button type="button" className="text-link explore-map-reset" onClick={handleBackdropClick}>
          Reset focus
        </button>
      </div>
      <svg
        className="explore-map-svg"
        viewBox="0 0 100 100"
        role="presentation"
        onClick={(e) => {
          if (e.target === e.currentTarget) handleBackdropClick();
        }}
      >
        <title>Scatter of games in compressed latent space, colored by KMeans cluster</title>
        <defs>
          <pattern id="explore-grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="#333" strokeWidth="0.35" opacity="0.45" />
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#explore-grid)" opacity="0.35" />
        <rect width="100" height="100" fill="#181818" opacity="0.92" />

        {data.points.map((p, i) => {
          const dimmed = highlightClusterId !== null && p.cluster_id !== highlightClusterId;
          const h = clusterHue(p.cluster_id);
          const fill = `hsl(${h} 62% 56%)`;
          return (
            <g key={`${p.name}-${i}`}>
              <circle
                cx={p.x}
                cy={100 - p.y}
                r={4.8}
                className="explore-hit"
                fill="transparent"
                onMouseEnter={(e) =>
                  setTip({
                    title: p.name,
                    subtitle: centroidById.get(p.cluster_id)?.label,
                    clientX: e.clientX,
                    clientY: e.clientY,
                  })
                }
                onMouseLeave={() => setTip(null)}
                onClick={(ev) => {
                  ev.stopPropagation();
                  setTip(null);
                  onSelectCluster(p.cluster_id);
                }}
              />
              <circle
                cx={p.x}
                cy={100 - p.y}
                r={highlightClusterId === p.cluster_id ? 2.35 : 1.65}
                fill={fill}
                stroke="rgba(0,0,0,0.35)"
                strokeWidth={0.25}
                className={dimmed ? "explore-dot explore-dot-dimmed" : "explore-dot"}
                pointerEvents="none"
              />
            </g>
          );
        })}

        {data.centroids.map((c) => {
          const isFocus = highlightClusterId === null || highlightClusterId === c.cluster_id;
          return (
            <g key={`cent-${c.cluster_id}`} className={isFocus ? "explore-centroid" : "explore-centroid is-muted"}>
              <circle
                cx={c.x}
                cy={100 - c.y}
                r={10}
                fill="transparent"
                className="explore-hit"
                onMouseEnter={(e) =>
                  setTip({
                    title: c.label,
                    subtitle: `${c.n_games.toLocaleString()} titles · centroid`,
                    clientX: e.clientX,
                    clientY: e.clientY,
                  })
                }
                onMouseLeave={() => setTip(null)}
                onClick={(ev) => {
                  ev.stopPropagation();
                  setTip(null);
                  onSelectCluster(c.cluster_id);
                }}
              />
              <circle
                cx={c.x}
                cy={100 - c.y}
                r={5.2}
                fill="none"
                stroke={`hsl(${clusterHue(c.cluster_id)} 70% 70%)`}
                strokeWidth={0.95}
                strokeDasharray="2.2 2.2"
                opacity={isFocus ? 1 : 0.55}
              />
              <circle
                cx={c.x}
                cy={100 - c.y}
                r={highlightClusterId === c.cluster_id ? 2 : 1.2}
                fill="#f7f7f7"
                opacity={highlightClusterId === c.cluster_id ? 0.95 : isFocus ? 0.72 : 0.4}
              />
            </g>
          );
        })}
      </svg>

      <div className="explore-map-footer muted">
        <span>
          PC1 {Math.round(ev1 * 100)}% · PC2 {Math.round(ev2 * 100)}% variance ·{" "}
          {data.points.length.toLocaleString()} plotted sample points
        </span>
      </div>

      {tip ? (
        <div
          className="explore-map-tip"
          style={{
            position: "fixed",
            left: tip.clientX + 12,
            top: tip.clientY + 12,
            pointerEvents: "none",
          }}
        >
          <strong>{tip.title}</strong>
          {tip.subtitle ? <span className="muted">{tip.subtitle}</span> : null}
        </div>
      ) : null}
    </div>
  );
}
