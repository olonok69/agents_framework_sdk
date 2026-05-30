from __future__ import annotations

import requests


def call_backend(api_url: str, endpoint: str, payload: dict) -> dict:
    url = f"{api_url.rstrip('/')}/{endpoint.lstrip('/')}"
    response = requests.post(url, json=payload, timeout=1200)
    response.raise_for_status()
    return response.json()
