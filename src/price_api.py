"""Tentativa conservadora de leitura de preços mensais nas páginas oficiais."""

import asyncio
import html
import logging
import re

import httpx2 as httpx


log = logging.getLogger("app.price_api")


def extract_monthly_brl(page_html):
    text = html.unescape(page_html)
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    patterns = (
        r"R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})\s*(?:/|por\s+)?\s*(?:ao\s+)?m[eê]s\b",
        r"(?:m[eê]s|mensal)[^R$]{0,35}R\$\s*([0-9]{1,3}(?:\.[0-9]{3})*,[0-9]{2})",
    )
    values = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            raw = match.group(1).replace(".", "").replace(",", ".")
            try:
                price = float(raw)
            except ValueError:
                continue
            if 5 <= price <= 500:
                values.add(round(price, 2))
    return (next(iter(values)) if len(values) == 1 else None), len(values)


async def verify_official_prices(store, services, price_sources):
    updated = 0
    results = []
    attempted = set()
    try:
        async with httpx.AsyncClient(timeout=12, follow_redirects=True) as client:
            for service in services:
                name = service["name"]
                url = price_sources[name]
                attempted.add(name)
                try:
                    response = await client.get(url, headers={"accept": "text/html,application/xhtml+xml"})
                    response.raise_for_status()
                    price, matches = extract_monthly_brl(response.text)
                    if price is not None:
                        message = f"R$ {price:.2f} extraído da página oficial."
                        store.update_price(name, url, "atualizado automaticamente", price)
                        updated += 1
                    elif matches > 1:
                        message = "Mais de um preço mensal encontrado; valor anterior mantido para revisão."
                        store.update_price(name, url, "ambíguo; valor anterior mantido")
                    else:
                        message = "Preço mensal não identificado; valor anterior mantido."
                        store.update_price(name, url, "não identificado; valor anterior mantido")
                except asyncio.CancelledError:
                    raise
                except BaseException as error:
                    message = f"Consulta indisponível ({type(error).__name__}); valor anterior mantido."
                    store.update_price(name, url, "falha na consulta; valor anterior mantido")
                    log.info("Preço de %s não consultado (%s); mantendo o salvo", name, type(error).__name__)
                results.append(f"{name}: {message}")
    except asyncio.CancelledError:
        raise
    except BaseException as error:
        # Mesmo uma falha ao abrir o cliente não altera nenhum preço já registrado.
        for service in services:
            name = service["name"]
            if name not in attempted:
                store.update_price(name, price_sources[name], "cliente indisponível; valor anterior mantido")
                results.append(f"{name}: consulta indisponível ({type(error).__name__}); valor anterior mantido.")
        log.warning("Cliente de preços indisponível: %s", type(error).__name__)

    failed = sum("mantido" in result or "indisponível" in result or "não identificado" in result or "ambíguo" in result for result in results)
    detail = f"{updated} de {len(services)} preços atualizados; {failed} mantidos sem alteração por falta de leitura inequívoca."
    overall_status = "verificado" if not failed else "parcial; valores anteriores preservados"
    store.record_source_status("Preços", overall_status, detail)
    return {"updated": updated, "detail": detail, "results": results}
