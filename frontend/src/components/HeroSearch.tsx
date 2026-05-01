import { Search } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { FormEvent, useState } from "react";

export function HeroSearch() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();

  const onSubmit = (event: FormEvent) => {
    event.preventDefault();
    if (!query.trim()) return;
    navigate(`/search?q=${encodeURIComponent(query.trim())}`);
  };

  return (
    <form onSubmit={onSubmit} className="hero-search">
      <Search size={18} />
      <input
        aria-label="Search games"
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search a game, genre, or mood..."
      />
      <button type="submit">Explore</button>
    </form>
  );
}
