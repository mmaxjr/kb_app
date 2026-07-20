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
    sincronizado = BooleanProperty(True)
    criado_em = StringProperty("")

    def on_pre_enter(self, *args):
        self.carregar_ticket()

    def carregar_ticket(self):
        cache_service = self.manager.cache_service
        tickets = {t.id: t for t in cache_service.get_all()}
        ticket = tickets.get(self.ticket_id)
        self.local_only = bool(ticket.local_only) if ticket else False
        # Mostra o status real: "sincronizado" só vira True quando o
        # Notion de fato confirmou o envio (ver ticket_create.py /
        # cache_service.py) -- antes disso a nota existe só no cache
        # local, mesmo não sendo "somente no dispositivo".
        self.sincronizado = bool(ticket.sincronizado) if ticket else True
        self.criado_em = ticket.criado_em if ticket else ""
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
            criado_em=self.criado_em,  # editar não deve mudar a data de criação
        )

    def salvar_edicao(self):
        # IMPORTANTE: salva no cache local SEMPRE, antes de qualquer coisa
        # -- é isso que faltava. Antes, uma nota "sincronizada com o
        # Notion" só era salva DE VERDADE se a chamada à API do Notion
        # desse certo; se falhasse (ou o database_id estivesse errado),
        # a edição inteira era descartada e a nota voltava pro estado
        # antigo na próxima vez que a tela abrisse -- exatamente o "não
        # salva, volta do jeito que criei" relatado.
        cache_service = self.manager.cache_service
        ticket = self._ticket_atual()
        ticket.local_only = self.local_only

        if self.local_only:
            ticket.sincronizado = True
            cache_service.save_local(ticket)
            self.sincronizado = True
            mostrar_aviso("Nota salva no dispositivo")
            return

        ticket.sincronizado = False
        cache_service.save_local(ticket)
        self.sincronizado = False
        mostrar_aviso("Alterações salvas no dispositivo, sincronizando com o Notion...")
        threading.Thread(target=self._salvar_thread, args=(ticket,), daemon=True).start()

    def _salvar_thread(self, ticket: Ticket):
        notion_service = self.manager.notion_service
        cache_service = self.manager.cache_service
        try:
            notion_service.update_ticket(
                ticket.id,
                titulo=ticket.titulo,
                descricao=ticket.descricao,
                solucao=ticket.solucao,
                categoria=ticket.categoria,
                tags=ticket.tags,
            )
            ticket.sincronizado = True
            cache_service.save_local(ticket)
            Clock.schedule_once(lambda dt: self._marcar_sincronizado(True))
            Clock.schedule_once(lambda dt: mostrar_aviso("Sincronizado com o Notion"))
        except Exception as e:
            Clock.schedule_once(lambda dt: self._marcar_sincronizado(False))
            Clock.schedule_once(
                lambda dt: mostrar_aviso(f"Salvo no dispositivo -- não sincronizou com o Notion ({e})")
            )

    def _marcar_sincronizado(self, valor: bool):
        # Só atualiza a tela se o usuário ainda estiver olhando essa
        # mesma nota (evita sobrescrever o estado se ele já saiu daqui).
        if self.manager.current == "ticket_detail":
            self.sincronizado = valor

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
