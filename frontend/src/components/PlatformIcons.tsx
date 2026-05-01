import { Gamepad2, Monitor, Trophy } from "lucide-react";

function normalizePlatformLabel(platform: string): "pc" | "ps" | "xbox" | "switch" | "other" {
  const p = platform.toLowerCase();
  if (p.includes("pc") || p.includes("windows") || p.includes("linux") || p.includes("mac")) {
    return "pc";
  }
  if (p.includes("playstation") || p.includes("ps")) {
    return "ps";
  }
  if (p.includes("xbox")) {
    return "xbox";
  }
  if (p.includes("switch") || p.includes("nintendo")) {
    return "switch";
  }
  return "other";
}

function platformToken(platform: string): string {
  const kind = normalizePlatformLabel(platform);
  if (kind === "pc") return "PC";
  if (kind === "ps") return "PS";
  if (kind === "xbox") return "XB";
  if (kind === "switch") return "NS";
  return "OT";
}

function platformIcon(platform: string) {
  const kind = normalizePlatformLabel(platform);
  if (kind === "pc") return <Monitor size={12} />;
  if (kind === "ps") return <Gamepad2 size={12} />;
  if (kind === "xbox") return <Gamepad2 size={12} />;
  if (kind === "switch") return <Gamepad2 size={12} />;
  return <Trophy size={12} />;
}

export function PlatformIcons({ platforms }: { platforms: string[] }) {
  return (
    <div className="platform-row" aria-label="Supported platforms">
      {platforms.slice(0, 4).map((platform) => (
        <span className="platform-icon" key={platform} title={platform}>
          {platformIcon(platform)}
          <span>{platformToken(platform)}</span>
        </span>
      ))}
    </div>
  );
}
