"""Cartão visual temporário para exportar resenha e capa como uma imagem."""

import flet as ft

from i18n import t


INK = ft.Colors.BLUE_GREY_900
MUTED = ft.Colors.BLUE_GREY_600
ACCENT = ft.Colors.TEAL_700
GOLD = ft.Colors.AMBER_700


def build_share_card(width, height, title, rating, review_text, language="pt-BR"): 
    viewport_width = float(width or 1000)
    viewport_height = float(height or 700)
    card_width = min(max(viewport_width - 32, 300), 1120)
    card_height = min(max(viewport_height - 32, 360), 620)
    review = review_text.strip() or t(language, "fallback_review")
    stars = "★" * int(rating) + "☆" * (5 - int(rating))
    kind = t(language, "movie") if title["kind"] == "Filme" else t(language, "series")

    def details():
        return [
            ft.Text(title["title"], size=28, weight=ft.FontWeight.BOLD, color=INK, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Text(f"{kind} · {title['year']}", size=14, color=MUTED),
            ft.Text(stars, size=25, color=GOLD),
            ft.Text(t(language, "my_review"), size=12, weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Text(review, size=16, color=INK, max_lines=5, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Text(t(language, "about_title"), size=12, weight=ft.FontWeight.BOLD, color=ACCENT),
            ft.Text(title["synopsis"], size=13, color=MUTED, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
            ft.Text(t(language, "illustrative_cover"), size=11, color=MUTED),
        ]

    if viewport_width >= 700:
        poster_height = card_height - 32
        poster_width = round(poster_height * 2 / 3)
        content = ft.Row(
            spacing=22,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Image(
                    src=title["poster"],
                    width=poster_width,
                    height=poster_height,
                    fit=ft.BoxFit.COVER,
                    border_radius=10,
                    error_content=ft.Container(
                        width=poster_width,
                        height=poster_height,
                        bgcolor=ft.Colors.BLUE_GREY_100,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text("Capa ilustrativa indisponível", color=MUTED),
                    ),
                ),
                ft.Column(expand=True, spacing=8, controls=details()),
            ],
        )
    else:
        poster_height = min(220, round(card_height * 0.32))
        content = ft.Column(
            spacing=5,
            controls=[
                ft.Image(
                    src=title["poster"],
                    width=card_width - 32,
                    height=poster_height,
                    fit=ft.BoxFit.COVER,
                    border_radius=10,
                    error_content=ft.Container(
                        width=card_width - 32,
                        height=poster_height,
                        bgcolor=ft.Colors.BLUE_GREY_100,
                        alignment=ft.Alignment.CENTER,
                        content=ft.Text("Capa ilustrativa indisponível", color=MUTED),
                    ),
                ),
                *details(),
            ],
        )

    return ft.Container(
        width=card_width,
        height=card_height,
        padding=16,
        bgcolor=ft.Colors.WHITE,
        border=ft.Border.all(1, ft.Colors.BLUE_GREY_100),
        border_radius=18,
        content=content,
    )
