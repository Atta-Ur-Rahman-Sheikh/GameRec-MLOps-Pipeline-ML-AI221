import { Compass, Crown, Shield, Swords } from "lucide-react";
import type { PlayerTypePrediction } from "../types/api";
import { percent } from "../lib/format";
import type { ReactNode } from "react";

const iconByArchetype: Record<string, ReactNode> = {
  explorer: <Compass size={16} strokeWidth={2} />,
  achiever: <Crown size={16} strokeWidth={2} />,
  socializer: <Shield size={16} strokeWidth={2} />,
  competitor: <Swords size={16} strokeWidth={2} />,
};

function iconFor(name: string) {
  const key = name.toLowerCase();
  if (key.includes("explor")) return iconByArchetype.explorer;
  if (key.includes("achiev")) return iconByArchetype.achiever;
  if (key.includes("social")) return iconByArchetype.socializer;
  if (key.includes("compet")) return iconByArchetype.competitor;
  return <Shield size={16} strokeWidth={2} />;
}

export function ArchetypeBadge({ item }: { item: PlayerTypePrediction }) {
  const widthPct = Math.max(2, Math.round(item.probability * 100));
  return (
    <div className={`archetype-card ${item.predicted ? "archetype-card--active" : ""}`}>
      <div className="archetype-card__top">
        <span className="archetype-card__icon" aria-hidden>
          {iconFor(item.archetype)}
        </span>
        <span className="archetype-card__name">{item.archetype}</span>
        <span className="archetype-card__value">{percent(item.probability)}</span>
      </div>
      <div className="archetype-card__track" role="presentation">
        <div className="archetype-card__fill" style={{ width: `${widthPct}%` }} />
      </div>
    </div>
  );
}
