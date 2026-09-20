from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.llm import LLMProvider, Message, get_llm_provider
from core.memory.database import Database

from .prompts import build_system_prompt


@dataclass
class DecisionSession:
    """Estado de uma conversa de apoio à decisão em andamento."""

    project_id: Optional[int] = None
    project_name: Optional[str] = None
    history: List[Message] = field(default_factory=list)


class DecisionSupportEngine:
    """Orquestra o fluxo de apoio à decisão descrito no prompt da Artemis:

    1. Dayvid apresenta uma questão ou dilema.
    2. O motor identifica o projeto envolvido e puxa o contexto relevante.
    3. A LLM faz perguntas para entender melhor a situação.
    4. A LLM ajuda a esclarecer trade-offs e implicações.
    5. A decisão é registrada no banco com a justificativa.

    O motor é agnóstico de LLM: qualquer LLMProvider serve, então trocar
    Claude por um modelo local (Llama etc.) não muda nada aqui.
    """

    def __init__(self, db: Optional[Database] = None, llm: Optional[LLMProvider] = None):
        self.db = db or Database()
        self.llm = llm or get_llm_provider()

    def start_session(self) -> DecisionSession:
        return DecisionSession()

    def identify_project(
        self, session: DecisionSession, user_message: str
    ) -> Optional[Dict]:
        """Procura, entre os projetos conhecidos, algum mencionado na
        mensagem do usuário. Não sobrescreve um projeto já identificado.
        """
        if session.project_id is not None:
            return None

        lowered = user_message.lower()
        for project in self.db.list_projects():
            if project["name"].lower() in lowered:
                session.project_id = project["id"]
                session.project_name = project["name"]
                return project
        return None

    def _context_block(self, session: DecisionSession) -> str:
        if session.project_id is None:
            return ""

        context = self.db.get_project_context(session.project_id)
        lines = [
            "Projeto: {}".format(context["project"]["name"]),
            "Status: {}".format(context["project"]["status"] or "não informado"),
            "Descrição: {}".format(
                context["project"]["description"] or "não informada"
            ),
        ]

        if context["constraints"]:
            lines.append("Restrições conhecidas:")
            lines.extend(
                "- {}".format(c["description"]) for c in context["constraints"]
            )

        if context["people"]:
            lines.append("Pessoas envolvidas:")
            lines.extend(
                "- {} ({})".format(p["name"], p["role"] or "papel não informado")
                for p in context["people"]
            )

        if context["decisions"]:
            lines.append("Decisões anteriores relevantes:")
            for d in context["decisions"]:
                lines.append(
                    "- {}: escolheu '{}' porque {}".format(
                        d["question"], d["chosen_option"], d["rationale"]
                    )
                )

        return "\n".join(lines)

    def ask(self, session: DecisionSession, user_message: str) -> str:
        """Envia a mensagem do usuário para a LLM, com o contexto do
        projeto identificado injetado no system prompt, e retorna a
        resposta da Artemis.
        """
        self.identify_project(session, user_message)

        session.history.append(Message(role="user", content=user_message))
        system_prompt = build_system_prompt(self._context_block(session))
        reply = self.llm.generate(session.history, system=system_prompt)
        session.history.append(Message(role="assistant", content=reply))
        return reply

    def record_decision(
        self,
        session: DecisionSession,
        question: str,
        chosen_option: str,
        rationale: str,
        options: Optional[List[str]] = None,
        tradeoffs: Optional[List[str]] = None,
    ) -> int:
        if session.project_id is None:
            raise ValueError(
                "Nenhum projeto identificado nesta conversa; não há onde "
                "registrar a decisão."
            )

        return self.db.record_decision(
            project_id=session.project_id,
            question=question,
            chosen_option=chosen_option,
            rationale=rationale,
            options=options,
            tradeoffs=tradeoffs,
        )
