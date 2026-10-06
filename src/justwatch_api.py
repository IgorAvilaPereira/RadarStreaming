"""Importação gratuita, sem token, do catálogo público regional do JustWatch.

O endpoint é usado pelo site público, mas não é uma API oficial com SLA; se mudar,
o snapshot existente continua no SQLite.
"""

import asyncio
import logging
import re
import unicodedata
from datetime import date
from urllib.parse import urljoin

import httpx2 as httpx


log = logging.getLogger("app.justwatch_api")
BASE_URL = "https://apis.justwatch.com/content"
LOCALE = "pt_BR"
IMAGE_BASE = "https://images.justwatch.com/"
ALIASES = {
    "Netflix": ("netflix",),
    "Prime Video": ("prime video", "amazon prime"),
    "Disney+": ("disney plus", "disney+"),
    "Max": ("max", "hbo max"),
    "Apple TV+": ("apple tv",),
}
GENRE_MAP = {
    "drama": "Drama", "comedy": "Comédia", "comedia": "Comédia",
    "science fiction": "Ficção científica", "science fiction and fantasy": "Ficção científica",
    "ficcao cientifica": "Ficção científica", "sci fi": "Ficção científica", "scifi": "Ficção científica",
    "thriller": "Suspense", "mystery and thriller": "Suspense", "crime": "Suspense", "suspense": "Suspense",
    "fantasy": "Fantasia", "fantasia": "Fantasia", "documentary": "Documentário", "documentario": "Documentário",
    "adventure": "Aventura", "aventura": "Aventura", "action and adventure": "Aventura", "action": "Aventura",
    "family": "Aventura", "animation": "Aventura", "romance": "Drama", "drama": "Drama",
}


def _normalize(value):
    value = unicodedata.normalize("NFKD", str(value).casefold())
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _find_provider(providers, service):
    aliases = tuple(_normalize(alias) for alias in ALIASES[service])
    for provider in providers:
        name = _normalize(provider.get("clear_name") or provider.get("technical_name") or provider.get("name") or "")
        if any(
            name == alias or name.endswith(f" {alias}") or name.startswith(f"{alias} ")
            for alias in aliases
        ):
            return provider.get("id")
    return None


def _genres(item):
    raw = item.get("genres") or []
    result = []
    for genre in raw:
        if isinstance(genre, dict):
            genre = genre.get("translation") or genre.get("name") or genre.get("short_name") or ""
        mapped = GENRE_MAP.get(_normalize(genre))
        if mapped and mapped not in result:
            result.append(mapped)
    return result or ["Drama"]


def _to_title(item, service):
    item_id = item.get("id") or item.get("object_id")
    if item_id is None:
        return None
    object_type = str(item.get("object_type") or item.get("content_type") or "movie").casefold()
    is_series = object_type in {"show", "tv", "series", "show_episode"}
    kind_key = "show" if is_series else "movie"
    raw_date = str(item.get("release_date") or item.get("original_release_date") or "")
    year = item.get("original_release_year") or item.get("release_year")
    if raw_date:
        try:
            year = int(raw_date[:4])
        except ValueError:
            raw_date = ""
    try:
        year = int(year or 0)
    except (TypeError, ValueError):
        year = 0
    release_date = raw_date[:10] if len(raw_date) >= 4 else (f"{year:04d}-01-01" if year else "")
    poster = item.get("poster") or item.get("poster_url") or ""
    if poster and not poster.startswith(("https://", "http://")):
        poster = urljoin(IMAGE_BASE, poster.lstrip("/"))
    if not poster:
        poster = "poster_aurora.svg"
    return {
        "id": f"justwatch:{kind_key}:{item_id}",
        "external_id": item_id,
        "title": item.get("title") or item.get("name") or "Título sem nome",
        "kind": "Série" if is_series else "Filme",
        "year": year,
        "genres": _genres(item),
        "synopsis": item.get("short_description") or item.get("description") or "Sinopse ainda não disponível.",
        "poster": poster,
        "release_date": release_date,
        "providers": {service},
    }


async def sync_justwatch_catalog(store, services):
    pending = []
    mapped = 0
    unmapped_services = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            provider_response = await client.get(f"{BASE_URL}/providers/locale/{LOCALE}")
            provider_response.raise_for_status()
            provider_payload = provider_response.json()
            providers = provider_payload if isinstance(provider_payload, list) else provider_payload.get("providers", provider_payload.get("results"))
            if not isinstance(providers, list) or not providers:
                raise ValueError("Formato de provedores inesperado")

            for service in services:
                name = service["name"]
                provider_id = _find_provider(providers, name)
                if provider_id is None:
                    unmapped_services.append(name)
                    continue
                mapped += 1
                for page_number in range(1, 4):
                    response = await client.post(
                        f"{BASE_URL}/titles/{LOCALE}/popular",
                        json={
                            "age_certifications": [],
                            "content_types": ["movie", "show"],
                            "genres": [],
                            "languages": [],
                            "max_price": None,
                            "min_price": None,
                            "monetization_types": ["flatrate"],
                            "page": page_number,
                            "page_size": 100,
                            "presentation_types": [],
                            "providers": [provider_id],
                            "release_year_from": date.today().year - 1,
                            "release_year_until": date.today().year,
                            "scoring_filter_types": [],
                            "timeline_type": "released",
                        },
                        headers={"accept": "application/json", "content-type": "application/json"},
                    )
                    response.raise_for_status()
                    payload = response.json()
                    if isinstance(payload, list):
                        items = payload
                        total_pages = 1
                    elif isinstance(payload, dict):
                        items = payload.get("items", payload.get("results"))
                        total_pages = payload.get("total_pages")
                        if not total_pages and payload.get("total_results") is not None:
                            total_pages = (int(payload["total_results"]) + 99) // 100
                        total_pages = int(total_pages or 3)
                    else:
                        items = None
                        total_pages = page_number
                    if not isinstance(items, list):
                        raise ValueError(f"Formato de catálogo inesperado para {name}")
                    for item in items:
                        title = _to_title(item, name)
                        if title:
                            pending.append((title, name))
                    if not items or len(items) < 100 or page_number >= min(total_pages, 3):
                        break

        if mapped != len(services):
            detail = (
                "Serviços não encontrados na fonte gratuita: "
                + ", ".join(unmapped_services)
                + "; catálogo anterior mantido."
            )
            store.record_source_status("JustWatch", "mapeamento incompleto; dados anteriores mantidos", detail)
            return {"success": False, "count": 0, "detail": detail}

        if not pending:
            detail = "A fonte não retornou títulos válidos; catálogo anterior mantido."
            store.record_source_status("JustWatch", "sem resultados; dados anteriores mantidos", detail)
            return {"success": False, "count": 0, "detail": detail}

        store.replace_catalog_snapshot("justwatch", pending)
        detail = f"{len(pending)} registros recentes recebidos da fonte pública para o Brasil."
        store.record_source_status("JustWatch", "atualizado", detail)
        log.info("Fonte gratuita atualizou %d registros", len(pending))
        return {"success": True, "count": len(pending), "detail": detail}
    except asyncio.CancelledError:
        raise
    except BaseException as error:
        detail = (
            f"Fonte gratuita indisponível ({type(error).__name__}: {error}); "
            "catálogo anterior mantido."
        )
        store.record_source_status("JustWatch", "falha; dados anteriores mantidos", detail)
        log.warning("Consulta JustWatch falhou: %s", error)
        return {"success": False, "count": 0, "detail": detail}
