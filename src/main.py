import logging

import flet as ft

from catalog_api import sync_tmdb_catalog
from data import PRICE_SOURCES, STREAMING_SERVICES, TITLES
from justwatch_api import sync_justwatch_catalog
from price_api import verify_official_prices
from storage import LocalStore
from views.dashboard import dashboard


LOG_LEVEL = logging.INFO
logging.basicConfig(format="%(levelname)s %(name)s: %(message)s")
logging.getLogger("app").setLevel(LOG_LEVEL)
log = logging.getLogger("app.main")


def main(page: ft.Page):
    page.title = "Radar de Streaming"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.Colors.BLUE_GREY_50
    page.padding = 18
    page.spacing = 12

    store = LocalStore()
    store.seed(TITLES, STREAMING_SERVICES, PRICE_SOURCES)
    log.info("SQLite local aberto em %s", store.database_path)

    async def synchronize_sources(token):
        if token.strip():
            catalog_result = await sync_tmdb_catalog(token, store, STREAMING_SERVICES)
            if not catalog_result["success"]:
                free_result = await sync_justwatch_catalog(store, STREAMING_SERVICES)
                catalog_result = {
                    "success": free_result["success"],
                    "count": free_result["count"],
                    "detail": f"TMDB não atualizou. Fonte gratuita: {free_result['detail']}",
                }
        else:
            catalog_result = await sync_justwatch_catalog(store, STREAMING_SERVICES)

        price_result = await verify_official_prices(store, STREAMING_SERVICES, PRICE_SOURCES)
        return {"catalog": catalog_result, "prices": price_result}

    page.add(dashboard(page, store, synchronize_sources))


ft.run(main)
