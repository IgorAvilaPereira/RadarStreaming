"""Coordena resenhas locais, histórico e compartilhamento externo."""

import flet as ft

from components.review_history import review_history_panel
from i18n import t
from review_sharing import share_review
from views.review_editor import show_review_editor


class LocalReviewFlow:
    def __init__(self, page, store, watched_ids, status_text, on_change, capture_share_image, language_getter):
        self.page = page
        self.store = store
        self.watched_ids = watched_ids
        self.status_text = status_text
        self.on_change = on_change
        self.capture_share_image = capture_share_image
        self.language_getter = language_getter
        self.reviews = store.get_reviews()
        self.share_service = ft.Share()
        self.history_host, self.refresh_history = review_history_panel(
            store, watched_ids, self.open_editor, self.remove_watched, language_getter
        )

    def save_review(self, title_id, rating, review_text):
        self.store.save_review(title_id, rating, review_text)
        self.watched_ids.add(title_id)
        self.reviews[title_id] = {"rating": rating, "text": review_text.strip()}
        self.on_change()
        self.status_text.value = t(self.language_getter(), "review_saved")
        self.page.update()

    async def share_current(self, title, rating, review_text):
        self.page.pop_dialog()
        self.page.update()
        try:
            image_data = await self.capture_share_image(title, rating, review_text)
            message = await share_review(
                self.share_service, title, rating, review_text, image_data,
                self.language_getter(),
            )
        except Exception as error:
            self.status_text.value = t(
                self.language_getter(), "share_failed",
                error=f"{type(error).__name__}: {error}",
            )
            self.page.update()
            raise
        message = t(self.language_getter(), "share_success")
        self.status_text.value = message
        self.page.update()
        return message

    def open_editor(self, title_id):
        title = next(
            (item for item in self.store.get_titles() if item["id"] == title_id),
            None,
        )
        if title is None:
            self.status_text.value = t(self.language_getter(), "missing_title")
            self.page.update()
            return
        show_review_editor(
            self.page, title, self.reviews.get(title_id), self.save_review,
            self.share_current, self.language_getter,
        )

    def mark_watched(self, title_id):
        self.store.mark_watched(title_id)
        self.watched_ids.add(title_id)
        self.on_change()
        self.status_text.value = t(self.language_getter(), "added_history")
        self.page.update()
        self.open_editor(title_id)

    def remove_watched(self, title_id):
        self.store.remove_watched(title_id)
        self.watched_ids.discard(title_id)
        self.reviews.pop(title_id, None)
        self.on_change()
        self.status_text.value = t(self.language_getter(), "removed_history")
        self.page.update()
