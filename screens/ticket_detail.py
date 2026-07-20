"""
Visualizar / editar um ticket existente.
"""
import threading

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar


class TicketDetailScreen(MDScreen):
    ticket_id = StringProperty("")

    def on_pre_enter(self, *args):
        self.carregar_ticket()

    def carregar_ticket(self):
        cache_service = self.manager.cache_service
        tickets = {t.id: t for t in cache_service.get_all()}
        ticket = tickets.get(self.ticket_id)
        if ticket:
            self.ids.titulo_field.text = ticket.titulo
            self.ids.descricao_field.text = ticket.descricao
            self.ids.solucao_field.text = ticket.solucao
            self.ids.categoria_field.text = ticket.categoria
            self.ids.tags_field.text = ",".join(ticket.tags)

    def salvar_edicao(self):
        threading.Thread(target=self._salvar_thread, daemon=True).start()

    def _salvar_thread(self):
        notion_service = self.manager.notion_service
        try:
            notion_service.update_ticket(
                self.ticket_id,
                titulo=self.ids.titulo_field.text,
                descricao=self.ids.descricao_field.text,
                solucao=self.ids.solucao_field.text,
                categoria=self.ids.categoria_field.text,
                tags=[t.strip() for t in self.ids.tags_field.text.split(",") if t.strip()],
            )
            Clock.schedule_once(lambda dt: Snackbar(text="Ticket atualizado").open())
        except Exception:
            Clock.schedule_once(lambda dt: Snackbar(text="Falha ao atualizar (sem conexão?)").open())

    def voltar(self):
        self.manager.current = "ticket_list"
