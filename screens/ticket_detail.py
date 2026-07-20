"""
Visualizar / editar um ticket existente.

Notas "somente no dispositivo" (local_only) são salvas direto no
cache local ao editar, sem tentar falar com o Notion. As demais
seguem o fluxo normal (update via Notion API).

Também permite exportar a nota atual (com as edições em tela, mesmo
que ainda não salvas) para .txt ou .pdf.
"""
import os
import threading

from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen

from models.ticket import Ticket
from services.export_service import export_pdf, export_txt
from utils.ui import mostrar_aviso


class TicketDetailScreen(MDScreen):
    ticket_id = StringProperty("")
    local_only = BooleanProperty(False)

    def on_pre_enter(self, *args):
        self.carregar_ticket()

    def carregar_ticket(self):
        cache_service = self.manager.cache_service
        tickets = {t.id: t for t in cache_service.get_all()}
        ticket = tickets.get(self.ticket_id)
        self.local_only = bool(ticket.local_only) if ticket else False
        if ticket:
            self.ids.titulo_field.text = ticket.titulo
            self.ids.descricao_field.text = ticket.descricao
            self.ids.solucao_field.text = ticket.solucao
            self.ids.categoria_field.text = ticket.categoria
            self.ids.tags_field.text = ",".join(ticket.tags)

    def _ticket_atual(self) -> Ticket:
        """Monta um Ticket a partir do que está em tela agora (inclui
        edições ainda não salvas — útil para exportar antes de salvar)."""
        return Ticket(
            id=self.ticket_id,
            titulo=self.ids.titulo_field.text,
            descricao=self.ids.descricao_field.text,
            solucao=self.ids.solucao_field.text,
            categoria=self.ids.categoria_field.text,
            tags=[t.strip() for t in self.ids.tags_field.text.split(",") if t.strip()],
            local_only=self.local_only,
        )

    def salvar_edicao(self):
        if self.local_only:
            self._salvar_local()
        else:
            threading.Thread(target=self._salvar_thread, daemon=True).start()

    def _salvar_local(self):
        cache_service = self.manager.cache_service
        ticket = self._ticket_atual()
        ticket.sincronizado = True
        ticket.local_only = True
        cache_service.save_local(ticket)
        mostrar_aviso("Nota salva no dispositivo")

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
            Clock.schedule_once(lambda dt: mostrar_aviso("Ticket atualizado"))
        except Exception:
            Clock.schedule_once(lambda dt: mostrar_aviso("Falha ao atualizar (sem conexão?)"))

    def exportar_txt(self):
        threading.Thread(target=self._exportar_thread, args=("txt",), daemon=True).start()

    def exportar_pdf(self):
        threading.Thread(target=self._exportar_thread, args=("pdf",), daemon=True).start()

    def _exportar_thread(self, formato: str):
        app = MDApp.get_running_app()
        dest_dir = os.path.join(app.user_data_dir, "exports")
        ticket = self._ticket_atual()
        try:
            if formato == "txt":
                path = export_txt(ticket, dest_dir)
            else:
                path = export_pdf(ticket, dest_dir)
            Clock.schedule_once(lambda dt: mostrar_aviso(f"Exportado: {path}"))
        except Exception as e:
            msg = f"Falha ao exportar {formato.upper()}: {e}"
            Clock.schedule_once(lambda dt: mostrar_aviso(msg))

    def voltar(self):
        self.manager.current = "ticket_list"
