"""
Cache local em SQLite para funcionar offline.

Fluxo padrão: cria-se um ticket offline -> salva no SQLite local com
sincronizado=0 -> quando há internet, sobe para o Notion e marca
sincronizado=1.

Fluxo "somente no dispositivo" (local_only=1): o ticket nunca é
enviado ao Notion, fica só no cache local (sincronizado é marcado
True apenas pra impedir tentativas de sync em background).
"""
import sqlite3
import threading

from models.ticket import Ticket


class CacheService:
    def __init__(self, db_path: str = "cache.db"):
        # check_same_thread=False é necessário porque este cache é acessado
        # de threads de fundo (carregar a lista, sincronizar com o Notion,
        # salvar edição) além da thread principal do Kivy. Sem isso, o
        # sqlite3 levanta "SQLite objects created in a thread can only be
        # used in that same thread" toda vez que uma thread de fundo chama
        # qualquer método daqui -- uma exceção que, por acontecer fora do
        # loop de eventos do Kivy, não é pega pelo ExceptionManager e falha
        # silenciosamente (a lista não carrega, a nota não salva, sem
        # nenhum aviso na tela). O Lock garante que, mesmo com várias
        # threads, só uma mexe na conexão por vez.
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._lock = threading.Lock()
        self._create_table()
        self._migrate()

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
                sincronizado INTEGER DEFAULT 0,
                local_only INTEGER DEFAULT 0,
                criado_em TEXT DEFAULT ''
            )
            """
        )
        self.conn.commit()

    def _migrate(self):
        """Adiciona colunas em bancos criados antes delas existirem
        (installs anteriores do app), sem apagar dados."""
        for coluna_sql in (
            "ALTER TABLE tickets ADD COLUMN local_only INTEGER DEFAULT 0",
            "ALTER TABLE tickets ADD COLUMN criado_em TEXT DEFAULT ''",
        ):
            try:
                self.conn.execute(coluna_sql)
                self.conn.commit()
            except sqlite3.OperationalError:
                pass  # coluna já existe

    def save_local(self, ticket: Ticket) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO tickets VALUES (?,?,?,?,?,?,?,?,?)",
                (
                    ticket.id,
                    ticket.titulo,
                    ticket.descricao,
                    ticket.solucao,
                    ticket.categoria,
                    ",".join(ticket.tags),
                    int(ticket.sincronizado),
                    int(ticket.local_only),
                    ticket.criado_em,
                ),
            )
            self.conn.commit()

    def get_all(self) -> list[Ticket]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT id, titulo, descricao, solucao, categoria, tags, "
                "sincronizado, local_only, criado_em FROM tickets"
            ).fetchall()
        return [Ticket.from_row(r) for r in rows]

    def get_unsynced(self) -> list[Ticket]:
        """Tickets pendentes de envio ao Notion (nunca inclui local_only)."""
        with self._lock:
            rows = self.conn.execute(
                "SELECT id, titulo, descricao, solucao, categoria, tags, "
                "sincronizado, local_only, criado_em FROM tickets "
                "WHERE sincronizado = 0 AND local_only = 0"
            ).fetchall()
        return [Ticket.from_row(r) for r in rows]

    def get_local_only(self) -> list[Ticket]:
        """Tickets salvos só no dispositivo (não existem no Notion)."""
        with self._lock:
            rows = self.conn.execute(
                "SELECT id, titulo, descricao, solucao, categoria, tags, "
                "sincronizado, local_only, criado_em FROM tickets WHERE local_only = 1"
            ).fetchall()
        return [Ticket.from_row(r) for r in rows]

    def mark_synced(self, ticket_id: str) -> None:
        with self._lock:
            self.conn.execute(
                "UPDATE tickets SET sincronizado = 1 WHERE id = ?", (ticket_id,)
            )
            self.conn.commit()

    def delete_local(self, ticket_id: str) -> None:
        with self._lock:
            self.conn.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
            self.conn.commit()
