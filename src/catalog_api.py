"""Busca lançamentos recentes e disponibilidade regional no TMDB."""

import asyncio
import logging
import re
import unicodedata
from datetime import date, timedelta

import httpx2 as httpx


log = logging.getLogger("app.catalog_api")
TMDB_API = "https://api.themoviedb.org/3"
TMDB_IMAGE = "https://image.tmdb.org/t/p/w342"

SERVICE_ALIASES = {
    "Netflix": ("netflix",),
    "Prime Video": ("prime video", "amazon prime"),
    "Disney+": ("disney+", "disney plus"),
    "Max": ("max",),
    "Apple TV+": ("apple tv",),
}
GENRE_NAMES = {
    12: "Aventura", 14: "Fantasia", 16: "Aventura", 18: "Drama",
    28: "Aventura", 35: "Comédia", 53: "Suspense", 80: "Suspense",
    99: "Documentário", 878: "Ficção científica", 9648: "Suspense",
    10749: "Drama", 10751: "Aventura", 10759: "Aventura",
    10765: "Ficção científica", 10768: "Drama",
}


def _normalize(value):
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _provider_for_service(provider_list, service):
    aliases = tuple(_normalize(alias) for alias in SERVICE_ALIASES[service])
    for provider in provider_list:
        candidate = _normalize(provider.get("provider_name", ""))
        if any(
            candidate == alias
            or candidate.endswith(f" {alias}")
            or candidate.startswith(f"{alias} ")
            for alias in aliases
        ):
            return provider.get("provider_id")
    return None


def _map_title(result, kind):
    release_date = result.get("release_date") or result.get("first_air_date") or ""
    try:
        year = int(release_date[:4])
    except (TypeError, ValueError):
        year = 0
    genre_names = list(dict.fromkeys(
        GENRE_NAMES[genre_id]
        for genre_id in result.get("genre_ids", [])
        if genre_id in GENRE_NAMES
    )) or ["Drama"]
    title = result.get("title") or result.get("name") or "Título sem nome"
    image_path = result.get("poster_path")
    return {
        "id": f"tmdb:{kind}:{result['id']}",
        "tmdb_id": result["id"],
        "title": title,
        "kind": "Filme" if kind == "movie" else "Série",
        "year": year,
        "genres": genre_names,
        "synopsis": result.get("overview") or "Sinopse ainda não disponível.",
        "poster": f"{TMDB_IMAGE}{image_path}" if image_path else "poster_aurora.svg",
        "release_date": release_date,
    }


async def sync_tmdb_catalog(token, store, services):
    if not token.strip():
        detail = "Token TMDB não informado; lançamentos já salvos foram mantidos."
        store.record_source_status("TMDB", "token ausente", detail)
        return {"success": False, "count": 0, "detail": detail}

    headers = {"Authorization": f"Bearer {token.strip()}", "accept": "application/json"}
    start_date = (date.today() - timedelta(days=365)).isoformat()
    end_date = date.today().isoformat()
    mapped_services = set()
    pending_titles = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            provider_lists = {}
            for kind in ("movie", "tv"):
                response = await client.get(
                    f"{TMDB_API}/watch/providers/{kind}",
                    params={"watch_region": "BR", "language": "pt-BR"},
                    headers=headers,
                )
                response.raise_for_status()
                provider_lists[kind] = response.json().get("results", [])

            for service in services:
                service_name = service["name"]
                for kind in ("movie", "tv"):
                    provider_id = _provider_for_service(provider_lists[kind], service_name)
                    if not provider_id:
                        continue
                    mapped_services.add(service_name)
                    if kind == "movie":
                        date_params = {"primary_release_date.gte": start_date, "primary_release_date.lte": end_date}
                        sort_by = "primary_release_date.desc"
                    else:
                        date_params = {"first_air_date.gte": start_date, "first_air_date.lte": end_date}
                        sort_by = "first_air_date.desc"

                    for page_number in range(1, 4):
                        response = await client.get(
                            f"{TMDB_API}/discover/{kind}",
                            params={
                                "language": "pt-BR",
                                "region": "BR",
                                "watch_region": "BR",
                                "with_watch_providers": str(provider_id),
                                "with_watch_monetization_types": "flatrate",
                                "sort_by": sort_by,
                                "page": page_number,
                                **date_params,
                            },
                            headers=headers,
                        )
                        response.raise_for_status()
                        payload = response.json()
                        results = payload.get("results", [])
                        for result in results:
                            if result.get("id"):
                                pending_titles.append((_map_title(result, kind), service_name))
                        total_pages = min(int(payload.get("total_pages") or 1), 3)
                        if not results or page_number >= total_pages:
                            break

        missing_services = sorted(
            {service["name"] for service in services} - mapped_services
        )
        if missing_services:
            detail = (
                "Provedor não mapeado no TMDB: " + ", ".join(missing_services)
                + "; catálogo anterior mantido."
            )
            store.record_source_status("TMDB", "mapeamento incompleto; dados anteriores mantidos", detail)
            return {"success": False, "count": 0, "detail": detail}
        if not pending_titles:
            detail = "Nenhum lançamento recebido; catálogo anterior mantido."
            store.record_source_status("TMDB", "sem resultados; dados anteriores mantidos", detail)
            return {"success": False, "count": 0, "detail": detail}

        # A transação troca o snapshot apenas depois de todas as consultas concluírem.
        store.replace_catalog_snapshot("tmdb", pending_titles)
        detail = f"{len(pending_titles)} registros recebidos na região BR."
        store.record_source_status("TMDB", "atualizado", detail)
        log.info("TMDB atualizou %d registros", len(pending_titles))
        return {"success": True, "count": len(pending_titles), "detail": detail}
    except asyncio.CancelledError:
        raise
    except BaseException as error:
        detail = (
            f"Consulta TMDB falhou ({type(error).__name__}: {error}); "
            "catálogo anterior mantido."
        )
        store.record_source_status("TMDB", "falha; dados anteriores mantidos", detail)
        log.warning("Falha na sincronização TMDB: %s", error)
        return {"success": False, "count": 0, "detail": detail}
