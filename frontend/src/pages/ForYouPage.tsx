import { useMutation } from "@tanstack/react-query";
import { Sparkles, Wand2 } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { GameCard } from "../components/GameCard";
import { ExplainPanel } from "../components/ExplainPanel";
import { SkeletonCard } from "../components/SkeletonCard";
import { getArchetypesByQuery, getExplain, getUserRecommendations, type GameViewModel } from "../lib/api";
import { readArchetypeIdentity, writeArchetypeIdentity } from "../lib/identity";

function parsePreference(text: string): { genres: string[]; tags: string[] } {
  const lower = text.toLowerCase();
  const genres = [
    "Action",
    "RPG",
    "Adventure",
    "Strategy",
    "Simulation",
    "Sports",
    "Indie",
    "Shooter",
  ].filter((g) => lower.includes(g.toLowerCase()));
  const tags = [
    "Open World",
    "Story Rich",
    "Horror",
    "Co-op",
    "Survival",
    "Roguelike",
    "PVP",
    "Sandbox",
  ].filter((t) => lower.includes(t.toLowerCase()));
  return { genres, tags };
}

/** Explain API needs two real catalog titles; use another recommendation as the reference anchor. */
function resolveExplainAnchor(candidate: string, items: GameViewModel[]): string | null {
  if (items.length < 2) return null;
  const first = items[0].name;
  if (candidate !== first) return first;
  return items[1].name;
}

export function ForYouPage() {
  const storedIdentity = readArchetypeIdentity();
  const [input, setInput] = useState("");
  const [anchorHint, setAnchorHint] = useState("");
  const [style, setStyle] = useState(55);
  const [niche, setNiche] = useState(55);
  const [picked, setPicked] = useState<string | null>(null);
  const [recommendations, setRecommendations] = useState<GameViewModel[]>([]);
  const [explainHint, setExplainHint] = useState<string | null>(null);

  const explain = useMutation({
    mutationFn: ({ anchorName, candidate }: { anchorName: string; candidate: string }) =>
      getExplain(anchorName, candidate),
    onMutate: () => setExplainHint(null),
    onError: () => setExplainHint(null),
  });

  const archetype = useMutation({
    mutationFn: getArchetypesByQuery,
    onSuccess: (result) => {
      const best = [...result.predictions].sort((a, b) => b.probability - a.probability)[0];
      if (best) {
        writeArchetypeIdentity({
          archetype: best.archetype,
          confidence: best.probability,
        });
      }
    },
  });

  const run = useMutation({
    mutationFn: getUserRecommendations,
    onSuccess: (items) => {
      setRecommendations(items);
      setPicked(null);
      explain.reset();
      setExplainHint(null);
    },
    onError: () => {
      setRecommendations([]);
    },
  });

  const parsedPreview = useMemo(() => parsePreference(input), [input]);
  const trimmed = input.trim();
  const likedTags = parsedPreview.tags.length > 0 ? parsedPreview.tags : trimmed ? [trimmed] : [];
  const likedGenres = parsedPreview.genres;
  const canSubmit = likedGenres.length > 0 || likedTags.length > 0;

  const styleLabel = useMemo(
    () => (style < 50 ? "Closer to literal keywords" : "Closer to latent / vibe"),
    [style]
  );
  const nicheLabel = useMemo(
    () => (niche < 50 ? "Lean popular" : "Lean hidden / niche"),
    [niche]
  );

  const submit = async (event?: React.FormEvent) => {
    event?.preventDefault();
    if (!canSubmit || run.isPending) return;

    const parsed = parsePreference(input);
    const tags = parsed.tags.length > 0 ? parsed.tags : [trimmed];
    const wText = Math.max(0.05, 1 - style / 100);
    const wLsa = Math.max(0.05, style / 100);
    const wPop = Math.max(0.05, 1 - niche / 100);
    const minPop = niche / 100;

    setAnchorHint(trimmed.slice(0, 80) + (trimmed.length > 80 ? "…" : ""));
    const payload = {
      liked_genres: parsed.genres,
      liked_tags: tags,
      platforms: [] as string[],
      n: 12,
      min_pop_quantile: minPop,
      min_rating: 0,
      w_lsa: wLsa,
      w_text: wText,
      w_pop: wPop,
      use_content_richness: true,
    };

    try {
      await run.mutateAsync(payload);
      archetype.mutate({
        liked_genres: parsed.genres,
        liked_tags: tags,
        top_k: 4,
        threshold: 0.4,
      });
    } catch {
      // run.onError clears list; toast not required
    }
  };

  const onWhyClick = (game: GameViewModel) => {
    setPicked(game.name);
    const anchorName = resolveExplainAnchor(game.name, recommendations);
    if (!anchorName) {
      explain.reset();
      setExplainHint(
        "We need at least two recommendations to compare. Try a broader description or adjust sliders, then run again."
      );
      return;
    }
    setExplainHint(null);
    explain.reset();
    explain.mutate({ anchorName, candidate: game.name });
  };

  const explainErrorMessage = explain.error
    ? explain.error instanceof Error
      ? explain.error.message.slice(0, 280)
      : String(explain.error).slice(0, 280)
    : null;

  return (
    <div className="page for-you-page">
      <section className="for-you-layout">
        <aside className="for-you-input">
          <p className="kicker for-you-kicker">
            <Wand2 size={14} aria-hidden /> For you
          </p>
          <h2>Describe what you want to play</h2>
          <p className="muted for-you-lead">
            Free text is turned into genre/tag signals. Named genres in your text (e.g. <strong>RPG</strong>,{" "}
            <strong>Indie</strong>) are picked up automatically — or we use your whole line as a content tag.
          </p>

          {storedIdentity ? (
            <p className="for-you-saved-identity muted">
              Saved archetype on this device:{" "}
              <strong className="for-you-saved-strong">{storedIdentity.archetype}</strong>
            </p>
          ) : null}

          <form onSubmit={submit} className="for-you-form">
            <label className="for-you-label" htmlFor="for-you-query">
              Your query
            </label>
            <textarea
              id="for-you-query"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Dark story RPG with exploration, or: cozy farming sim on PC…"
              rows={5}
              aria-describedby="for-you-preview"
            />
            <p id="for-you-preview" className="for-you-detected muted">
              {trimmed ? (
                <>
                  Detected:{" "}
                  {likedGenres.length || likedTags.length ? (
                    <>
                      {likedGenres.length > 0 ? <span>genres: {likedGenres.join(", ")}</span> : null}
                      {likedGenres.length > 0 && likedTags.length > 0 ? " · " : null}
                      {likedTags.length > 0 ? <span>tags: {likedTags.join(", ")}</span> : null}
                    </>
                  ) : (
                    <span>using your full text as a search tag</span>
                  )}
                </>
              ) : (
                "Type something to enable recommendations."
              )}
            </p>

            <div className="slider-block">
              <label htmlFor="for-you-style">{styleLabel}</label>
              <input
                id="for-you-style"
                type="range"
                min={0}
                max={100}
                value={style}
                onChange={(event) => setStyle(Number(event.target.value))}
                aria-valuetext={`${style} percent latent`}
              />
              <small>Keywords ↔ Latent similarity</small>
            </div>

            <div className="slider-block">
              <label htmlFor="for-you-niche">{nicheLabel}</label>
              <input
                id="for-you-niche"
                type="range"
                min={0}
                max={100}
                value={niche}
                onChange={(event) => setNiche(Number(event.target.value))}
                aria-valuetext={`popularity floor about ${niche} percent`}
              />
              <small>Mainstream ↔ Niche</small>
            </div>

            <button
              type="submit"
              className="primary-button for-you-submit"
              disabled={!canSubmit || run.isPending}
            >
              {run.isPending ? "Finding games…" : "Recommend now"}
            </button>
          </form>

          {run.isError ? (
            <p className="for-you-inline-error" role="alert">
              {run.error instanceof Error ? run.error.message.slice(0, 200) : "Request failed."} Check the API and
              try again.
            </p>
          ) : null}

          {archetype.data ? (
            <div className="identity-callout">
              <span>This run — you play like</span>
              <strong>
                {[...archetype.data.predictions].sort((a, b) => b.probability - a.probability)[0]?.archetype ??
                  "—"}
              </strong>
            </div>
          ) : null}
          {archetype.isError ? (
            <p className="muted for-you-mini-note">Archetype hint unavailable for this query (non-blocking).</p>
          ) : null}
        </aside>

        <div className="for-you-results">
          <header className="for-you-results-header">
            <div>
              <h2 className="for-you-results-title">Your recommendations</h2>
              {anchorHint ? (
                <p className="muted for-you-query echo">
                  From: <q>{anchorHint}</q>
                </p>
              ) : (
                <p className="muted for-you-query">Run a query to fill this column.</p>
              )}
            </div>
            <span className="for-you-count muted">
              {run.isPending ? "…" : `${recommendations.length} games`}
            </span>
          </header>

          <ExplainPanel
            explain={explain.data ?? null}
            isLoading={explain.isPending}
            error={explainErrorMessage}
            hint={explainHint}
          />

          {run.isPending ? (
            <div className="game-grid dense for-you-grid">
              {Array.from({ length: 8 }).map((_, idx) => (
                <SkeletonCard key={idx} />
              ))}
            </div>
          ) : recommendations.length === 0 ? (
            <div className="for-you-empty">
              <Sparkles className="for-you-empty-icon" size={32} aria-hidden />
              <h3>No picks yet</h3>
              <p className="muted">
                Describe a vibe on the left and submit. Browse the{" "}
                <Link to="/search">catalog</Link> if you prefer keyword search first.
              </p>
            </div>
          ) : (
            <ul className="for-you-card-list">
              {recommendations.map((game) => (
                <li key={game.name} className="for-you-card-item">
                  <GameCard
                    game={game}
                    subtitle={
                      game.score !== undefined ? `Match score ${Math.round(game.score * 100)}%` : "Recommended"
                    }
                  />
                  <button
                    type="button"
                    className={`for-you-why ${picked === game.name ? "is-active" : ""}`}
                    aria-pressed={picked === game.name}
                    onClick={() => onWhyClick(game)}
                  >
                    Why?
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
