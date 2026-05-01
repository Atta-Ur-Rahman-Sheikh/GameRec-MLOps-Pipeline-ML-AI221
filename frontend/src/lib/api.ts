import type {
  ClusterCard,
  ClusterMapResponse,
  DiscoverRowsResponse,
  ExplainResponse,
  GameSearchHit,
  PlayerTypeResponse,
  RecommendationItem,
  RecommendationResponse,
  SeasonalityResponse,
} from "../types/api";
import { imageFallbackForTitle } from "./mockImage";

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
const API_BASE_CANDIDATES = Array.from(
  new Set([
    API_BASE,
    "http://localhost:8000",
    "http://127.0.0.1:8001",
    "http://localhost:8001",
  ])
);

export type GameViewModel = {
  name: string;
  rating: number | null;
  popularity: number;
  genres: string[];
  platforms: string[];
  tags: string[];
  categories: string[];
  score?: number;
  lsa?: number;
  text?: number;
  imageUrl: string;
  rawgSlug?: string;
  releasedRawg?: string;
  releasedSteam?: string;
  metacritic?: number;
  votes?: number;
  clusterId?: number;
  steamAppId?: number;
};

export type DiscoverRowsViewModel = {
  trendingReleases: GameViewModel[];
  topRatedPopularity: GameViewModel[];
  hiddenGems: GameViewModel[];
};

type RequestOptions = {
  method?: "GET" | "POST";
  body?: unknown;
};

async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const method = options.method ?? "GET";
  let lastError: Error | null = null;

  for (const base of API_BASE_CANDIDATES) {
    try {
      const response = await fetch(`${base}${path}`, {
        method,
        headers: {
          "Content-Type": "application/json",
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
      });

      if (!response.ok) {
        const text = await response.text();
        lastError = new Error(text || `Request failed with status ${response.status}`);
        continue;
      }

      return (await response.json()) as T;
    } catch (err) {
      lastError = err instanceof Error ? err : new Error(String(err));
    }
  }

  throw (
    lastError ??
    new Error(
      "Unable to reach the backend API. Make sure FastAPI is running and VITE_API_BASE_URL is correct."
    )
  );
}

export function normalizeGame(input: GameSearchHit | RecommendationItem): GameViewModel {
  const remoteImage = "image_url" in input && input.image_url ? input.image_url : null;
  return {
    name: input.name,
    rating: "rating" in input ? input.rating : null,
    popularity: input.popularity ?? 0,
    genres: input.genres ?? [],
    platforms: input.platforms ?? [],
    tags: "tags" in input && input.tags ? input.tags : [],
    categories: "categories" in input && input.categories ? input.categories : [],
    score: "score" in input ? input.score : undefined,
    lsa: "lsa_sim" in input ? input.lsa_sim : undefined,
    text: "txt_sim" in input ? input.txt_sim : undefined,
    imageUrl: remoteImage ?? imageFallbackForTitle(input.name),
    rawgSlug: "rawg_slug" in input && input.rawg_slug ? input.rawg_slug : undefined,
    releasedRawg: "released_rawg" in input ? input.released_rawg ?? undefined : undefined,
    releasedSteam: "released_steam" in input ? input.released_steam ?? undefined : undefined,
    metacritic: "metacritic" in input ? input.metacritic ?? undefined : undefined,
    votes: "votes" in input && input.votes != null ? input.votes : undefined,
    clusterId: "cluster_id" in input && input.cluster_id != null ? input.cluster_id : undefined,
    steamAppId: "steam_app_id" in input && input.steam_app_id != null ? input.steam_app_id : undefined,
  };
}

export async function searchGames(query: string, limit = 20): Promise<GameViewModel[]> {
  const result = await request<GameSearchHit[]>(
    `/games/search?q=${encodeURIComponent(query)}&limit=${limit}`
  );
  return result.map(normalizeGame);
}

export async function getClusters(): Promise<ClusterCard[]> {
  return request<ClusterCard[]>("/discover/clusters");
}

export async function getClusterMap(): Promise<ClusterMapResponse> {
  return request<ClusterMapResponse>("/discover/cluster-map");
}

export async function getDiscoverRows(limit = 12): Promise<DiscoverRowsViewModel> {
  const rows = await request<DiscoverRowsResponse>(`/games/discover?limit=${limit}`);
  return {
    trendingReleases: rows.trending_releases.map(normalizeGame),
    topRatedPopularity: rows.top_rated_popularity.map(normalizeGame),
    hiddenGems: rows.hidden_gems.map(normalizeGame),
  };
}

export async function getSimilarRecommendations(payload: {
  game_name: string;
  n?: number;
  w_lsa?: number;
  w_text?: number;
  w_pop?: number;
  min_pop?: number | null;
}): Promise<GameViewModel[]> {
  const result = await request<RecommendationResponse>("/recommend/similar", {
    method: "POST",
    body: payload,
  });
  return result.items.map(normalizeGame);
}

export async function getUserRecommendations(payload: {
  liked_genres: string[];
  liked_tags: string[];
  platforms: string[];
  n?: number;
  min_pop_quantile?: number;
  min_rating?: number;
  w_lsa?: number;
  w_text?: number;
  w_pop?: number;
  use_content_richness?: boolean;
}): Promise<GameViewModel[]> {
  const result = await request<RecommendationResponse>("/recommend/user", {
    method: "POST",
    body: payload,
  });
  return result.items.map(normalizeGame);
}

export async function getArchetypesByTitle(gameName: string): Promise<PlayerTypeResponse> {
  return request<PlayerTypeResponse>("/predict/player-type/by-title", {
    method: "POST",
    body: {
      game_name: gameName,
      top_k: 4,
      threshold: 0.4,
    },
  });
}

export async function getArchetypesByQuery(payload: {
  liked_genres: string[];
  liked_tags: string[];
  top_k?: number;
  threshold?: number;
}): Promise<PlayerTypeResponse> {
  return request<PlayerTypeResponse>("/predict/player-type/by-query", {
    method: "POST",
    body: {
      top_k: 4,
      threshold: 0.4,
      ...payload,
    },
  });
}

export async function getExplain(anchor: string, recommended: string): Promise<ExplainResponse> {
  return request<ExplainResponse>("/recommend/explain", {
    method: "POST",
    body: {
      anchor,
      recommended,
      top_k_tokens: 8,
    },
  });
}

export async function getSeasonalityThemes(): Promise<string[]> {
  return request<string[]>("/seasonality/themes");
}

export async function getSeasonalityTheme(theme: string): Promise<SeasonalityResponse> {
  return request<SeasonalityResponse>(`/seasonality/${encodeURIComponent(theme)}`);
}
