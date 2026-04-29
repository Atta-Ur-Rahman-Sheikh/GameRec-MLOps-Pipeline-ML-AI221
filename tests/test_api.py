"""FastAPI integration tests (TestClient)."""

from __future__ import annotations

from urllib.parse import quote


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert "artifacts_loaded" in body


def test_games_search(client):
    r = client.get("/games/search", params={"q": "portal", "limit": 5})
    assert r.status_code == 200
    hits = r.json()
    assert isinstance(hits, list)
    if hits:
        assert "name" in hits[0]


def test_recommend_similar(client, famous_game):
    r = client.post(
        "/recommend/similar",
        json={"game_name": famous_game, "n": 5},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["anchor"] == famous_game
    assert len(data["items"]) == 5


def test_recommend_user(client):
    r = client.post(
        "/recommend/user",
        json={
            "liked_genres": ["Indie"],
            "liked_tags": ["Roguelike"],
            "n": 5,
        },
    )
    assert r.status_code == 200
    assert len(r.json()["items"]) <= 5


def test_predict_player_type_by_title(client, famous_game):
    r = client.post(
        "/predict/player-type/by-title",
        json={"game_name": famous_game},
    )
    assert r.status_code == 200
    preds = r.json()["predictions"]
    assert preds
    assert "archetype" in preds[0]


def test_predict_player_type_by_query(client):
    r = client.post(
        "/predict/player-type/by-query",
        json={"liked_tags": ["Horror"], "liked_genres": ["Indie"]},
    )
    assert r.status_code == 200


def test_predict_popularity(client):
    r = client.post(
        "/predict/popularity",
        json={
            "tags": ["Building", "Sandbox"],
            "genres": ["Simulation"],
            "categories": [],
            "description": "Relaxing builder game.",
            "release_year": 2022,
        },
    )
    assert r.status_code == 200
    assert "predicted_popularity" in r.json()


def test_discover_clusters(client):
    r = client.get("/discover/clusters")
    assert r.status_code == 200
    cards = r.json()
    assert isinstance(cards, list)


def test_discover_hidden_genre(client, famous_game):
    path = f"/discover/hidden-genre/{quote(famous_game)}"
    r = client.get(path)
    assert r.status_code == 200
    body = r.json()
    assert body["game"]
    assert "cluster_id" in body


def test_seasonality_themes(client):
    r = client.get("/seasonality/themes")
    assert r.status_code == 200
    themes = r.json()
    assert themes


def test_seasonality_theme(client):
    themes = client.get("/seasonality/themes").json()
    r = client.get(f"/seasonality/{themes[0]}")
    assert r.status_code == 200
    body = r.json()
    assert len(body["seasonal_index"]) == 12


def test_recommend_explain(client, famous_game):
    r = client.post(
        "/recommend/similar",
        json={"game_name": famous_game, "n": 2},
    )
    assert r.status_code == 200
    other = r.json()["items"][0]["name"]
    ex = client.post(
        "/recommend/explain",
        json={"anchor": famous_game, "recommended": other},
    )
    assert ex.status_code == 200
    assert "shared_genres" in ex.json()
