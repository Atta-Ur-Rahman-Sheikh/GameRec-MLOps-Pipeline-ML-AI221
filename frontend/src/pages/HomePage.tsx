import { useQuery } from "@tanstack/react-query";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useRef } from "react";
import { Link } from "react-router-dom";
import { HeroSearch } from "../components/HeroSearch";
import { GameCard } from "../components/GameCard";
import { SkeletonCard } from "../components/SkeletonCard";
import { getDiscoverRows } from "../lib/api";

export function HomePage() {
  const trendingRef = useRef<HTMLDivElement>(null);
  const topRatedRef = useRef<HTMLDivElement>(null);
  const hiddenGemsRef = useRef<HTMLDivElement>(null);

  const discover = useQuery({
    queryKey: ["discover-rows"],
    queryFn: () => getDiscoverRows(12),
  });
  const discoverError =
    discover.error instanceof Error
      ? discover.error.message
      : "Unable to load home discovery rows right now.";

  const scrollRow = (target: { current: HTMLDivElement | null }, direction: "left" | "right") => {
    const node = target.current;
    if (!node) return;
    const delta = direction === "left" ? -360 : 360;
    node.scrollBy({ left: delta, behavior: "smooth" });
  };

  return (
    <div className="page">
      <section className="hero">
        <div>
          <p className="kicker">GameRec ML Recommender</p>
          <h1>What do you want to play?</h1>
          <p className="hero-copy">
            Describe your vibe in natural language. We translate it into recommendations and explain
            exactly why each game fits.
          </p>
          <HeroSearch />
        </div>
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Trending releases</h2>
          <Link to="/for-you">Personalize</Link>
        </div>
        {discover.isError ? <p className="muted">{discoverError}</p> : null}
        <div className="row-carousel">
          <button
            type="button"
            className="carousel-nav"
            aria-label="Scroll trending releases left"
            onClick={() => scrollRow(trendingRef, "left")}
          >
            <ChevronLeft size={16} />
          </button>
          <div className="game-row-scroll" role="region" aria-label="Trending releases" ref={trendingRef}>
            {discover.isLoading
              ? Array.from({ length: 8 }).map((_, idx) => (
                  <div className="row-card" key={idx}>
                    <SkeletonCard />
                  </div>
                ))
              : (discover.data?.trendingReleases ?? []).map((game) => (
                  <div className="row-card" key={game.name}>
                    <GameCard game={game} />
                  </div>
                ))}
          </div>
          <button
            type="button"
            className="carousel-nav"
            aria-label="Scroll trending releases right"
            onClick={() => scrollRow(trendingRef, "right")}
          >
            <ChevronRight size={16} />
          </button>
        </div>
        {!discover.isLoading &&
        !discover.isError &&
        (discover.data?.trendingReleases?.length ?? 0) === 0 ? (
          <p className="muted">No trending releases found from the current dataset.</p>
        ) : null}
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Top-rated by popularity model</h2>
          <Link to="/search">Browse all</Link>
        </div>
        <div className="row-carousel">
          <button
            type="button"
            className="carousel-nav"
            aria-label="Scroll top-rated row left"
            onClick={() => scrollRow(topRatedRef, "left")}
          >
            <ChevronLeft size={16} />
          </button>
          <div
            className="game-row-scroll"
            role="region"
            aria-label="Top-rated by popularity model"
            ref={topRatedRef}
          >
            {discover.isLoading
              ? Array.from({ length: 8 }).map((_, idx) => (
                  <div className="row-card" key={idx}>
                    <SkeletonCard />
                  </div>
                ))
              : (discover.data?.topRatedPopularity ?? []).map((game) => (
                  <div className="row-card" key={game.name}>
                    <GameCard game={game} />
                  </div>
                ))}
          </div>
          <button
            type="button"
            className="carousel-nav"
            aria-label="Scroll top-rated row right"
            onClick={() => scrollRow(topRatedRef, "right")}
          >
            <ChevronRight size={16} />
          </button>
        </div>
        {!discover.isLoading &&
        !discover.isError &&
        (discover.data?.topRatedPopularity?.length ?? 0) === 0 ? (
          <p className="muted">No top-rated recommendations are available yet.</p>
        ) : null}
      </section>

      <section className="section">
        <div className="section-head">
          <h2>Hidden gems</h2>
          <Link to="/explore">Explore clusters</Link>
        </div>
        <div className="row-carousel">
          <button
            type="button"
            className="carousel-nav"
            aria-label="Scroll hidden gems left"
            onClick={() => scrollRow(hiddenGemsRef, "left")}
          >
            <ChevronLeft size={16} />
          </button>
          <div className="game-row-scroll" role="region" aria-label="Hidden gems" ref={hiddenGemsRef}>
            {discover.isLoading
              ? Array.from({ length: 8 }).map((_, idx) => (
                  <div className="row-card" key={idx}>
                    <SkeletonCard />
                  </div>
                ))
              : (discover.data?.hiddenGems ?? []).map((game) => (
                  <div className="row-card" key={game.name}>
                    <GameCard game={game} subtitle="Low-known, high-fit" />
                  </div>
                ))}
          </div>
          <button
            type="button"
            className="carousel-nav"
            aria-label="Scroll hidden gems right"
            onClick={() => scrollRow(hiddenGemsRef, "right")}
          >
            <ChevronRight size={16} />
          </button>
        </div>
        {!discover.isLoading && !discover.isError && (discover.data?.hiddenGems?.length ?? 0) === 0 ? (
          <p className="muted">No hidden gems were found for this dataset snapshot.</p>
        ) : null}
      </section>
    </div>
  );
}
