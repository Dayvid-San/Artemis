import os

from .base import LLMProvider
from .mock_provider import MockProvider

_KNOWN_PROVIDERS = ("claude", "local", "mock")


def get_llm_provider(name: str = None, **kwargs) -> LLMProvider:
    """Constrói um LLMProvider pelo nome.

    name pode ser:
      - "claude": API da Anthropic
      - "local" (ou "llama"/"openai-compatible"): qualquer endpoint local
        compatível com a API da OpenAI (ex.: Ollama rodando Llama)
      - "mock": provedor offline e determinístico, usado em testes

    Se name não for informado, usa a variável de ambiente
    ARTEMIS_LLM_PROVIDER e, na ausência dela, "mock".
    """
    name = (name or os.environ.get("ARTEMIS_LLM_PROVIDER") or "mock").lower()

    if name == "claude":
        try:
            from .claude_provider import ClaudeProvider
        except ImportError as exc:
            raise ImportError(
                "O pacote 'anthropic' é necessário para o provedor 'claude'. "
                "Instale com: pip install anthropic"
            ) from exc
        return ClaudeProvider(**kwargs)

    if name in ("local", "llama", "openai-compatible"):
        from .openai_compatible_provider import OpenAICompatibleProvider

        return OpenAICompatibleProvider(**kwargs)

    if name == "mock":
        return MockProvider(**kwargs)

    raise ValueError(
        "Provedor de LLM desconhecido: '{}'. Opções: {}".format(
            name, ", ".join(_KNOWN_PROVIDERS)
        )
    )
