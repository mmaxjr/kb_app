"""
Criar novo ticket. Salva local (SQLite) imediatamente e tenta
sincronizar com o Notion em background.
"""
import threading
import uuid

from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar

from models.ticket import Ticket


class TicketCreateScreen(MDScreen):
    def criar_ticket(self):
        titulo = self.ids.titulo_field.text.strip()
        if not titulo:
            Snackbar(text="Título é obrigatório").open()
            return

        ticket = Ticket(
            id=str(uuid.uuid4()),
            titulo=titulo,
            descricao=self.ids.descricao_field.text,
            solucao=self.ids.solucao_field.text,
            categoria=self.ids.categoria_field.text,
            tags=[t.strip() for t in self.ids.tags_field.text.split(",") if t.strip()],
            sincronizado=False,
        )

        self.manager.cache_service.save_local(ticket)
        self._limpar_campos()
        Snackbar(text="Ticket salvo localmente").open()

        threading.Thread(target=self._sincronizar_thread, args=(ticket,), daemon=True).start()
        self.manager.current = "ticket_list"

    def _sincronizar_thread(self, ticket: Ticket):
        notion_service = self.manager.notion_service
        cache_service = self.manager.cache_service
        try:
            pagina = notion_service.create_ticket(
                ticket.titulo, ticket.descricao, ticket.solucao,
                ticket.categoria, ticket.tags,
            )
            # Substitui o id local (uuid) pelo id real da página do Notion
            cache_service.delete_local(ticket.id)
            ticket.id = pagina["id"]
            ticket.sincronizado = True
            cache_service.save_local(ticket)
        except Exception:
            pass  # continua marcado como não sincronizado; tenta de novo depois

    def _limpar_campos(self):
        self.ids.titulo_field.text = ""
        self.ids.descricao_field.text = ""
        self.ids.solucao_field.text = ""
        self.ids.categoria_field.text = ""
        self.ids.tags_field.text = ""

    def cancelar(self):
        self._limpar_campos()
        self.manager.current = "ticket_list"
