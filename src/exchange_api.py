"""Consulta assíncrona da cotação BRL/USD; falhas são tratadas pela tela."""

import httpx2 as httpx


async def fetch_brl_to_usd():
    async with httpx.AsyncClient(timeout=12) as client:
        response = await client.get(
            "https://api.frankfurter.dev/v1/latest",
            params={"base": "BRL", "symbols": "USD"},
        )
        response.raise_for_status()
        payload = response.json()
        rate = float(payload["rates"]["USD"])
        if rate <= 0:
            raise ValueError("Cotação BRL/USD inválida")
        return rate, payload.get("date", "")
