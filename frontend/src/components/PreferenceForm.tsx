import { FormEvent, useMemo, useState } from "react";

type PreferencePayload = {
  liked_genres: string[];
  liked_tags: string[];
  platforms: string[];
  min_rating: number;
};

const GENRES = [
  "Action",
  "RPG",
  "Adventure",
  "Indie",
  "Strategy",
  "Simulation",
  "Racing",
  "Sports",
];

const TAGS = ["Co-op", "Horror", "Story Rich", "Open World", "PVP", "Roguelike", "Survival"];
const PLATFORMS = ["Windows", "Linux", "Mac", "PlayStation", "Xbox", "Nintendo Switch"];

export function PreferenceForm({ onSubmit }: { onSubmit: (payload: PreferencePayload) => void }) {
  const [genres, setGenres] = useState<string[]>(["Action"]);
  const [tags, setTags] = useState<string[]>(["Story Rich"]);
  const [platforms, setPlatforms] = useState<string[]>(["Windows"]);
  const [minRating, setMinRating] = useState(3.5);

  const canSubmit = useMemo(() => genres.length > 0 || tags.length > 0, [genres, tags]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (!canSubmit) return;
    onSubmit({
      liked_genres: genres,
      liked_tags: tags,
      platforms,
      min_rating: minRating,
    });
  };

  return (
    <form className="panel preference-form" onSubmit={submit}>
      <h3>Your recommendation profile</h3>
      <Field title="Genres" all={GENRES} value={genres} onChange={setGenres} />
      <Field title="Tags" all={TAGS} value={tags} onChange={setTags} />
      <Field title="Platforms" all={PLATFORMS} value={platforms} onChange={setPlatforms} />
      <label className="slider">
        <span>Minimum rating: {minRating.toFixed(1)}</span>
        <input
          type="range"
          min={0}
          max={5}
          step={0.1}
          value={minRating}
          onChange={(event) => setMinRating(Number(event.target.value))}
        />
      </label>
      <button type="submit" disabled={!canSubmit}>
        Generate for me
      </button>
    </form>
  );
}

function Field({
  title,
  all,
  value,
  onChange,
}: {
  title: string;
  all: string[];
  value: string[];
  onChange: (value: string[]) => void;
}) {
  const toggle = (item: string) => {
    if (value.includes(item)) {
      onChange(value.filter((v) => v !== item));
    } else {
      onChange([...value, item]);
    }
  };

  return (
    <div className="field">
      <h4>{title}</h4>
      <div className="chip-row">
        {all.map((item) => (
          <button
            type="button"
            key={item}
            className={`chip-toggle ${value.includes(item) ? "on" : ""}`}
            onClick={() => toggle(item)}
          >
            {item}
          </button>
        ))}
      </div>
    </div>
  );
}
