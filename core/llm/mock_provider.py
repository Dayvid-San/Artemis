from typing import List, Optional

from .base import LLMProvider, Message


class MockProvider(LLMProvider):
    """Provedor offline e determinístico, usado em testes e no desenvolvimento
    local quando nenhuma chave de API ou servidor local está configurado.
    Nunca faz chamadas de rede.
    """

    def __init__(self, canned_reply: Optional[str] = None):
        self._canned_reply = canned_reply

    def generate(self, messages: List[Message], system: str = "") -> str:
        if self._canned_reply is not None:
            return self._canned_reply

        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"), ""
        )
        return (
            "[MockProvider] O que te faz pensar nisso agora, e o que muda se "
            "você esperar mais uma semana? (em resposta a: \"{}\")"
        ).format(last_user)
