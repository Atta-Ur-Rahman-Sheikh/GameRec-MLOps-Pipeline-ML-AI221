import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Plus } from "lucide-react";
import type { GameViewModel } from "../lib/api";
import { normalizeNameForPath } from "../lib/format";
import { PlatformIcons } from "./PlatformIcons";

type GameCardProps = {
  game: GameViewModel;
  subtitle?: string;
};

export function GameCard({ game, subtitle }: GameCardProps) {
  const score = game.rating ? Math.round(Math.max(0, Math.min(5, game.rating)) * 20) : null;
  const scoreClass = score === null ? "na" : score >= 75 ? "good" : score >= 55 ? "mid" : "bad";
  const detailPath = `/game/${normalizeNameForPath(game.name)}`;

  return (
    <motion.article
      className="game-card"
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 230, damping: 20 }}
    >
      <Link to={detailPath} className="game-card-tile-link" aria-label={`Open ${game.name} details`} />
      <div className="game-image-wrap">
        <img src={game.imageUrl} alt="" className="game-image" loading="lazy" />
        <button
          type="button"
          className="quick-add"
          aria-label={`Quick add ${game.name}`}
          onClick={(event) => {
            event.preventDefault();
            event.stopPropagation();
          }}
        >
          <Plus size={14} />
        </button>
      </div>
      <div className="game-body">
        <div className="game-topline">
          <h3>{game.name}</h3>
          <span className={`score-badge ${scoreClass}`}>{score ?? "N/A"}</span>
        </div>
        <PlatformIcons platforms={game.platforms} />
        {subtitle ? <p className="subtitle">{subtitle}</p> : null}
        <div className="chip-row">
          {game.genres.slice(0, 3).map((genre) => (
            <button
              key={genre}
              className="chip tag-button"
              type="button"
              onClick={(event) => {
                event.preventDefault();
                event.stopPropagation();
              }}
            >
              {genre}
            </button>
          ))}
        </div>
      </div>
    </motion.article>
  );
}
