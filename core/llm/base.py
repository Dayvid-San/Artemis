from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class Message:
    role: str  # "user" ou "assistant"
    content: str


class LLMProvider(ABC):
    """Interface comum que todo backend de linguagem precisa implementar.

    O motor de apoio à decisão só conversa com esta interface, então trocar
    a Claude API por um servidor local de Llama (ou qualquer outro modelo)
    nunca precisa tocar na lógica de raciocínio ou no banco de dados.
    """

    @abstractmethod
    def generate(self, messages: List[Message], system: str = "") -> str:
        """Retorna a resposta do assistente para a conversa fornecida."""
        raise NotImplementedError
