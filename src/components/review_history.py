"""Lista local de títulos assistidos e suas resenhas."""

import flet as ft

from i18n import t


INK = ft.Colors.BLUE_GREY_900
MUTED = ft.Colors.BLUE_GREY_600
GOLD = ft.Colors.AMBER_700


def review_history_panel(store, watched_ids, on_edit, on_remove, language_getter):
    host = ft.Column(spacing=8)

    def action_handler(callback, title_id):
        def run_action():
            callback(title_id)
        return run_action

    def refresh():
        titles = [title for title in store.get_titles() if title["id"] in watched_ids]
        if not titles:
            host.controls = [ft.Text(t(language_getter(), "empty_history"), color=MUTED)]
            return

        reviews = store.get_reviews()
        host.controls = []
        for title in titles:
            review = reviews.get(title["id"])
            kind = t(language_getter(), "movie") if title["kind"] == "Filme" else t(language_getter(), "series")
            details = [ft.Text(f"{kind} · {title['year']}", size=12, color=MUTED)]
            if review:
                details.extend([
                    ft.Text("★" * review["rating"] + "☆" * (5 - review["rating"]), color=GOLD),
                    ft.Text(review["text"] or t(language_getter(), "no_comment"), size=12, color=INK, max_lines=3),
                ])
            else:
                details.append(ft.Text(t(language_getter(), "no_review"), size=12, color=MUTED))

            host.controls.append(
                ft.Container(
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.BLUE_GREY_100),
                    border_radius=12,
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Column(
                                expand=True,
                                spacing=3,
                                controls=[
                                    ft.Text(title["title"], weight=ft.FontWeight.BOLD, color=INK),
                                    *details,
                                ],
                            ),
                            ft.Column(
                                tight=True,
                                controls=[
                                    ft.TextButton(
                                        content=ft.Text(t(language_getter(), "edit_review")), 
                                        on_click=action_handler(on_edit, title["id"]),
                                    ),
                                    ft.TextButton(
                                        content=ft.Text(t(language_getter(), "remove_history")), 
                                        on_click=action_handler(on_remove, title["id"]),
                                    ),
                                ],
                            ),
                        ],
                    ),
                )
            )

    return host, refresh
