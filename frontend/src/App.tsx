import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ExplorePage } from "./pages/ExplorePage";
import { ForYouPage } from "./pages/ForYouPage";
import { GamePage } from "./pages/GamePage";
import { HomePage } from "./pages/HomePage";
import { SearchPage } from "./pages/SearchPage";
import { TrendsPage } from "./pages/TrendsPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/for-you" element={<ForYouPage />} />
        <Route path="/explore" element={<ExplorePage />} />
        <Route path="/trends" element={<TrendsPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/game/:name" element={<GamePage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Layout>
  );
}
