"""Recomendações explicáveis, ponderadas por preferências e avaliações locais."""


def recommend_titles(titles, favorite_genres, watched_ids, reviews=None, limit=None):
    favorites = set(favorite_genres)
    watched = set(watched_ids)
    reviews = reviews or {}
    genre_weights = {genre: 1.25 for genre in favorites}

    # Assistir sem avaliar é um sinal fraco; a nota da resenha pesa mais.
    for title in titles:
        if title["id"] not in watched:
            continue
        review = reviews.get(title["id"])
        if review:
            rating = int(review["rating"])
            signal = (rating - 3) * 0.38
        else:
            signal = 0.16
        for genre in title.get("genres", []):
            genre_weights[genre] = max(-2.5, min(2.5, genre_weights.get(genre, 0) + signal))

    positive_mass = sum(max(weight, 0) for weight in genre_weights.values())
    negative_mass = sum(abs(min(weight, 0)) for weight in genre_weights.values())
    ranked = []

    for title in titles:
        if title["id"] in watched or title["id"] in reviews:
            continue
        genres = set(title.get("genres", []))
        positive_match = sum(max(genre_weights.get(genre, 0), 0) for genre in genres)
        negative_match = sum(abs(min(genre_weights.get(genre, 0), 0)) for genre in genres)

        if positive_mass:
            preference_fit = positive_match / positive_mass
            coverage = positive_match / max(sum(max(weight, 0) for weight in genre_weights.values()), 1)
            score = 0.72 * preference_fit + 0.28 * min(coverage * 2, 1)
        else:
            score = 0.38
        if negative_mass:
            score -= 0.3 * (negative_match / negative_mass)
        score = max(0, min(1, score))
        ranked.append((score, title.get("year", 0), title))

    ranked.sort(key=lambda row: (row[0], row[1]), reverse=True)
    results = [(title, score) for score, _, title in ranked]
    return results if limit is None else results[:limit]


def rank_services(services, favorite_genres, titles, watched_ids):
    favorites = set(favorite_genres)
    watched = set(watched_ids)
    results = []
    for service in services:
        available = [t for t in titles if service["name"] in t["providers"] and t["id"] not in watched]
        genre_fit = len(favorites.intersection(service["genres"])) / max(len(favorites), 1)
        catalog_fit = min(len(available) / 4, 1)
        match = (genre_fit * 0.7 + catalog_fit * 0.3) if favorites else catalog_fit
        value_score = match / service["monthly_price"]
        results.append({**service, "match": match, "value_score": value_score, "available_count": len(available)})
    return sorted(results, key=lambda item: (item["value_score"], item["match"]), reverse=True)
