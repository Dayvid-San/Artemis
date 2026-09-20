import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.memory.database import Database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")

    def tearDown(self):
        self.db.close()

    def test_add_and_get_project_by_name_is_case_insensitive(self):
        self.db.add_project("Tyto Club", description="Clube de assinatura", status="ativo")

        project = self.db.get_project_by_name("tyto club")

        self.assertIsNotNone(project)
        self.assertEqual(project["name"], "Tyto Club")
        self.assertEqual(project["status"], "ativo")

    def test_unknown_project_returns_none(self):
        self.assertIsNone(self.db.get_project_by_name("Não existe"))

    def test_project_context_aggregates_constraints_people_and_decisions(self):
        project_id = self.db.add_project("EngScan")
        self.db.add_constraint(project_id, "Orçamento de marketing congelado até Q2")
        self.db.add_person(project_id, "Marina", role="sócia")
        self.db.record_decision(
            project_id,
            question="Contratar mais um dev agora?",
            chosen_option="Esperar mais um mês",
            rationale="Caixa apertado até fechar o próximo contrato",
            options=["Contratar agora", "Esperar mais um mês"],
            tradeoffs=["Velocidade vs. runway"],
        )

        context = self.db.get_project_context(project_id)

        self.assertEqual(context["project"]["name"], "EngScan")
        self.assertEqual(len(context["constraints"]), 1)
        self.assertEqual(context["people"][0]["name"], "Marina")
        self.assertEqual(len(context["decisions"]), 1)
        self.assertEqual(context["decisions"][0]["chosen_option"], "Esperar mais um mês")
        self.assertEqual(
            context["decisions"][0]["tradeoffs"], ["Velocidade vs. runway"]
        )

    def test_get_project_context_for_unknown_project_raises(self):
        with self.assertRaises(ValueError):
            self.db.get_project_context(999)

    def test_list_decisions_respects_limit_and_order(self):
        project_id = self.db.add_project("LZ Informática")
        for i in range(3):
            self.db.record_decision(
                project_id,
                question="Decisão {}".format(i),
                chosen_option="opção {}".format(i),
                rationale="motivo {}".format(i),
            )

        decisions = self.db.list_decisions(project_id, limit=2)

        self.assertEqual(len(decisions), 2)
        # Mais recente primeiro.
        self.assertEqual(decisions[0]["question"], "Decisão 2")


if __name__ == "__main__":
    unittest.main()
