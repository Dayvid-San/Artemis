import os
from typing import List, Optional

from .base import LLMProvider, Message

DEFAULT_MODEL = "claude-sonnet-5"


class ClaudeProvider(LLMProvider):
    """Provedor que fala com a API da Anthropic (Claude)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_MODEL,
        max_tokens: int = 1024,
    ):
        import anthropic  # importado sob demanda: dependência opcional

        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY não configurada. Defina a variável de "
                "ambiente ou passe api_key= ao criar o ClaudeProvider."
            )

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model
        self._max_tokens = max_tokens

    def generate(self, messages: List[Message], system: str = "") -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=self._max_tokens,
            system=system,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return "".join(
            block.text for block in response.content if block.type == "text"
        )
