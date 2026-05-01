import { useEffect, useMemo, useState } from "react";
import { useQueries, useQuery } from "@tanstack/react-query";
import { CalendarDays, ChartColumnIncreasing, Flame } from "lucide-react";
import { getSeasonalityTheme, getSeasonalityThemes } from "../lib/api";
import { messageFromFetchError } from "../lib/apiErrors";
import type { SeasonalityResponse } from "../types/api";

function toPath(values: number[], yMin = 0, yMax = 100): string {
  if (!values.length) return "";
  const norm = values.map((v, i) => {
    const x = (i / (values.length - 1 || 1)) * 100;
    const y = yMax - ((v - yMin) / (yMax - yMin + 1e-9)) * (yMax - 16);
    return `${x},${y}`;
  });
  return `M ${norm.join(" L ")}`;
}

function monthList(row: SeasonalityResponse | undefined): string[] {
  if (row?.month_names?.length === 12) return row.month_names;
  return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
}

function heatTone(value: number): string {
  const t = Math.max(0, Math.min(1, value / 2.2));
  const light = 16 + t * 54;
  return `hsl(46 88% ${light}%)`;
}

export function TrendsPage() {
  const themes = useQuery({
    queryKey: ["themes"],
    queryFn: getSeasonalityThemes,
  });

  const [activeTheme, setActiveTheme] = useState<string>("");
  const [hoverMonthIdx, setHoverMonthIdx] = useState<number | null>(null);
  const themeList = themes.data ?? [];

  useEffect(() => {
    if (!activeTheme && themeList.length) {
      setActiveTheme(themeList[0]);
    }
  }, [activeTheme, themeList]);

  const activeThemeQuery = useQuery({
    queryKey: ["theme", activeTheme],
    queryFn: () => getSeasonalityTheme(activeTheme),
    enabled: Boolean(activeTheme),
  });

  const overviewThemes = useMemo(() => themeList.slice(0, 6), [themeList]);

  const overviewQueries = useQueries({
    queries: overviewThemes.map((theme) => ({
      queryKey: ["theme", theme],
      queryFn: () => getSeasonalityTheme(theme),
      enabled: !!theme,
    })),
  });

  const rows = useMemo(
    () => overviewQueries.map((q) => q.data).filter(Boolean) as SeasonalityResponse[],
    [overviewQueries]
  );
  const active = activeThemeQuery.data;
  const months = monthList(active);
  const activeMonth = hoverMonthIdx ?? 0;

  const bestMonth = useMemo(() => {
    if (!active?.seasonal_index?.length) return null;
    let bestIdx = 0;
    for (let i = 1; i < active.seasonal_index.length; i += 1) {
      if (active.seasonal_index[i] > active.seasonal_index[bestIdx]) bestIdx = i;
    }
    return { idx: bestIdx, value: active.seasonal_index[bestIdx] };
  }, [active]);

  const weakestMonth = useMemo(() => {
    if (!active?.seasonal_index?.length) return null;
    let weakIdx = 0;
    for (let i = 1; i < active.seasonal_index.length; i += 1) {
      if (active.seasonal_index[i] < active.seasonal_index[weakIdx]) weakIdx = i;
    }
    return { idx: weakIdx, value: active.seasonal_index[weakIdx] };
  }, [active]);

  const activeError = activeThemeQuery.isError ? messageFromFetchError(activeThemeQuery.error) : null;
  const chartMax = Math.max(...(active?.monthly_avg ?? [1]), 1);
  const linePath = toPath(active?.seasonal_index ?? [], 0, Math.max(...(active?.seasonal_index ?? [1]), 1.8));

  return (
    <div className="page trend-page">
      <section className="section trend-hero">
        <h1>Release Trends</h1>
        <p className="muted">
          Track when each theme tends to launch strongest, then compare monthly release shape and
          seasonality index side-by-side.
        </p>
      </section>

      <section className="section trend-layout">
        <div className="panel trend-controls-panel">
          <h3>Theme picker</h3>
          <p className="muted">Choose a theme to inspect release cadence and seasonality behavior.</p>
          <div className="trend-theme-list">
            {themes.isLoading ? (
              <p className="muted">Loading themes...</p>
            ) : null}
            {themes.isError ? (
              <p className="muted">{messageFromFetchError(themes.error)}</p>
            ) : null}
            {themeList.map((theme) => (
              <button
                key={theme}
                type="button"
                className={`trend-theme-chip ${activeTheme === theme ? "is-active" : ""}`}
                onClick={() => {
                  setActiveTheme(theme);
                  setHoverMonthIdx(null);
                }}
              >
                {theme}
              </button>
            ))}
          </div>
        </div>

        <div className="panel trend-primary">
          <div className="trend-primary-head">
            <h3>{activeTheme || "Pick a theme"}</h3>
            {active?.window ? (
              <span className="muted">
                Window: {active.window.year_min} to {active.window.year_max}
              </span>
            ) : null}
          </div>

          {activeThemeQuery.isLoading ? <p className="muted">Loading trend details...</p> : null}
          {activeError ? <p className="muted">{activeError}</p> : null}

          {active ? (
            <>
              <div className="trend-stat-grid">
                <article className="trend-stat">
                  <CalendarDays size={16} />
                  <div>
                    <span className="muted">Peak month</span>
                    <strong>{bestMonth ? months[bestMonth.idx] : "N/A"}</strong>
                  </div>
                </article>
                <article className="trend-stat">
                  <Flame size={16} />
                  <div>
                    <span className="muted">Peak index</span>
                    <strong>{bestMonth ? bestMonth.value.toFixed(2) : "N/A"}</strong>
                  </div>
                </article>
                <article className="trend-stat">
                  <ChartColumnIncreasing size={16} />
                  <div>
                    <span className="muted">Samples</span>
                    <strong>{active.n_games.toLocaleString()} games</strong>
                  </div>
                </article>
              </div>

              <div className="trend-month-chart">
                {(active.monthly_avg ?? []).map((v, idx) => (
                  <button
                    key={`${active.theme}-bar-${idx}`}
                    type="button"
                    className={`trend-month-bar ${activeMonth === idx ? "is-active" : ""}`}
                    style={{ height: `${16 + (v / (chartMax + 1e-9)) * 84}%` }}
                    onMouseEnter={() => setHoverMonthIdx(idx)}
                    onFocus={() => setHoverMonthIdx(idx)}
                    onClick={() => setHoverMonthIdx(idx)}
                    title={`${months[idx]}: ${v.toFixed(0)} releases`}
                  />
                ))}
              </div>

              <div className="trend-month-labels">
                {months.map((m, idx) => (
                  <button
                    key={`${active.theme}-label-${m}`}
                    type="button"
                    className={`trend-month-label ${idx === activeMonth ? "is-active" : ""}`}
                    onMouseEnter={() => setHoverMonthIdx(idx)}
                    onFocus={() => setHoverMonthIdx(idx)}
                    onClick={() => setHoverMonthIdx(idx)}
                  >
                    {m}
                  </button>
                ))}
              </div>

              <div className="trend-line-card">
                <svg viewBox="0 0 100 100" role="img" aria-label="Seasonality index line">
                  <path d={linePath} className="trend-line trend-line-focus" />
                </svg>
                <p className="muted">
                  {months[activeMonth]}: {active.monthly_avg?.[activeMonth]?.toFixed(0) ?? "0"} releases, seasonal
                  index {active.seasonal_index?.[activeMonth]?.toFixed(2) ?? "0.00"}
                </p>
              </div>
            </>
          ) : null}
        </div>
      </section>

      <section className="section trend-heat-section">
        <h3>Cross-theme seasonality heatmap</h3>
        <p className="muted trend-heat-intro">
          Dark cells are off-season and brighter cells mark stronger seasonal windows (index closer to 2x baseline).
        </p>
        <div className="trend-heat-months" aria-hidden>
          <span />
          {months.map((m) => (
            <span key={`head-${m}`}>{m}</span>
          ))}
        </div>
        <div className="heatmap">
          {rows.map((row) => (
            <div
              key={row.theme}
              className={`heat-row ${row.theme === activeTheme ? "is-active" : ""}`}
              onClick={() => setActiveTheme(row.theme)}
            >
              <button type="button" className="heat-row-theme">
                {row.theme}
              </button>
              {row.seasonal_index.map((value, idx) => (
                <button
                  type="button"
                  key={`${row.theme}-${idx}`}
                  className="heat-cell"
                  style={{ background: heatTone(value) }}
                  title={`${row.month_names[idx]}: ${value.toFixed(2)}`}
                >
                  <span>{value.toFixed(2)}</span>
                </button>
              ))}
            </div>
          ))}
        </div>
        <div className="trend-heat-legend muted" aria-hidden>
          <span>Low seasonality</span>
          <div />
          <span>High seasonality</span>
        </div>
      </section>

      {active ? (
        <section className="section insight-grid trend-insights">
          <article className="panel">
            <h4>Best launch month</h4>
            <p className="muted">Highest seasonal demand multiplier</p>
            <strong>{bestMonth ? months[bestMonth.idx] : "N/A"}</strong>
          </article>
          <article className="panel">
            <h4>Weakest month</h4>
            <p className="muted">Lowest seasonal demand month</p>
            <strong>{weakestMonth ? months[weakestMonth.idx] : "N/A"}</strong>
          </article>
          <article className="panel">
            <h4>Volatility</h4>
            <p className="muted">Spread between strongest and weakest index</p>
            <strong>
              {bestMonth && weakestMonth ? (bestMonth.value - weakestMonth.value).toFixed(2) : "N/A"}
            </strong>
          </article>
        </section>
      ) : null}
    </div>
  );
}
