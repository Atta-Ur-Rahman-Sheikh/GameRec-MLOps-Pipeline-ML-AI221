export type GameSearchHit = {
  name: string;
  popularity: number;
  rating: number | null;
  genres: string[];
  platforms?: string[];
  tags?: string[];
  categories?: string[];
  score?: number;
  image_url?: string | null;
  rawg_slug?: string | null;
  released_rawg?: string | null;
  released_steam?: string | null;
  metacritic?: number | null;
  votes?: number | null;
  cluster_id?: number | null;
  steam_app_id?: number | null;
};

export type RecommendationItem = {
  name: string;
  score: number;
  lsa_sim: number;
  txt_sim: number;
  rating: number;
  popularity: number;
  genres?: string[];
  platforms?: string[];
  tags?: string[];
  categories?: string[];
  image_url?: string | null;
  rawg_slug?: string | null;
  released_rawg?: string | null;
  released_steam?: string | null;
  metacritic?: number | null;
  votes?: number | null;
  cluster_id?: number | null;
  steam_app_id?: number | null;
};

export type RecommendationResponse = {
  anchor?: string | null;
  query?: Record<string, unknown> | null;
  items: RecommendationItem[];
};

export type DiscoverRowsResponse = {
  trending_releases: GameSearchHit[];
  top_rated_popularity: GameSearchHit[];
  hidden_gems: GameSearchHit[];
};

export type PlayerTypePrediction = {
  archetype: string;
  probability: number;
  predicted: boolean;
};

export type PlayerTypeResponse = {
  predictions: PlayerTypePrediction[];
};

export type DistinctiveTag = {
  tag: string;
  lift: number;
  count: number;
};

export type ClusterCard = {
  cluster_id: number;
  auto_name: string;
  size: number;
  avg_popularity: number;
  top_genres: string[];
  distinctive_tags: DistinctiveTag[];
  examples: string[];
};

export type ClusterMapPoint = {
  name: string;
  cluster_id: number;
  x: number;
  y: number;
  popularity: number;
};

export type ClusterMapCentroid = {
  cluster_id: number;
  label: string;
  x: number;
  y: number;
  n_games: number;
};

export type ClusterMapResponse = {
  method: string;
  explained_variance_ratio: [number, number];
  points: ClusterMapPoint[];
  centroids: ClusterMapCentroid[];
};

export type ExplainResponse = {
  anchor: string;
  recommended: string;
  lsa_sim: number;
  txt_sim: number;
  shared_genres: string[];
  shared_tags: string[];
  top_terms: [string, number][];
};

export type SeasonalityResponse = {
  theme: string;
  n_games: number;
  month_names: string[];
  monthly_avg: number[];
  seasonal_index: number[];
  peak_month?: string | null;
  peak_index_value?: number | null;
  forecast?: Record<string, unknown> | null;
};
