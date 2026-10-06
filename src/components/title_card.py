"""Cartão de recomendação com capa, disponibilidade e ação de histórico."""

import flet as ft

from i18n import GENRE_LABELS, t


INK = ft.Colors.BLUE_GREY_900
MUTED = ft.Colors.BLUE_GREY_600
ACCENT = ft.Colors.TEAL_700


def title_card(title, score, mark_watched, language="pt-BR"):
    providers = title.get("providers", [])
    where = " · ".join(providers) if providers else t(language, "availability_unknown")
    source_labels = {
        "seed": t(language, "source_seed"),
        "justwatch": t(language, "source_justwatch"),
        "tmdb": t(language, "source_tmdb"),
    }
    source_label = source_labels.get(title.get("source"), t(language, "source_local"))
    kind = t(language, "movie") if title.get("kind") == "Filme" else t(language, "series")
    genres = ", ".join(GENRE_LABELS.get(language, GENRE_LABELS["pt-BR"]).get(g, g) for g in title["genres"])
    return ft.Container(
        width=196,
        padding=12,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLUE_GREY_100),
        border_radius=16,
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Image(src=title["poster"], width=150, height=175, fit=ft.BoxFit.COVER),
                ft.Text(title["title"], size=16, weight=ft.FontWeight.BOLD, color=INK, max_lines=2),
                ft.Text(f"{kind} · {title['year']}", size=12, color=MUTED),
                ft.Text(genres, size=12, color=ACCENT, max_lines=2),
                ft.Text(title["synopsis"], size=12, color=INK, max_lines=3),
                ft.Text(t(language, "where", providers=where), size=11, color=MUTED, max_lines=2),
                ft.Text(t(language, "affinity", score=round(score * 100)), size=12, weight=ft.FontWeight.BOLD, color=ACCENT),
                ft.Button(content=ft.Text(t(language, "watched")), on_click=lambda: mark_watched(title["id"])),
                ft.Text(source_label, size=10, color=MUTED),
            ],
        ),
    )
