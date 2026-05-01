import { useQuery } from "@tanstack/react-query";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { searchGames } from "../lib/api";
import { normalizeNameForPath } from "../lib/format";

export function TopSearchBar() {
  const [query, setQuery] = useState("");
  const [focused, setFocused] = useState(false);
  const navigate = useNavigate();

  const trimmed = query.trim();
  const active = trimmed.length > 1;

  const auto = useQuery({
    queryKey: ["top-search", trimmed],
    queryFn: () => searchGames(trimmed, 6),
    enabled: active,
  });

  const showDropdown = focused && active;

  const onSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!trimmed) return;
    navigate(`/search?q=${encodeURIComponent(trimmed)}`);
    setFocused(false);
  };

  const results = useMemo(() => auto.data ?? [], [auto.data]);

  return (
    <form className="top-search" onSubmit={onSubmit}>
      <Search size={16} />
      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search games..."
        onFocus={() => setFocused(true)}
        onBlur={() => setTimeout(() => setFocused(false), 120)}
      />
      {showDropdown ? (
        <div className="search-dropdown">
          {results.length ? (
            results.map((game) => (
              <Link
                className="search-item"
                to={`/game/${normalizeNameForPath(game.name)}`}
                key={game.name}
              >
                <img src={game.imageUrl} alt={game.name} />
                <div>
                  <strong>{game.name}</strong>
                  <span>{game.genres.slice(0, 2).join(" · ") || "Game"}</span>
                </div>
              </Link>
            ))
          ) : (
            <div className="search-empty">No matching games</div>
          )}
        </div>
      ) : null}
    </form>
  );
}
