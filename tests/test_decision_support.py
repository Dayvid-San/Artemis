import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.decision_support import DecisionSupportEngine
from core.llm.mock_provider import MockProvider
from core.memory.database import Database


class TestDecisionSupportEngine(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.project_id = self.db.add_project(
            "Tyto Club", description="Clube de assinatura de vinhos", status="ativo"
        )
        self.db.add_constraint(self.project_id, "Sem orçamento para novas contratações")
        self.llm = MockProvider(canned_reply="O que muda se você esperar mais uma semana?")
        self.engine = DecisionSupportEngine(db=self.db, llm=self.llm)

    def test_identifies_known_project_mentioned_in_message(self):
        session = self.engine.start_session()

        self.engine.ask(session, "Preciso decidir algo sobre o Tyto Club")

        self.assertEqual(session.project_id, self.project_id)
        self.assertEqual(session.project_name, "Tyto Club")

    def test_does_not_identify_unknown_project(self):
        session = self.engine.start_session()

        self.engine.ask(session, "Preciso decidir algo sobre um projeto novo")

        self.assertIsNone(session.project_id)

    def test_ask_appends_user_and_assistant_turns_to_history(self):
        session = self.engine.start_session()

        reply = self.engine.ask(session, "Sobre o Tyto Club: devo trocar de fornecedor?")

        self.assertEqual(reply, "O que muda se você esperar mais uma semana?")
        self.assertEqual(len(session.history), 2)
        self.assertEqual(session.history[0].role, "user")
        self.assertEqual(session.history[1].role, "assistant")

    def test_record_decision_without_project_raises(self):
        session = self.engine.start_session()

        with self.assertRaises(ValueError):
            self.engine.record_decision(
                session, question="q", chosen_option="a", rationale="r"
            )

    def test_record_decision_persists_to_database(self):
        session = self.engine.start_session()
        self.engine.ask(session, "Sobre o Tyto Club, devo trocar de fornecedor?")

        decision_id = self.engine.record_decision(
            session,
            question="Trocar de fornecedor?",
            chosen_option="Manter o atual por mais um trimestre",
            rationale="Trocar agora arriscaria o lançamento de outubro",
            options=["Trocar agora", "Manter o atual"],
            tradeoffs=["Custo vs. risco de lançamento"],
        )

        decisions = self.db.list_decisions(self.project_id)
        self.assertEqual(len(decisions), 1)
        self.assertEqual(decisions[0]["id"], decision_id)
        self.assertEqual(
            decisions[0]["chosen_option"], "Manter o atual por mais um trimestre"
        )

    def test_context_block_includes_constraints(self):
        session = self.engine.start_session()
        session.project_id = self.project_id
        session.project_name = "Tyto Club"

        context = self.engine._context_block(session)

        self.assertIn("Sem orçamento para novas contratações", context)


if __name__ == "__main__":
    unittest.main()
