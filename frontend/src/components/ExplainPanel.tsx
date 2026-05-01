import type { ExplainResponse } from "../types/api";

export function ExplainPanel({
  explain,
  popularityPrior = 0,
  isLoading = false,
  error = null,
  hint = null,
}: {
  explain: ExplainResponse | null;
  popularityPrior?: number;
  isLoading?: boolean;
  error?: string | null;
  hint?: string | null;
}) {
  if (isLoading) {
    return (
      <section className="panel explain-panel">
        <h3>Why this recommendation?</h3>
        <p className="muted explain-panel-shimmer">Loading explanation…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="panel explain-panel explain-panel--error" role="alert">
        <h3>Why this recommendation?</h3>
        <p className="muted">{error}</p>
      </section>
    );
  }

  if (hint && !explain) {
    return (
      <section className="panel explain-panel">
        <h3>Why this recommendation?</h3>
        <p className="muted">{hint}</p>
      </section>
    );
  }

  if (!explain) {
    return (
      <section className="panel explain-panel">
        <h3>Why this recommendation?</h3>
        <p className="muted">
          Pick a game below and tap <strong>Why?</strong> — we compare it to another pick from your list so the
          numbers match how the catalog is indexed.
        </p>
      </section>
    );
  }

  const summary = explain.shared_tags.length
    ? `Recommended because both titles share ${explain.shared_tags.slice(0, 2).join(" and ")}.`
    : "Recommended due to strong latent and content similarity.";

  return (
    <section className="panel explain-panel">
      <h3>Why this recommendation?</h3>
      <p className="muted explain-panel-compare">
        Comparing <strong>{explain.anchor}</strong>
        {" → "}
        <strong>{explain.recommended}</strong>
      </p>
      <div className="explain-bars">
        <Bar label="Content Match" value={explain.txt_sim} />
        <Bar label="Latent Match" value={explain.lsa_sim} />
        <Bar label="Popularity Prior" value={popularityPrior} />
      </div>
      <div className="chip-row">
        {explain.shared_genres.map((item) => (
          <span className="chip" key={`genre-${item}`}>
            {item}
          </span>
        ))}
        {explain.shared_tags.map((item) => (
          <span className="chip subtle tag-gold" key={`tag-${item}`}>
            {item}
          </span>
        ))}
      </div>
      <p className="muted">{summary}</p>
    </section>
  );
}

function Bar({ label, value }: { label: string; value: number }) {
  const width = Math.max(0, Math.min(100, Math.round(value * 100)));
  return (
    <div className="bar-row">
      <span>{label}</span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${width}%` }} />
      </div>
      <strong>{width}%</strong>
    </div>
  );
}
