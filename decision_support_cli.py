#!/usr/bin/env python3
"""CLI de teste, em texto, para o módulo de apoio à decisão da Artemis.

Uso:
    python decision_support_cli.py

Provedor de LLM controlado pela variável de ambiente ARTEMIS_LLM_PROVIDER:
    mock   -> offline, determinístico (padrão, não precisa de chave/API)
    claude -> API da Anthropic (precisa de ANTHROPIC_API_KEY)
    local  -> servidor local compatível com OpenAI, ex.: Ollama/Llama
              (ARTEMIS_LLM_BASE_URL, ARTEMIS_LLM_MODEL)

Comandos dentro da conversa:
    /decidir <opção escolhida> | <justificativa>   registra a decisão atual
    /sair                                           encerra a conversa
"""
from core.decision_support import DecisionSupportEngine
from core.memory.database import Database


def main():
    db = Database("data/artemis.db")
    engine = DecisionSupportEngine(db=db)
    session = engine.start_session()

    print("Artemis (apoio à decisão) — digite /sair para encerrar.\n")
    while True:
        try:
            user_message = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_message:
            continue
        if user_message == "/sair":
            break

        if user_message.startswith("/decidir"):
            _, _, payload = user_message.partition(" ")
            chosen, _, rationale = payload.partition("|")
            if not session.project_id:
                print("Artemis: Ainda não identifiquei o projeto desta conversa.\n")
                continue
            last_question = next(
                (m.content for m in reversed(session.history) if m.role == "user"),
                "Decisão",
            )
            decision_id = engine.record_decision(
                session,
                question=last_question,
                chosen_option=chosen.strip(),
                rationale=rationale.strip(),
            )
            print("Artemis: Decisão registrada (#{}).\n".format(decision_id))
            continue

        reply = engine.ask(session, user_message)
        print("Artemis: {}\n".format(reply))


if __name__ == "__main__":
    main()
