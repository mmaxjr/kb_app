"""
Cache local em SQLite para funcionar offline.

Fluxo: cria-se um ticket offline -> salva no SQLite local com
sincronizado=0 -> quando há internet, sobe para o Notion e marca
sincronizado=1.
"""
import sqlite3

from models.ticket import Ticket


class CacheService:
    def __init__(self, db_path: str = "cache.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tickets (
                id TEXT PRIMARY KEY,
                titulo TEXT,
                descricao TEXT,
                solucao TEXT,
                categoria TEXT,
                tags TEXT,
                sincronizado INTEGER DEFAULT 0
            )
            """
        )
        self.conn.commit()

    def save_local(self, ticket: Ticket) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO tickets VALUES (?,?,?,?,?,?,?)",
            (
                ticket.id,
                ticket.titulo,
                ticket.descricao,
                ticket.solucao,
                ticket.categoria,
                ",".join(ticket.tags),
                int(ticket.sincronizado),
            ),
        )
        self.conn.commit()

    def get_all(self) -> list[Ticket]:
        rows = self.conn.execute("SELECT * FROM tickets").fetchall()
        return [Ticket.from_row(r) for r in rows]

    def get_unsynced(self) -> list[Ticket]:
        rows = self.conn.execute(
            "SELECT * FROM tickets WHERE sincronizado = 0"
        ).fetchall()
        return [Ticket.from_row(r) for r in rows]

    def mark_synced(self, ticket_id: str) -> None:
        self.conn.execute(
            "UPDATE tickets SET sincronizado = 1 WHERE id = ?", (ticket_id,)
        )
        self.conn.commit()

    def delete_local(self, ticket_id: str) -> None:
        self.conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        self.conn.commit()
