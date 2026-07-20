"""
Lista de notas: busca no Notion (com fallback pro cache local se não
houver internet), filtra por categoria (chips) e por texto (busca local
instantânea + busca remota ao apertar enter/lupa), e permite navegar
para detalhe/criação.
"""
import threading

from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.card import MDCard
from kivymd.uix.screen import MDScreen
from kivy.properties import BooleanProperty, ColorProperty, StringProperty

from models.ticket import Ticket
from theme import CHIP_COLORS, COLORS
from utils.format import cor_categoria, preview_texto, tempo_relativo
from utils.ui import mostrar_aviso

CATEGORIA_TODAS = "Todas"


class CategoriaChip(MDCard):
    """Chip de filtro por categoria. Não usa ButtonBehavior (quebra o MRO
    junto com MDCard -- ver IntegrationCard em integrations.py); implementa
    o próprio toque do mesmo jeito."""

    nome = StringProperty("")
    selecionado = BooleanProperty(False)

    def __init__(self, **kwargs):
        self.register_event_type("on_release")
        super().__init__(**kwargs)

    def on_release(self, *args):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.collide_point(*touch.pos):
                self.dispatch("on_release")
            return True
        return super().on_touch_up(touch)


class NotaCard(MDCard):
    """Card de uma nota na lista. Mesma técnica de toque do CategoriaChip."""

    ticket_id = StringProperty("")
    categoria = StringProperty("")
    categoria_cor = ColorProperty(COLORS["accent"])
    tempo = StringProperty("")
    titulo_nota = StringProperty("")
    solucao_preview = StringProperty("")

    def __init__(self, **kwargs):
        self.register_event_type("on_release")
        super().__init__(**kwargs)

    def on_release(self, *args):
        pass

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            if self.collide_point(*touch.pos):
                self.dispatch("on_release")
            return True
        return super().on_touch_up(touch)


class TicketListScreen(MDScreen):
    def __init__(self, **kwargs):
        self._tickets_todos = []
        self._categoria_selecionada = CATEGORIA_TODAS
        super().__init__(**kwargs)

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
            # Sem internet, Notion não configurado, ou erro na API: usa o
            # cache local (Notion já baixado antes + local-only)
            tickets = cache_service.get_all()

        Clock.schedule_once(lambda dt: self._popular_lista(tickets))

    def _popular_lista(self, tickets):
        self._tickets_todos = tickets
        self._popular_chips_categoria()
        self._aplicar_filtro()

    def _popular_chips_categoria(self):
        container = self.ids.get("chips_categoria")
        if container is None:
            return
        container.clear_widgets()

        categorias = sorted({t.categoria for t in self._tickets_todos if t.categoria})
        nomes = [CATEGORIA_TODAS] + categorias

        # Se a categoria selecionada não existe mais na lista atual (ex.:
        # a única nota daquela categoria foi apagada), volta pra "Todas".
        if self._categoria_selecionada not in nomes:
            self._categoria_selecionada = CATEGORIA_TODAS

        for nome in nomes:
            chip = CategoriaChip(nome=nome, selecionado=(nome == self._categoria_selecionada))
            chip.bind(on_release=lambda inst, n=nome: self._selecionar_categoria(n))
            container.add_widget(chip)

    def _selecionar_categoria(self, nome: str):
        self._categoria_selecionada = nome
        self._popular_chips_categoria()
        self._aplicar_filtro()

    def _aplicar_filtro(self):
        texto = (self.ids.busca_field.text or "").strip().lower() if self.ids.get("busca_field") else ""

        filtrados = []
        for t in self._tickets_todos:
            if self._categoria_selecionada != CATEGORIA_TODAS and t.categoria != self._categoria_selecionada:
                continue
            if texto:
                alvo = " ".join([t.titulo or "", t.categoria or "", ",".join(t.tags or [])]).lower()
                if texto not in alvo:
                    continue
            filtrados.append(t)

        self._renderizar_cards(filtrados)

    def _renderizar_cards(self, tickets):
        container = self.ids.get("notas_list")
        if container is None:
            return
        container.clear_widgets()

        if not tickets:
            from kivymd.uix.label import MDLabel

            container.add_widget(
                MDLabel(
                    text="Nenhuma nota encontrada",
                    halign="center",
                    color=COLORS["text_dim"],
                    size_hint_y=None,
                    height=dp(80),
                )
            )
            return

        for t in tickets:
            card = NotaCard(
                ticket_id=t.id,
                categoria=(t.categoria or "Geral").upper(),
                categoria_cor=cor_categoria(t.categoria, CHIP_COLORS),
                tempo=tempo_relativo(t.criado_em),
                titulo_nota=t.titulo or "(sem título)",
                solucao_preview=f"Solução: {preview_texto(t.solucao, 70)}" if t.solucao else "Sem solução registrada ainda",
            )
            card.bind(on_release=lambda inst, tid=t.id: self.abrir_detalhe(tid))
            container.add_widget(card)

    def abrir_detalhe(self, ticket_id: str):
        detalhe = self.manager.get_screen("ticket_detail")
        detalhe.ticket_id = ticket_id
        self.manager.current = "ticket_detail"

    def texto_buscar_mudou(self, texto: str):
        """Filtro local instantâneo enquanto digita (sobre o que já está
        carregado -- não bate na API a cada tecla)."""
        self._aplicar_filtro()

    def buscar(self, texto: str):
        """Enter/lupa: busca de verdade na API do Notion (pega notas que
        não estavam carregadas ainda)."""
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
