import os

import ollama

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")


class OllamaUnavailableError(Exception):
    """Raised when the local Ollama server can't be reached or errors out.
    Callers should catch this and degrade gracefully - never let it surface
    as a raw traceback to an operator mid-demo."""


class OllamaClient:
    """Thin wrapper around a local Ollama server."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._client = ollama.Client()

    def generate(self, prompt: str, system: str | None = None, temperature: float = 0.1) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat(
                model=self.model, messages=messages, options={"temperature": temperature}
            )
        except Exception as e:
            raise OllamaUnavailableError(str(e)) from e

        return response["message"]["content"].strip()


ollama_client = OllamaClient()
