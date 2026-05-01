import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { ArchetypeBadge } from "../components/ArchetypeBadge";
import { ExplainPanel } from "../components/ExplainPanel";
import { GameCard } from "../components/GameCard";
import {
  getArchetypesByTitle,
  getExplain,
  getSimilarRecommendations,
  searchGames,
  type GameViewModel,
} from "../lib/api";
import { compactNumber, rating as formatRating } from "../lib/format";

const POPULARITY_SCALE = 5;

function popularityBarPercent(value: number): number {
  if (value <= 0) return 0;
  const linear = (value / POPULARITY_SCALE) * 100;
  return Math.max(4, Math.min(100, Math.round(linear)));
}

export function GamePage() {
  const params = useParams();
  const gameName = decodeURIComponent(params.name ?? "");
  const [selectedName, setSelectedName] = useState<string | null>(null);
  const [selectedGame, setSelectedGame] = useState<GameViewModel | null>(null);

  const anchorGame = useQuery({
    queryKey: ["anchor-game", gameName],
    queryFn: async () => {
      const res = await searchGames(gameName, 1);
      return res[0] ?? null;
    },
    enabled: gameName.length > 0,
  });

  const recommendations = useQuery({
    queryKey: ["similar", gameName],
    queryFn: () => getSimilarRecommendations({ game_name: gameName, n: 10 }),
    enabled: gameName.length > 0,
  });

  const archetypes = useQuery({
    queryKey: ["archetypes", gameName],
    queryFn: () => getArchetypesByTitle(gameName),
    enabled: gameName.length > 0,
  });

  const explain = useMutation({
    mutationFn: ({ anchor, recommended }: { anchor: string; recommended: string }) =>
      getExplain(anchor, recommended),
  });

  const topPicks = useMemo(() => recommendations.data ?? [], [recommendations.data]);
  const g = anchorGame.data;
  const displayName = g?.name ?? gameName;
  const popScore = g?.popularity ?? 0;
  const popFill = popularityBarPercent(popScore);
  const popularityPrior = selectedGame
    ? Math.max(0.05, Math.min(1, selectedGame.popularity / Math.max(1, g?.popularity ?? 1)))
    : 0;

  return (
    <div className="page game-detail-page">
      <section className="section game-hero game-hero--detail">
        <div className="game-hero__media">
          <img src={g?.imageUrl} alt="" className="hero-cover hero-cover--detail" />
          <div className="game-hero__media-links">
            {g?.steamAppId != null ? (
              <a
                className="game-external-link"
                href={`https://store.steampowered.com/app/${g.steamAppId}`}
                target="_blank"
                rel="noreferrer"
              >
                Steam
              </a>
            ) : null}
            {g?.rawgSlug ? (
              <a
                className="game-external-link"
                href={`https://rawg.io/games/${g.rawgSlug}`}
                target="_blank"
                rel="noreferrer"
              >
                RAWG
              </a>
            ) : null}
          </div>
        </div>
        <div className="game-hero__body">
          <h1 className="game-detail-title">{displayName}</h1>
          <p className="muted game-detail-lead">Who this game fits, and what to play next.</p>

          <dl className="game-stat-strip">
            <div className="game-stat-strip__item">
              <dt>User rating</dt>
              <dd>{g?.rating != null ? formatRating(g.rating) : "—"}</dd>
            </div>
            <div className="game-stat-strip__item">
              <dt>Metacritic</dt>
              <dd>{g?.metacritic != null ? g.metacritic : "—"}</dd>
            </div>
            <div className="game-stat-strip__item">
              <dt>Reviews</dt>
              <dd>{g?.votes != null ? compactNumber(g.votes) : "—"}</dd>
            </div>
            <div className="game-stat-strip__item">
              <dt>Cluster</dt>
              <dd>{g?.clusterId != null ? `#${g.clusterId}` : "—"}</dd>
            </div>
            <div className="game-stat-strip__item game-stat-strip__item--wide">
              <dt>Released</dt>
              <dd className="game-stat-strip__releases">
                {g?.releasedSteam ? <span title="Steam">Steam: {g.releasedSteam}</span> : null}
                {g?.releasedRawg ? <span title="RAWG">RAWG: {g.releasedRawg}</span> : null}
                {!g?.releasedSteam && !g?.releasedRawg ? "—" : null}
              </dd>
            </div>
          </dl>

          <div className="popularity-meter" aria-label="Popularity score">
            <div className="popularity-meter__head">
              <span className="popularity-meter__label">Popularity index</span>
              <span className="popularity-meter__value">{popScore.toFixed(2)}</span>
              <span className="popularity-meter__scale">/ {POPULARITY_SCALE}</span>
            </div>
            <div className="popularity-meter__track">
              <div className="popularity-meter__fill" style={{ width: `${popFill}%` }} />
            </div>
            <p className="popularity-meter__hint muted">
              Bayesian-smoothed blend of ratings and review volume (same 0–5 style scale as stars).
            </p>
          </div>

          <div className="game-detail-chips">
            <div>
              <h3 className="game-detail-chips__heading">Genres</h3>
              <div className="chip-row">
                {(g?.genres ?? []).slice(0, 8).map((genre) => (
                  <span className="chip" key={genre}>
                    {genre}
                  </span>
                ))}
                {(g?.genres?.length ?? 0) === 0 ? <span className="muted">—</span> : null}
              </div>
            </div>
            <div>
              <h3 className="game-detail-chips__heading">Platforms</h3>
              <div className="chip-row">
                {(g?.platforms ?? []).slice(0, 10).map((p) => (
                  <span className="chip chip--outline" key={p}>
                    {p}
                  </span>
                ))}
                {(g?.platforms?.length ?? 0) === 0 ? <span className="muted">—</span> : null}
              </div>
            </div>
            {(g?.tags?.length ?? 0) > 0 ? (
              <div>
                <h3 className="game-detail-chips__heading">Tags</h3>
                <div className="chip-row game-detail-chips__wrap">
                  {g!.tags!.map((tag) => (
                    <span className="chip chip--tag" key={tag}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
            {(g?.categories?.length ?? 0) > 0 ? (
              <div>
                <h3 className="game-detail-chips__heading">Steam features</h3>
                <div className="chip-row game-detail-chips__wrap">
                  {g!.categories!.map((cat) => (
                    <span className="chip chip--subtle" key={cat}>
                      {cat}
                    </span>
                  ))}
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </section>

      <section className="section split game-detail-split">
        <div className="panel game-archetype-panel">
          <h3>Player archetypes</h3>
          <p className="muted">Estimated from game metadata — stronger bars are a closer match.</p>
          <div className="archetype-grid archetype-grid--cards">
            {(archetypes.data?.predictions ?? []).map((item) => (
              <ArchetypeBadge item={item} key={item.archetype} />
            ))}
          </div>
        </div>
        <ExplainPanel explain={explain.data ?? null} popularityPrior={popularityPrior} />
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Recommended for {displayName}</h2>
        </div>
        <div className="game-grid">
          {topPicks.map((game) => (
            <div key={game.name}>
              <GameCard
                game={game}
                subtitle={
                  game.score !== undefined ? `${Math.round(game.score * 100)}% match` : "Recommended"
                }
              />
              <button
                className={`text-link ${selectedName === game.name ? "active" : ""}`}
                type="button"
                onClick={() => {
                  setSelectedName(game.name);
                  setSelectedGame(game);
                  explain.mutate({ anchor: gameName, recommended: game.name });
                }}
              >
                Why this game?
              </button>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
