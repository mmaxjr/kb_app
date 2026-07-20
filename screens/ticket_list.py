"""
Lista de tickets: busca no Notion (com fallback pro cache local se
não houver internet) e permite navegar para detalhe/criação.
"""
import threading

from kivy.clock import Clock
from kivymd.uix.screen import MDScreen

from models.ticket import Ticket
from utils.ui import mostrar_aviso


class TicketListScreen(MDScreen):
    def on_pre_enter(self, *args):
        self.carregar_tickets()

    def carregar_tickets(self):
        threading.Thread(target=self._carregar_thread, daemon=True).start()

    def _carregar_thread(self):
        notion_service = self.manager.notion_service
        cache_service = self.manager.cache_service
        tickets = []
        try:
            resultado = notion_service.list_tickets()
            tickets = [Ticket.from_notion_page(p) for p in resultado.get("results", [])]
            for t in tickets:
                cache_service.save_local(t)
            # Notas "somente no dispositivo" nunca existem no Notion, então
            # não vêm nesse resultado — precisam ser mescladas de volta.
            tickets += cache_service.get_local_only()
        except Exception:
            # Sem internet ou erro na API: usa o cache local (Notion + local-only)
            tickets = cache_service.get_all()

        Clock.schedule_once(lambda dt: self._popular_lista(tickets))

    def _popular_lista(self, tickets):
        self.ids.tickets_list.clear_widgets()
        for t in tickets:
            self._adicionar_item(t)

    def _adicionar_item(self, ticket: Ticket):
        from kivymd.uix.list import TwoLineListItem

        secondary = ticket.categoria or ""
        if ticket.local_only:
            status = "somente no dispositivo"
        elif ticket.sincronizado:
            status = "sincronizado com o Notion"
        else:
            status = "aguardando sincronizar"
        secondary = f"{secondary}  ·  {status}" if secondary else status

        item = TwoLineListItem(
            text=ticket.titulo or "(sem título)",
            secondary_text=secondary,
            on_release=lambda x, tid=ticket.id: self.abrir_detalhe(tid),
        )
        self.ids.tickets_list.add_widget(item)

    def abrir_detalhe(self, ticket_id: str):
        detalhe = self.manager.get_screen("ticket_detail")
        detalhe.ticket_id = ticket_id
        self.manager.current = "ticket_detail"

    def buscar(self, texto: str):
        if not texto:
            self.carregar_tickets()
            return
        threading.Thread(target=self._buscar_thread, args=(texto,), daemon=True).start()

    def _buscar_thread(self, texto: str):
        notion_service = self.manager.notion_service
        try:
            resultado = notion_service.search_tickets(texto)
            tickets = [Ticket.from_notion_page(p) for p in resultado.get("results", [])]
        except Exception:
            tickets = []
            Clock.schedule_once(lambda dt: mostrar_aviso("Sem conexão para buscar"))
        Clock.schedule_once(lambda dt: self._popular_lista(tickets))

    def ir_para_criar(self):
        self.manager.current = "ticket_create"

    def ir_para_integracoes(self):
        self.manager.current = "integrations"
