import datetime
import json
import os
import sqlite3
from typing import Dict, List, Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT DEFAULT '',
    status TEXT DEFAULT '',
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS constraints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS people (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    role TEXT DEFAULT '',
    notes TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    options TEXT DEFAULT '[]',
    tradeoffs TEXT DEFAULT '[]',
    chosen_option TEXT DEFAULT '',
    rationale TEXT DEFAULT '',
    created_at TEXT NOT NULL
);
"""


def _now() -> str:
    return datetime.datetime.utcnow().isoformat()


class Database:
    """Acesso ao banco de dados pessoal de Dayvid: projetos, restrições,
    pessoas envolvidas e o histórico de decisões já tomadas.

    Usa SQLite por padrão (arquivo local, sem servidor). Pode rodar em
    memória (path=":memory:") para testes.
    """

    def __init__(self, path: str = ":memory:"):
        if path != ":memory:":
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)

        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA foreign_keys = ON;")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self):
        self._conn.close()

    # --- Projetos ---------------------------------------------------

    def add_project(self, name: str, description: str = "", status: str = "") -> int:
        cursor = self._conn.execute(
            "INSERT INTO projects (name, description, status, created_at) "
            "VALUES (?, ?, ?, ?)",
            (name, description, status, _now()),
        )
        self._conn.commit()
        return cursor.lastrowid

    def list_projects(self) -> List[Dict]:
        rows = self._conn.execute("SELECT * FROM projects ORDER BY name").fetchall()
        return [dict(row) for row in rows]

    def get_project_by_name(self, name: str) -> Optional[Dict]:
        row = self._conn.execute(
            "SELECT * FROM projects WHERE lower(name) = lower(?)", (name,)
        ).fetchone()
        return dict(row) if row else None

    # --- Restrições ---------------------------------------------------

    def add_constraint(self, project_id: int, description: str) -> int:
        cursor = self._conn.execute(
            "INSERT INTO constraints (project_id, description, created_at) "
            "VALUES (?, ?, ?)",
            (project_id, description, _now()),
        )
        self._conn.commit()
        return cursor.lastrowid

    def list_constraints(self, project_id: int) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM constraints WHERE project_id = ? ORDER BY id", (project_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    # --- Pessoas --------------------------------------------------------

    def add_person(
        self, project_id: int, name: str, role: str = "", notes: str = ""
    ) -> int:
        cursor = self._conn.execute(
            "INSERT INTO people (project_id, name, role, notes) VALUES (?, ?, ?, ?)",
            (project_id, name, role, notes),
        )
        self._conn.commit()
        return cursor.lastrowid

    def list_people(self, project_id: int) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM people WHERE project_id = ? ORDER BY id", (project_id,)
        ).fetchall()
        return [dict(row) for row in rows]

    # --- Decisões -------------------------------------------------------

    def record_decision(
        self,
        project_id: int,
        question: str,
        chosen_option: str,
        rationale: str,
        options: Optional[List[str]] = None,
        tradeoffs: Optional[List[str]] = None,
    ) -> int:
        cursor = self._conn.execute(
            "INSERT INTO decisions "
            "(project_id, question, options, tradeoffs, chosen_option, rationale, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                project_id,
                question,
                json.dumps(options or [], ensure_ascii=False),
                json.dumps(tradeoffs or [], ensure_ascii=False),
                chosen_option,
                rationale,
                _now(),
            ),
        )
        self._conn.commit()
        return cursor.lastrowid

    def list_decisions(self, project_id: int, limit: int = 5) -> List[Dict]:
        rows = self._conn.execute(
            "SELECT * FROM decisions WHERE project_id = ? "
            "ORDER BY created_at DESC LIMIT ?",
            (project_id, limit),
        ).fetchall()
        decisions = []
        for row in rows:
            decision = dict(row)
            decision["options"] = json.loads(decision["options"])
            decision["tradeoffs"] = json.loads(decision["tradeoffs"])
            decisions.append(decision)
        return decisions

    # --- Contexto agregado -----------------------------------------------

    def get_project_context(self, project_id: int) -> Dict:
        """Reúne tudo que a Artemis precisa saber sobre um projeto antes de
        ajudar em uma decisão: estado atual, restrições, pessoas envolvidas
        e as decisões mais recentes já registradas.
        """
        row = self._conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise ValueError("Projeto {} não encontrado.".format(project_id))

        return {
            "project": dict(row),
            "constraints": self.list_constraints(project_id),
            "people": self.list_people(project_id),
            "decisions": self.list_decisions(project_id),
        }
