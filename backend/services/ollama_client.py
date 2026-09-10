import os

import ollama

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")


class OllamaClient:
    """Thin wrapper around a local Ollama server."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._client = ollama.Client()

    def generate(self, prompt: str, system: str | None = None) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = self._client.chat(model=self.model, messages=messages)
        return response["message"]["content"].strip()


ollama_client = OllamaClient()
