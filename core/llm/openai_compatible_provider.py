import os
from typing import List, Optional

import requests

from .base import LLMProvider, Message


class OpenAICompatibleProvider(LLMProvider):
    """Fala com qualquer endpoint de chat compatível com a API da OpenAI
    (Ollama, LM Studio, llama.cpp server, vLLM, ...).

    É assim que a Artemis roda sobre um modelo open source local, como
    Llama, sem precisar de nenhuma mudança na lógica de apoio à decisão.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self._base_url = (
            base_url
            or os.environ.get("ARTEMIS_LLM_BASE_URL")
            or "http://localhost:11434/v1"
        ).rstrip("/")
        self._model = model or os.environ.get("ARTEMIS_LLM_MODEL") or "llama3"
        self._api_key = (
            api_key or os.environ.get("ARTEMIS_LLM_API_KEY") or "not-needed"
        )
        self._timeout = timeout

    def generate(self, messages: List[Message], system: str = "") -> str:
        payload_messages = []
        if system:
            payload_messages.append({"role": "system", "content": system})
        payload_messages.extend(
            {"role": m.role, "content": m.content} for m in messages
        )

        response = requests.post(
            "{}/chat/completions".format(self._base_url),
            headers={"Authorization": "Bearer {}".format(self._api_key)},
            json={"model": self._model, "messages": payload_messages},
            timeout=self._timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
