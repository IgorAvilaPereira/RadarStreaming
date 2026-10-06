"""Editor local de resenhas com nota por estrelas."""

import flet as ft

from i18n import t


INK = ft.Colors.BLUE_GREY_900
MUTED = ft.Colors.BLUE_GREY_600
GOLD = ft.Colors.AMBER_700


def show_review_editor(page, title, review, on_save, on_share, language_getter, initial_hint=None):
    rating = int(review["rating"]) if review else 0
    note_field = ft.TextField(
        label=t(language_getter(), "review_label"),
        value=review["text"] if review else "",
        multiline=True,
        min_lines=3,
        max_lines=6,
        hint_text=t(language_getter(), "review_hint"),
    )
    hint = ft.Text(
        initial_hint or t(language_getter(), "choose_stars"),
        size=12,
        color=ft.Colors.ERROR if initial_hint else MUTED,
    )
    stars = ft.Row(spacing=2)

    def star_handler(selected):
        def choose():
            set_rating(selected)
        return choose

    def update_stars():
        stars.controls = [
            ft.TextButton(
                content=ft.Text("★" if value <= rating else "☆", size=30, color=GOLD if value <= rating else MUTED),
                on_click=star_handler(value),
            )
            for value in range(1, 6)
        ]

    def set_rating(value):
        nonlocal rating
        rating = value
        update_stars()
        page.update()

    def close():
        page.pop_dialog()

    def save():
        if rating == 0:
            hint.value = t(language_getter(), "need_stars_save")
            hint.color = ft.Colors.ERROR
            page.update()
            return
        on_save(title["id"], rating, note_field.value or "")
        page.pop_dialog()

    async def share():
        if rating == 0:
            hint.value = t(language_getter(), "need_stars_share")
            hint.color = ft.Colors.ERROR
            page.update()
            return
        hint.value = t(language_getter(), "share_preparing")
        hint.color = MUTED
        page.update()
        current_text = note_field.value or ""
        try:
            await on_share(title, rating, current_text)
        except Exception as error:
            show_review_editor(
                page,
                title,
                {"rating": rating, "text": current_text},
                on_save,
                on_share,
                language_getter,
                initial_hint=t(
                    language_getter(), "share_failed",
                    error=f"{type(error).__name__}: {error}",
                ),
            )

    update_stars()
    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text(f"{t(language_getter(), 'review_title')} · {title['title']}", color=INK),
            content=ft.Column(
                tight=True,
                spacing=8,
                controls=[
                    ft.Text(f"{t(language_getter(), 'movie') if title['kind'] == 'Filme' else t(language_getter(), 'series')} · {title['year']}", size=13, color=MUTED),
                    stars,
                    note_field,
                    hint,
                    ft.Text(t(language_getter(), "local_only"), size=11, color=MUTED),
                ],
            ),
            actions=[
                ft.TextButton(content=ft.Text(t(language_getter(), "cancel")), on_click=close),
                ft.TextButton(content=ft.Text(t(language_getter(), "share")), on_click=share),
                ft.Button(content=ft.Text(t(language_getter(), "save_review")), on_click=save),
            ],
        )
    )
