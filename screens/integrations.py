"""
Tela de Integrações: mostra as 5 integrações possíveis (Notion, Google
Drive, OneDrive, Supabase, Obsidian), qual delas é o destino ativo de
gravação (o "radio" com check) e o estado de conexão de cada uma.

Notion e Supabase gravam registros estruturados; Google Drive, OneDrive
e Obsidian gravam um .md por nota, organizado em pastas por categoria.
"""
import threading

from kivy.metrics import dp
from kivy.properties import BooleanProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField

from services.integrations_service import INTEGRACOES, REQUER_OAUTH_PENDENTE, get_integracao
from services.md_export_service import caminho_pasta
from services.supabase_service import SupabaseService
from theme import COLORS
from utils.ui import mostrar_aviso


class IntegrationCard(MDCard):
    """Card clicável. Não dá pra usar `ButtonBehavior` junto com `MDCard`
    aqui -- as duas classes têm bases (FocusBehavior/BoxLayout etc.) que
    geram conflito de MRO ("Cannot create a consistent method resolution
    order") em tempo de import, derrubando o app inteiro antes mesmo da
    tela abrir. Em vez disso, implementa o próprio toque (grab/ungrab),
    do jeito que o ButtonBehavior faz por baixo dos panos, disparando
    `on_release` só quando o toque solta dentro do card."""

    integ_id = StringProperty("")
    selecionado = BooleanProperty(False)
    icone = StringProperty("")
    icone_cor_hex = StringProperty("")
    nome = StringProperty("")
    subtitulo = StringProperty("")

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


class IntegrationsScreen(MDScreen):
    _dialog = None

    def on_pre_enter(self, *args):
        self._popular_lista()

    def _popular_lista(self):
        integrations_service = self.manager.integrations_service
        destino_ativo = integrations_service.get_destino_ativo()

        container = self.ids.get("integrations_list")
        if container is None:
            return
        container.clear_widgets()

        for cfg in INTEGRACOES:
            conectado = integrations_service.is_conectado(cfg["id"])
            status = "conectado" if conectado else "não conectado"
            subtitulo = f"{cfg['tipo_desc']} — {status}"

            card = IntegrationCard(
                integ_id=cfg["id"],
                selecionado=(cfg["id"] == destino_ativo),
                icone=cfg["icone"],
                icone_cor_hex=cfg["cor"],
                nome=cfg["nome"],
                subtitulo=subtitulo,
            )
            card.bind(on_release=lambda inst, cid=cfg["id"]: self._tocar_card(cid))
            container.add_widget(card)

        self._atualizar_preview_pastas(destino_ativo)

    def _atualizar_preview_pastas(self, destino_ativo: str):
        label = self.ids.get("pastas_preview")
        if label is None:
            return
        cfg = get_integracao(destino_ativo) or {}
        if cfg.get("modo") == "md_pasta":
            base = "/NoteMax"
            label.text = (
                f"{base}/Rede/*.md\n{base}/Servidor/*.md\n{base}/VPN/*.md"
            )
        else:
            label.text = "Registros estruturados — sem pastas (banco de dados)."

    def _tocar_card(self, integ_id: str):
        integrations_service = self.manager.integrations_service
        if integrations_service.is_conectado(integ_id):
            integrations_service.set_destino_ativo(integ_id)
            self._popular_lista()
            return
        self._abrir_conexao(integ_id)

    def _abrir_conexao(self, integ_id: str):
        if integ_id == "notion":
            self._abrir_dialogo_notion()
        elif integ_id == "obsidian":
            self._abrir_dialogo_obsidian()
        elif integ_id == "supabase":
            self._abrir_dialogo_supabase()
        elif integ_id in REQUER_OAUTH_PENDENTE:
            self._abrir_aviso_oauth(integ_id)

    # -- Notion ---------------------------------------------------------
    def _abrir_dialogo_notion(self):
        campo = MDTextField(hint_text="Token de integration do Notion")
        conteudo = _caixa_dialogo([campo])
        self._dialog = MDDialog(
            title="Conectar Notion",
            type="custom",
            content_cls=conteudo,
            buttons=[_botao("CANCELAR", self._fechar_dialogo), _botao("CONECTAR", lambda *a: self._confirmar_notion(campo.text))],
        )
        self._dialog.open()

    def _confirmar_notion(self, token: str):
        token = (token or "").strip()
        if not token:
            mostrar_aviso("Cole o token do Notion")
            return
        senha = getattr(self.manager, "master_password", None)
        if not senha:
            mostrar_aviso("Sessão sem senha mestra em memória, desbloqueie de novo")
            self._fechar_dialogo()
            return
        self.manager.crypto_service.save_secret("notion_token", token, senha)
        self.manager.notion_service.set_token(token)
        self.manager.integrations_service.set_conectado("notion", True)
        self.manager.integrations_service.set_destino_ativo("notion")
        self._fechar_dialogo()
        mostrar_aviso("Notion conectado")
        self._popular_lista()

    # -- Obsidian (pasta local) ------------------------------------------
    def _abrir_dialogo_obsidian(self):
        campo = MDTextField(hint_text="Caminho da pasta/vault no dispositivo")
        conteudo = _caixa_dialogo([campo])
        self._dialog = MDDialog(
            title="Conectar Obsidian",
            type="custom",
            content_cls=conteudo,
            buttons=[_botao("CANCELAR", self._fechar_dialogo), _botao("CONECTAR", lambda *a: self._confirmar_obsidian(campo.text))],
        )
        self._dialog.open()

    def _confirmar_obsidian(self, pasta: str):
        import os

        pasta = (pasta or "").strip()
        if not pasta:
            mostrar_aviso("Informe o caminho da pasta")
            return
        try:
            os.makedirs(pasta, exist_ok=True)
        except Exception:
            mostrar_aviso("Não consegui criar/acessar essa pasta")
            return

        self.manager.integrations_service.set_config("obsidian", pasta=pasta)
        self.manager.integrations_service.set_conectado("obsidian", True)
        self.manager.integrations_service.set_destino_ativo("obsidian")
        self._fechar_dialogo()
        mostrar_aviso("Obsidian conectado")
        self._popular_lista()

    # -- Supabase ---------------------------------------------------------
    def _abrir_dialogo_supabase(self):
        campo_url = MDTextField(hint_text="URL do projeto (https://xxx.supabase.co)")
        campo_key = MDTextField(hint_text="Chave anon/service", password=True)
        conteudo = _caixa_dialogo([campo_url, campo_key])
        self._dialog = MDDialog(
            title="Conectar Supabase",
            type="custom",
            content_cls=conteudo,
            buttons=[
                _botao("CANCELAR", self._fechar_dialogo),
                _botao("CONECTAR", lambda *a: self._confirmar_supabase(campo_url.text, campo_key.text)),
            ],
        )
        self._dialog.open()

    def _confirmar_supabase(self, url: str, key: str):
        url = (url or "").strip()
        key = (key or "").strip()
        if not url or not key:
            mostrar_aviso("Preencha URL e chave")
            return
        senha = getattr(self.manager, "master_password", None)
        if not senha:
            mostrar_aviso("Sessão sem senha mestra em memória, desbloqueie de novo")
            self._fechar_dialogo()
            return

        mostrar_aviso("Testando conexão com o Supabase...")
        threading.Thread(
            target=self._testar_supabase_thread, args=(url, key, senha), daemon=True
        ).start()
        self._fechar_dialogo()

    def _testar_supabase_thread(self, url, key, senha):
        from kivy.clock import Clock

        servico = SupabaseService(url, key)
        ok = servico.testar_conexao()

        def _finalizar(_dt):
            if not ok:
                mostrar_aviso("Não consegui conectar — confira URL e chave")
                return
            self.manager.integrations_service.set_config("supabase", project_url=url)
            self.manager.crypto_service.save_secret("supabase_key", key, senha)
            self.manager.integrations_service.set_conectado("supabase", True)
            self.manager.integrations_service.set_destino_ativo("supabase")
            mostrar_aviso("Supabase conectado")
            self._popular_lista()

        Clock.schedule_once(_finalizar)

    # -- Google Drive / OneDrive (ainda sem OAuth configurado) -----------
    def _abrir_aviso_oauth(self, integ_id: str):
        cfg = get_integracao(integ_id) or {}
        conteudo = _caixa_dialogo([])
        self._dialog = MDDialog(
            title=f"Conectar {cfg.get('nome', integ_id)}",
            text=(
                "Essa integração precisa de um app OAuth registrado "
                f"({cfg.get('nome', integ_id)} exige credenciais próprias, "
                "ainda não configuradas neste projeto). A tela já está "
                "pronta -- assim que as credenciais existirem, o fluxo de "
                "login entra aqui."
            ),
            buttons=[_botao("ENTENDI", self._fechar_dialogo)],
        )
        self._dialog.open()

    def _fechar_dialogo(self, *args):
        if self._dialog:
            self._dialog.dismiss()
            self._dialog = None

    def conectar_nova(self):
        integrations_service = self.manager.integrations_service
        for cfg in INTEGRACOES:
            if not integrations_service.is_conectado(cfg["id"]):
                self._abrir_conexao(cfg["id"])
                return
        mostrar_aviso("Todas as integrações já estão conectadas")

    def voltar(self):
        self.manager.current = "ticket_list"


def _caixa_dialogo(campos: list) -> BoxLayout:
    caixa = BoxLayout(orientation="vertical", spacing=dp(12), size_hint_y=None)
    caixa.height = dp(56) * max(len(campos), 1)
    for campo in campos:
        caixa.add_widget(campo)
    return caixa


def _botao(texto: str, on_release):
    from kivymd.uix.button import MDFlatButton

    return MDFlatButton(text=texto, on_release=on_release, theme_text_color="Custom", text_color=COLORS["accent"])
