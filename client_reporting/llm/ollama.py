from __future__ import annotations

from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class OllamaConfig:
    model: str = "llama3.1"
    base_url: str = "http://localhost:11434"
    timeout_seconds: int = 45


class OllamaClient:
    def __init__(self, config: OllamaConfig | None = None) -> None:
        self.config = config or OllamaConfig()

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.config.base_url}/api/generate",
            json={
                "model": self.config.model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.25, "top_p": 0.8},
            },
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
        return str(payload.get("response", "")).strip()
