import { FileCode2, Gamepad2, Home, Search, Sparkles, TrendingUp } from "lucide-react";
import { Link, NavLink } from "react-router-dom";
import { useMemo } from "react";
import type { PropsWithChildren } from "react";
import { readArchetypeIdentity } from "../lib/identity";
import { TopSearchBar } from "./TopSearchBar";

const API_DOCS_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function Layout({ children }: PropsWithChildren) {
  const identity = useMemo(() => readArchetypeIdentity(), []);
  const apiDocsUrl = `${API_DOCS_BASE.replace(/\/$/, "")}/docs`;

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link to="/" className="logo">
          <span className="logo-mark" aria-hidden>
            <Gamepad2 size={20} strokeWidth={2.25} />
          </span>
          <span>GameRec</span>
        </Link>
        <TopSearchBar />
        <nav className="nav">
          <NavLink to="/" className="nav-link">
            <Home size={14} /> Discover
          </NavLink>
          <NavLink to="/search" className="nav-link">
            <Search size={14} /> Browse
          </NavLink>
          <NavLink to="/for-you" className="nav-link">
            <Sparkles size={14} /> For You
          </NavLink>
          <NavLink to="/explore" className="nav-link">
            <Home size={14} /> Explore
          </NavLink>
          <NavLink to="/trends" className="nav-link">
            <TrendingUp size={14} /> Trends
          </NavLink>
          <a
            className="icon-action icon-action--link"
            href={apiDocsUrl}
            target="_blank"
            rel="noreferrer"
            title="Open API docs (Swagger)"
            aria-label="Open backend API documentation in a new tab"
          >
            <FileCode2 size={15} strokeWidth={2} />
          </a>
        </nav>
      </header>
      {identity ? (
        <div className="identity-nav-pill">
          You play like <strong>{identity.archetype}</strong>
        </div>
      ) : null}
      <main className="main-content">{children}</main>
    </div>
  );
}
