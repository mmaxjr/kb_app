"""
Criar novo ticket.

Dois modos, escolhidos pelo switch "Salvar somente no dispositivo":
- Desligado (padrão): salva local (SQLite) e tenta sincronizar com o
  Notion em background.
- Ligado: salva só no cache local, nunca tenta enviar ao Notion.
"""
import threading
import uuid

from kivy.clock import Clock
from kivymd.uix.screen import MDScreen

from models.ticket import Ticket
from utils.ui import mostrar_aviso


class TicketCreateScreen(MDScreen):
    def criar_ticket(self):
        titulo = self.ids.titulo_field.text.strip()
        if not titulo:
            mostrar_aviso("Título é obrigatório")
            return

        salvar_so_no_dispositivo = self.ids.local_only_switch.active

        ticket = Ticket(
            id=str(uuid.uuid4()),
            titulo=titulo,
            descricao=self.ids.descricao_field.text,
            solucao=self.ids.solucao_field.text,
            categoria=self.ids.categoria_field.text,
            tags=[t.strip() for t in self.ids.tags_field.text.split(",") if t.strip()],
            sincronizado=salvar_so_no_dispositivo,  # local_only nunca fica "pendente"
            local_only=salvar_so_no_dispositivo,
        )

        self.manager.cache_service.save_local(ticket)
        self._limpar_campos()

        if salvar_so_no_dispositivo:
            mostrar_aviso("Nota salva somente no dispositivo")
        else:
            mostrar_aviso("Nota salva localmente, sincronizando com o Notion...")
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
            # Só aqui dá pra garantir que realmente chegou no Notion --
            # o aviso de "sincronizando..." mostrado na hora de salvar não
            # prova que deu certo, então confirma com um segundo aviso
            # quando o envio termina de verdade.
            Clock.schedule_once(lambda dt: mostrar_aviso("Sincronizado com o Notion"))
        except Exception:
            # Continua marcado como não sincronizado (sincronizado=False
            # no cache local) -- a nota não se perde, só não subiu ainda.
            Clock.schedule_once(
                lambda dt: mostrar_aviso("Sem conexão: nota ficou salva só no dispositivo por enquanto")
            )

    def _limpar_campos(self):
        self.ids.titulo_field.text = ""
        self.ids.descricao_field.text = ""
        self.ids.solucao_field.text = ""
        self.ids.categoria_field.text = ""
        self.ids.tags_field.text = ""
        self.ids.local_only_switch.active = False

    def cancelar(self):
        self._limpar_campos()
        self.manager.current = "ticket_list"
