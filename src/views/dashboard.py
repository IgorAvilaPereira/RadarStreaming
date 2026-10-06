"""Telas principais do Radar de Streaming, com suporte mobile e localização."""

import asyncio
import math
from datetime import date

import flet as ft

from components.share_card import build_share_card
from components.title_card import title_card
from data import GENRES, STREAMING_SERVICES
from exchange_api import fetch_brl_to_usd
from i18n import GENRE_LABELS, format_money, t
from recommendations import rank_services, recommend_titles
from views.review_flow import LocalReviewFlow


INK = ft.Colors.BLUE_GREY_900
MUTED = ft.Colors.BLUE_GREY_600
ACCENT = ft.Colors.TEAL_700
PANEL = ft.Colors.WHITE
MONTHS = {
    "pt-BR": ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"],
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
}


def dashboard(page: ft.Page, store, on_sync):
    language = store.get_setting("ui_language", "pt-BR")
    if language not in {"pt-BR", "en"}:
        language = "pt-BR"
    page.title = t(language, "app_title")
    currency = store.get_setting("display_currency", "BRL")
    if currency not in {"BRL", "USD"}:
        currency = "BRL"
    fx_rate = store.get_setting("brl_usd_rate")
    fx_date = store.get_setting("brl_usd_date", "")
    # Fallback só para manter os valores em USD visíveis quando não há rede
    # nem cotação previamente salva. Não é gravado como cotação oficial.
    fx_is_fallback = not bool(fx_rate)
    if fx_is_fallback:
        fx_rate = 0.20  # estimativa local: US$ 1 ≈ R$ 5,00
    fx_is_live = False
    favorite_genres = set(store.get_genres(GENRES[:3]))
    watched_ids = store.get_watched_ids()
    recommendation_page = 0
    recommendation_page_size = 7
    ranked_recommendations = []
    visible_recommendations = []

    recommendations_host = ft.Column(spacing=12)
    comparison_host = ft.Column(spacing=12)
    status_text = ft.Text(t(language, "local_saved"), size=13, color=MUTED)
    sync_status = ft.Text(t(language, "sync_info"), size=13, color=MUTED)
    sync_info_text = ft.Text(t(language, "sync_info"), size=13, color=MUTED)
    source_warning_text = ft.Text(t(language, "source_warning"), size=12, color=MUTED)
    catalog_info = ft.Text(t(language, "catalog_initial"), size=12, color=MUTED)
    exchange_status = ft.Text("", size=12, color=MUTED)
    token_field = ft.TextField(
        label=t(language, "token_label"),
        value=store.get_tmdb_token(),
        password=True,
        can_reveal_password=True,
        helper=ft.Text(t(language, "token_helper"), size=12, color=MUTED),
    )
    sync_button = ft.Button(content=ft.Text(t(language, "sync_button")))
    tmdb_settings_button = ft.TextButton(content=ft.Text(t(language, "tmdb_settings")), url="https://www.themoviedb.org/settings/api")
    price_disclaimer_text = ft.Text(t(language, "price_disclaimer"), size=12, color=MUTED)
    search_field = ft.TextField(
        label=t(language, "search_title"),
        hint_text=t(language, "search_hint"),
        on_change=None,
    )
    service_filter = ft.Dropdown(
        value="",
        label=t(language, "filter_streaming"),
        options=[ft.DropdownOption(key="", text=t(language, "all_services"))]
        + [ft.DropdownOption(key=s["name"], text=s["name"]) for s in STREAMING_SERVICES],
    )
    type_filter = ft.Dropdown(
        value="",
        label=t(language, "filter_type"),
        options=[
            ft.DropdownOption(key="", text=t(language, "all_types")),
            ft.DropdownOption(key="Filme", text=t(language, "movie")),
            ft.DropdownOption(key="Série", text=t(language, "series")),
        ],
    )
    language_filter = ft.Dropdown(
        value=language,
        label=t(language, "language"),
        options=[ft.DropdownOption(key="pt-BR", text="Português (Brasil)"), ft.DropdownOption(key="en", text="English")],
        on_select=None,
    )
    currency_filter = ft.Dropdown(
        value=currency,
        label=t(language, "currency"),
        options=[ft.DropdownOption(key="BRL", text="BRL · R$"), ft.DropdownOption(key="USD", text="USD · US$")],
        on_select=None,
    )

    home_title = ft.Text(size=23, weight=ft.FontWeight.BOLD, color=INK)
    home_subtitle = ft.Text(size=14, color=MUTED)
    genres_prompt = ft.Text(size=15, weight=ft.FontWeight.BOLD, color=INK)
    profile_title = ft.Text(size=23, weight=ft.FontWeight.BOLD, color=INK)
    profile_subtitle = ft.Text(size=14, color=MUTED)
    services_title = ft.Text(t(language, "manage_services"), size=18, weight=ft.FontWeight.BOLD, color=INK)
    custom_services_host = ft.Column(spacing=4)
    add_service_button = ft.OutlinedButton(content=ft.Text(t(language, "add_service")))
    profile_genres_title = ft.Text(size=15, weight=ft.FontWeight.BOLD, color=INK)
    auto_update_title = ft.Text(size=18, weight=ft.FontWeight.BOLD, color=INK)
    history_title = ft.Text(size=18, weight=ft.FontWeight.BOLD, color=INK)
    compare_title = ft.Text(size=23, weight=ft.FontWeight.BOLD, color=INK)
    compare_subtitle = ft.Text(size=14, color=MUTED)
    price_note = ft.Text(size=12, color=INK)
    app_title_text = ft.Text(size=24, weight=ft.FontWeight.BOLD, color=INK)
    tagline_text = ft.Text(size=13, color=MUTED)
    language_checks = []

    def current_language():
        return language

    def current_titles():
        return store.get_titles()

    def monthly_price_brl(service):
        if service.get("entered_currency") == "USD" and service.get("entered_price") and fx_rate:
            return float(service["entered_price"]) / float(fx_rate)
        return float(service["monthly_price"])

    def service_price_text(service, multiplier=1):
        if currency == "USD" and service.get("entered_currency") == "USD":
            return f"US$ {float(service['entered_price']) * multiplier:,.2f}"
        return format_money(monthly_price_brl(service) * multiplier, currency, fx_rate) or "—"

    def update_service_filter_options():
        selected = service_filter.value or ""
        options = [ft.DropdownOption(key="", text=t(language, "all_services"))]
        options.extend(
            ft.DropdownOption(key=service["name"], text=service["name"])
            for service in store.get_services(STREAMING_SERVICES)
        )
        service_filter.options = options
        service_filter.value = selected if any(option.key == selected for option in options) else ""

    def refresh_custom_services():
        custom_services = store.get_custom_services()
        if not custom_services:
            custom_services_host.controls = [ft.Text(t(language, "custom_services_empty"), size=13, color=MUTED)]
            return
        custom_services_host.controls = [
            ft.ListTile(
                title=ft.Text(service["name"]),
                subtitle=ft.Text(format_money(service["monthly_price"], currency, fx_rate) or "—"),
            )
            for service in custom_services
        ]

    def filter_recommendations(items):
        query = (search_field.value or "").strip().casefold()
        provider = service_filter.value or ""
        kind = type_filter.value or ""
        result = []
        for title, score in items:
            haystack = " ".join([
                title.get("title", ""), title.get("synopsis", ""),
                " ".join(title.get("genres", [])), " ".join(title.get("providers", [])),
            ]).casefold()
            if query and query not in haystack:
                continue
            if provider and provider not in title.get("providers", []):
                continue
            if kind and title.get("kind") != kind:
                continue
            result.append((title, score))
        return result

    def render_recommendation_page():
        total = len(visible_recommendations)
        if not total:
            recommendations_host.controls = [
                ft.Container(
                    padding=20,
                    bgcolor=PANEL,
                    border_radius=14,
                    content=ft.Text(t(language, "no_results")),
                )
            ]
            return

        page_count = (total + recommendation_page_size - 1) // recommendation_page_size
        start = recommendation_page * recommendation_page_size
        stop = min(start + recommendation_page_size, total)
        visible = visible_recommendations[start:stop]

        def show_previous():
            nonlocal recommendation_page
            recommendation_page = max(0, recommendation_page - 1)
            render_recommendation_page()
            page.update()

        def show_next():
            nonlocal recommendation_page
            recommendation_page = min(page_count - 1, recommendation_page + 1)
            render_recommendation_page()
            page.update()

        page_label = t(language, "page_count", page=recommendation_page + 1, pages=page_count)
        recommendations_host.controls = [
            ft.Column(
                spacing=8,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        wrap=True,
                        controls=[
                            ft.Button(content=ft.Text(t(language, "previous")), disabled=recommendation_page == 0, on_click=show_previous),
                            ft.Text(t(language, "result_count", start=start + 1, stop=stop, total=total, page_label=page_label), size=12, color=MUTED),
                            ft.Button(content=ft.Text(t(language, "next")), disabled=recommendation_page >= page_count - 1, on_click=show_next),
                        ],
                    ),
                    ft.Row(
                        scroll=ft.ScrollMode.AUTO,
                        spacing=14,
                        controls=[title_card(title, score, review_flow.mark_watched, language) for title, score in visible],
                    ),
                ],
            )
        ]

    def refresh_recommendations():
        nonlocal recommendation_page, ranked_recommendations, visible_recommendations
        ranked_recommendations = recommend_titles(
            current_titles(), favorite_genres, watched_ids, review_flow.reviews
        )
        visible_recommendations = filter_recommendations(ranked_recommendations)
        page_count = max(1, (len(visible_recommendations) + recommendation_page_size - 1) // recommendation_page_size)
        recommendation_page = min(recommendation_page, page_count - 1)
        render_recommendation_page()

    def refresh_comparison():
        services = store.get_services(STREAMING_SERVICES)
        ranked = rank_services(services, favorite_genres, current_titles(), watched_ids)
        best_name = ranked[0]["name"] if ranked else ""
        comparison_host.controls = []
        for service in ranked:
            month = format_money(service["monthly_price"], currency, fx_rate)
            annual = format_money(service["monthly_price"] * 12, currency, fx_rate)
            amount = f"{month or '—'} {t(language, 'per_month')}  ·  {annual or '—'} {t(language, 'per_year')}"
            genres = ", ".join(GENRE_LABELS.get(language, GENRE_LABELS["pt-BR"]).get(g, g) for g in service["genres"][:4])
            checked = service["checked_at"] or ("not checked yet" if language == "en" else "ainda não conferido")
            comparison_host.controls.append(
                ft.Container(
                    padding=16,
                    bgcolor=PANEL,
                    border=ft.Border.all(1, ft.Colors.BLUE_GREY_100),
                    border_radius=14,
                    content=ft.Column(
                        spacing=7,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                controls=[
                                    ft.Text(service["name"], size=18, weight=ft.FontWeight.BOLD, color=INK),
                                    ft.Text(t(language, "best_for_you") if service["name"] == best_name else "", size=11, weight=ft.FontWeight.BOLD, color=ACCENT),
                                ],
                            ),
                            ft.Text(amount, color=INK),
                            ft.Text(t(language, "compatibility", match=round(service["match"] * 100), count=service["available_count"]), size=13, color=MUTED),
                            ft.ProgressBar(value=service["match"], color=ACCENT, bgcolor=ft.Colors.BLUE_GREY_100, bar_height=7),
                            ft.Text(t(language, "strong_genres", genres=genres), size=12, color=MUTED),
                            ft.Text(t(language, "price_status", status=service["price_status"], checked=checked), size=12, color=MUTED),
                        ],
                    ),
                )
            )

    def open_add_service_dialog():
        name_field = ft.TextField(label=t(language, "service_name"), autofocus=True)
        price_field = ft.TextField(
            label=t(language, "service_price"),
            keyboard_type=ft.KeyboardType.NUMBER,
            hint_text="24,90",
        )
        source_field = ft.TextField(
            label=t(language, "service_source_url"),
            keyboard_type=ft.KeyboardType.URL,
            helper=ft.Text(t(language, "service_source_helper"), size=12, color=MUTED),
        )
        genre_checks = [
            ft.Checkbox(
                label=GENRE_LABELS.get(language, GENRE_LABELS["pt-BR"]).get(genre, genre),
                value=genre in favorite_genres,
                data=genre,
            )
            for genre in GENRES
        ]
        error_text = ft.Text("", color=ft.Colors.ERROR, size=12)

        def save_new_service():
            name = (name_field.value or "").strip()
            try:
                price = float((price_field.value or "").strip().replace(",", "."))
            except ValueError:
                price = 0
            selected_genres = [check.data for check in genre_checks if check.value]
            existing_names = {
                service["name"].casefold()
                for service in store.get_services(STREAMING_SERVICES)
            }
            if not name:
                error_text.value = t(language, "service_name_required")
            elif price <= 0:
                error_text.value = t(language, "service_price_invalid")
            elif name.casefold() in existing_names:
                error_text.value = t(language, "service_exists")
            elif not selected_genres:
                error_text.value = t(language, "service_genre_required")
            else:
                try:
                    store.add_custom_service(name, price, selected_genres, source_field.value or "")
                except Exception:
                    error_text.value = t(language, "service_exists")
                else:
                    update_service_filter_options()
                    refresh_custom_services()
                    refresh_recommendations()
                    refresh_comparison()
                    status_text.value = t(language, "service_added")
                    page.pop_dialog()
                    page.update()
                    return
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            scrollable=True,
            title=ft.Text(t(language, "add_service")),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    name_field,
                    price_field,
                    source_field,
                    ft.Text(t(language, "service_genres"), weight=ft.FontWeight.BOLD),
                    *genre_checks,
                    error_text,
                ],
            ),
            actions=[
                ft.TextButton(content=ft.Text(t(language, "cancel")), on_click=page.pop_dialog),
                ft.Button(content=ft.Text(t(language, "save_service")), on_click=save_new_service),
            ],
        )
        page.show_dialog(dialog)

    def refresh_after_profile_change():

        refresh_recommendations()
        review_flow.refresh_history()
        refresh_comparison()
        page.update()

    async def capture_share_image(title, rating, review_text):
        original_controls = list(page.controls)
        original_bgcolor = page.bgcolor
        original_padding = page.padding
        original_screenshots = page.enable_screenshots
        try:
            page.enable_screenshots = True
            page.clean()
            page.bgcolor = ft.Colors.BLUE_GREY_900
            page.padding = 8
            card = build_share_card(page.width, page.height, title, rating, review_text, language)
            page.add(ft.Container(expand=True, alignment=ft.Alignment.CENTER, content=card))
            page.update()
            return await page.take_screenshot(pixel_ratio=1, delay=120)
        finally:
            page.clean()
            page.bgcolor = original_bgcolor
            page.padding = original_padding
            page.enable_screenshots = original_screenshots
            page.add(*original_controls)
            page.update()

    review_flow = LocalReviewFlow(
        page, store, watched_ids, status_text, refresh_after_profile_change,
        capture_share_image, current_language,
    )
    history_host = review_flow.history_host

    def toggle_genre(e):
        genre = e.control.data
        if e.control.value:
            favorite_genres.add(genre)
        else:
            favorite_genres.discard(genre)
        store.save_genres(sorted(favorite_genres))
        refresh_recommendations()
        refresh_comparison()
        status_text.value = t(language, "saved_preferences")
        page.update()

    def make_genre_checks():
        checks = []
        for genre in GENRES:
            check = ft.Checkbox(
                label=GENRE_LABELS.get(language, GENRE_LABELS["pt-BR"]).get(genre, genre),
                data=genre,
                value=genre in favorite_genres,
                on_change=toggle_genre,
            )
            checks.append(check)
        language_checks.extend(checks)
        return ft.Row(scroll=ft.ScrollMode.AUTO, spacing=4, controls=checks)

    def current_month_label():
        names = MONTHS[language]
        month = names[date.today().month - 1]
        return f"{month.capitalize()} {date.today().year}" if language == "en" else f"{month.capitalize()} de {date.today().year}"

    def update_static_labels():
        app_title_text.value = t(language, "app_title")
        tagline_text.value = t(language, "tagline")
        home_title.value = t(language, "recommendations")
        home_subtitle.value = t(language, "recommendation_subtitle")
        genres_prompt.value = t(language, "genres_prompt")
        profile_title.value = t(language, "profile_title")
        profile_subtitle.value = t(language, "profile_subtitle")
        profile_genres_title.value = t(language, "genres_title")
        auto_update_title.value = t(language, "automatic_update")
        history_title.value = t(language, "history_title")
        compare_title.value = t(language, "compare_title", month=current_month_label())
        compare_subtitle.value = t(language, "compare_subtitle")
        for check in language_checks:
            check.label = GENRE_LABELS.get(language, GENRE_LABELS["pt-BR"]).get(check.data, check.data)
        token_field.label = t(language, "token_label")
        token_field.helper = ft.Text(t(language, "token_helper"), size=12, color=MUTED)
        sync_button.content = ft.Text(t(language, "sync_button"))
        tmdb_settings_button.content = ft.Text(t(language, "tmdb_settings"))
        price_disclaimer_text.value = t(language, "price_disclaimer")
        sync_info_text.value = t(language, "sync_info")
        source_warning_text.value = t(language, "source_warning")
        search_field.label = t(language, "search_title")
        search_field.hint_text = t(language, "search_hint")
        service_filter.label = t(language, "filter_streaming")
        update_service_filter_options()
        services_title.value = t(language, "manage_services")
        add_service_button.content = ft.Text(t(language, "add_service"))
        refresh_custom_services()
        type_filter.label = t(language, "filter_type")
        type_filter.options = [ft.DropdownOption(key="", text=t(language, "all_types")), ft.DropdownOption(key="Filme", text=t(language, "movie")), ft.DropdownOption(key="Série", text=t(language, "series"))]
        language_filter.label = t(language, "language")
        currency_filter.label = t(language, "currency")
        if language_filter.value != language:
            language_filter.value = language
        tab_bar.tabs = [ft.Tab(label=t(language, "tab_for_you")), ft.Tab(label=t(language, "tab_profile")), ft.Tab(label=t(language, "tab_compare"))]
        currency_note = t(language, "price_note_usd") if currency == "USD" else t(language, "price_note")
        price_note.value = currency_note
        if currency == "USD":
            if fx_is_fallback:
                exchange_status.value = t(language, "exchange_fallback")
            else:
                status_key = "exchange_live" if fx_is_live else "exchange_cached"
                exchange_status.value = t(language, status_key, date=fx_date or "—")
        else:
            exchange_status.value = ""
        if catalog_info.value in {t("pt-BR", "catalog_initial"), t("en", "catalog_initial")}:
            catalog_info.value = t(language, "catalog_initial")
        refresh_recommendations()
        review_flow.refresh_history()
        refresh_comparison()

    def apply_filters():
        nonlocal recommendation_page
        recommendation_page = 0
        refresh_recommendations()
        page.update()

    def on_language_select(e):
        nonlocal language
        language = e.control.value or "pt-BR"
        store.save_setting("ui_language", language)
        page.title = t(language, "app_title")
        status_text.value = t(language, "local_saved")
        sync_status.value = t(language, "sync_info")
        update_static_labels()
        page.update()

    def on_currency_select(e):
        nonlocal currency
        currency = e.control.value or "BRL"
        store.save_setting("display_currency", currency)
        update_static_labels()
        page.update()

    async def refresh_exchange_rate():
        nonlocal fx_rate, fx_date, fx_is_live, fx_is_fallback
        try:
            rate, rate_date = await fetch_brl_to_usd()
            fx_rate, fx_date, fx_is_live = rate, rate_date, True
            fx_is_fallback = False
            store.save_setting("brl_usd_rate", rate)
            store.save_setting("brl_usd_date", rate_date)
        except asyncio.CancelledError:
            raise
        except Exception:
            # Mantém a cotação local salva ou a estimativa claramente sinalizada;
            # falhas de rede não apagam nem substituem dados persistidos.
            fx_is_live = False
        update_static_labels()
        page.update()

    async def perform_sync():
        sync_button.disabled = True
        sync_status.value = t(language, "sync_start")
        store.save_tmdb_token(token_field.value or "")
        page.update()
        try:
            result = await on_sync(token_field.value or "")
            catalog_result = result["catalog"]
            price_result = result["prices"]
            refresh_recommendations()
            review_flow.refresh_history()
            refresh_comparison()
            if catalog_result["success"]:
                catalog_info.value = t(language, "updated_catalog", detail=catalog_result["detail"])
            else:
                catalog_info.value = t(language, "stale_catalog", detail=catalog_result["detail"])
            sync_status.value = t(language, "sync_complete", catalog=catalog_result["detail"], prices=price_result["detail"])
        except asyncio.CancelledError:
            raise
        except BaseException as error:
            sync_status.value = t(language, "sync_interrupted", error=type(error).__name__)
        finally:
            sync_button.disabled = False
            page.update()

    search_field.on_change = lambda e: apply_filters()
    service_filter.on_select = lambda e: apply_filters()
    type_filter.on_select = lambda e: apply_filters()
    language_filter.on_select = on_language_select
    currency_filter.on_select = on_currency_select
    sync_button.on_click = perform_sync
    add_service_button.on_click = open_add_service_dialog

    home_view = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=14,
        controls=[
            ft.Column(spacing=4, controls=[home_title, home_subtitle]),
            catalog_info,
            ft.Column(spacing=8, controls=[search_field, service_filter, type_filter]),
            genres_prompt,
            make_genre_checks(),
            recommendations_host,
        ],
    )
    profile_view = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=16,
        controls=[
            ft.Column(spacing=4, controls=[profile_title, profile_subtitle]),
            ft.Row(wrap=True, spacing=12, controls=[language_filter, currency_filter]),
            services_title,
            add_service_button,
            custom_services_host,
            ft.Divider(color=ft.Colors.BLUE_GREY_100),
            profile_genres_title,
            make_genre_checks(),
            ft.Divider(color=ft.Colors.BLUE_GREY_100),
            auto_update_title,
            sync_info_text,
            token_field,
            tmdb_settings_button,
            sync_button,
            sync_status,
            source_warning_text,
            ft.Divider(color=ft.Colors.BLUE_GREY_100),
            history_title,
            history_host,
        ],
    )
    compare_view = ft.Column(
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=14,
        controls=[
            ft.Column(spacing=4, controls=[compare_title, compare_subtitle]),
            ft.Container(padding=12, bgcolor=ft.Colors.AMBER_50, border_radius=12, content=price_note),
            exchange_status,
            price_disclaimer_text,
            comparison_host,
        ],
    )
    tab_bar = ft.TabBar(
        scrollable=True,
        tabs=[ft.Tab(label=t(language, "tab_for_you")), ft.Tab(label=t(language, "tab_profile")), ft.Tab(label=t(language, "tab_compare"))],
        indicator_color=ACCENT,
        label_color=ACCENT,
        unselected_label_color=MUTED,
    )
    # update_static_labels refers to the TabBar, so it is called only after this point.
    root_header = ft.Column(
        spacing=0,
        controls=[
            ft.Row(
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Image(src="icon.svg", width=42, height=42),
                    ft.Column(expand=True, spacing=0, controls=[app_title_text, tagline_text]),
                ],
            ),
        ],
    )
    tabs = ft.Tabs(
        length=3,
        selected_index=0,
        expand=True,
        animation_duration=180,
        content=ft.Column(expand=True, controls=[tab_bar, ft.TabBarView(expand=True, controls=[home_view, profile_view, compare_view])]),
    )
    root = ft.Column(expand=True, spacing=12, controls=[root_header, tabs, status_text])
    update_static_labels()
    refresh_recommendations()
    review_flow.refresh_history()
    refresh_comparison()
    asyncio.create_task(perform_sync())
    asyncio.create_task(refresh_exchange_rate())
    return root
