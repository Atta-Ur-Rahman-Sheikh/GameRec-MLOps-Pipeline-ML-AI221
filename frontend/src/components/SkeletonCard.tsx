export function SkeletonCard() {
  return (
    <article className="game-card skeleton">
      <div className="skeleton-image" />
      <div className="game-body">
        <div className="skeleton-line short" />
        <div className="skeleton-line long" />
        <div className="skeleton-line medium" />
      </div>
    </article>
  );
}
