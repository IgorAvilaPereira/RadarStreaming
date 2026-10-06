"""Compartilha imagem composta com capa, nota e resenha do usuário."""

import flet as ft

from i18n import t


def _review_caption(title, rating, review_text, language="pt-BR"):
    stars = "★" * int(rating) + "☆" * (5 - int(rating))
    kind = t(language, "movie") if title["kind"] == "Filme" else t(language, "series")
    synopsis_label = "Synopsis" if language == "en" else "Sinopse"
    cover_note = "Illustrative poster. Availability may vary by region." if language == "en" else "Capa ilustrativa. Disponibilidade pode variar por região."
    shared = "Shared with Streaming Radar" if language == "en" else "Compartilhado pelo Radar de Streaming"
    default_review = "My review is saved in Streaming Radar." if language == "en" else "Minha avaliação está salva no Radar de Streaming."
    return "\n".join(
        part
        for part in [
            f"{title['title']} · {kind} ({title['year']})",
            stars,
            review_text.strip() or default_review,
            f"{synopsis_label}: {title['synopsis']}",
            cover_note,
            shared,
        ]
        if part
    )


async def share_review(share_service, title, rating, review_text, image_data, language="pt-BR"): 
    if not image_data:
        raise ValueError("A imagem composta não foi gerada.")
    await share_service.share_files(
        files=[
            ft.ShareFile.from_bytes(
                data=image_data,
                mime_type="image/png",
                name="resenha-radar.png",
            )
        ],
        title=(f"Review of {title['title']}" if language == "en" else f"Resenha de {title['title']}"),
        text=_review_caption(title, rating, review_text, language),
    )
    return "Imagem da resenha com capa, nota e opinião enviada ao menu de compartilhamento."
