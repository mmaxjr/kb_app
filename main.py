"""
NOTE MAX - ponto de entrada.
Carrega o App KivyMD, registra as telas no ScreenManager
e injeta os serviços (Notion, crypto, cache) em cada tela.

Este arquivo é escrito com um cuidado extra de robustez: até os
IMPORTS do topo do arquivo (kivymd, telas, serviços) ficam protegidos
por try/except. Se qualquer dependência falhar ao carregar -- inclusive
uma falha "nativa" em algum pacote com extensão em C/Rust -- o app
mostra a mensagem de erro na tela e grava um log, em vez de só fechar
sem explicação nenhuma.
"""
import os
import traceback

from kivy.app import App
from kivy.uix.label import Label


def _write_crash_log(tb: str, app_name: str = "notemax"):
    """Tenta salvar o traceback num arquivo, tentando alguns locais
    possíveis (não dá pra confiar em App.user_data_dir aqui porque a
    falha pode ter acontecido antes do Kivy terminar de inicializar)."""
    candidates = [
        os.path.join(os.path.expanduser("~"), ".config", app_name, "crash_log.txt"),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_log.txt"),
        "/sdcard/notemax_crash_log.txt",
    ]
    for path in candidates:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(tb)
            break
        except Exception:
            continue


_IMPORT_ERROR = None

try:
    from kivy.base import ExceptionHandler, ExceptionManager
    from kivy.core.text import LabelBase
    from kivy.lang import Builder
    from kivy.core.window import Window
    from kivy.uix.label import Label as _KivyLabel
    from kivy.uix.popup import Popup
    from kivy.uix.scrollview import ScrollView as _KivyScrollView
    from kivymd.app import MDApp
    from kivymd.uix.label import MDLabel
    from kivymd.uix.screenmanager import MDScreenManager

    from screens.splash_screen import SplashScreen
    from screens.lock_screen import LockScreen
    from screens.ticket_list import TicketListScreen
    from screens.ticket_detail import TicketDetailScreen
    from screens.ticket_create import TicketCreateScreen
    from screens.integrations import IntegrationsScreen

    from services.crypto_service import CryptoService
    from services.notion_service import NotionService
    from services.cache_service import CacheService
    from services.integrations_service import IntegrationsService

    from theme import COLORS, FONT_DISPLAY, FONT_MONO
except Exception:
    _IMPORT_ERROR = traceback.format_exc()
    _write_crash_log(_IMPORT_ERROR)


def _mostrar_popup_erro(tb: str):
    """Mostra o traceback numa janela que fica aberta até o usuário
    fechar, pra dar pra tirar print. Usa só widgets Kivy puros (Popup,
    Label, ScrollView) -- não depende do KivyMD, então funciona mesmo
    se o erro tiver acontecido dentro de algo do KivyMD."""
    label = _KivyLabel(
        text="Erro inesperado:\n\n" + tb,
        size_hint_y=None,
        halign="left",
        valign="top",
        color=(1, 1, 1, 1),
    )
    label.bind(texture_size=lambda inst, val: setattr(label, "height", val[1]))
    label.bind(width=lambda inst, val: setattr(label, "text_size", (val, None)))

    scroll = _KivyScrollView(do_scroll_x=False)
    scroll.add_widget(label)

    popup = Popup(
        title="Erro no NOTE MAX (tire um print disso e me manda)",
        content=scroll,
        size_hint=(0.95, 0.85),
    )
    popup.open()


if _IMPORT_ERROR is None:

    class _NoteMaxExceptionHandler(ExceptionHandler):
        """Pega qualquer exceção não tratada que aconteça DEPOIS do app
        já estar rodando -- clique de botão, transição de tela, etc.
        Sem isso, um erro num on_release (como o de salvar a senha ou
        criar uma nota) simplesmente derruba o app inteiro sem
        explicação, porque o Kivy não tem tratamento de exceção
        automático pra esses callbacks."""

        def handle_exception(self, inst):
            tb = traceback.format_exc()
            _write_crash_log(tb)
            try:
                _mostrar_popup_erro(tb)
            except Exception:
                pass
            return ExceptionManager.PASS

    ExceptionManager.add_handler(_NoteMaxExceptionHandler())


def _calcular_insets_sistema():
    """Retorna (topo_px, base_px) pra empurrar o conteúdo pra fora da barra
    de status e da barra de navegação do Android.

    A partir do Android 15 (API 35) o app não escolhe mais ficar "por
    baixo" das barras do sistema -- isso passou a ser obrigatório
    (edge-to-edge forçado), então sem esse ajuste manual os topos das
    telas ficam colados/cortados atrás do relógio e os botões do rodapé
    caem em cima da barra de gestos, difíceis de tocar. Foi exatamente
    o que apareceu nos prints do usuário (título "Integrações" atrás do
    relógio, botão "CONECTAR NOVA INTEGRAÇÃO" quase saindo da tela).

    Tenta ler o inset real via WindowInsets (Android); se não conseguir
    (desktop, ou qualquer falha ao chamar a API do Android), cai num
    valor fixo razoável em vez de deixar tudo grudado na borda."""
    from kivy.metrics import dp
    from kivy.utils import platform

    padrao = (dp(24), dp(24))
    if platform != "android":
        return padrao

    try:
        from jnius import autoclass

        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        activity = PythonActivity.mActivity
        decor_view = activity.getWindow().getDecorView()
        insets = decor_view.getRootWindowInsets()
        if insets is None:
            return padrao
        topo = insets.getSystemWindowInsetTop()
        base = insets.getSystemWindowInsetBottom()
        if topo <= 0 and base <= 0:
            return padrao
        return (float(topo), float(base))
    except Exception:
        return padrao


def _register_brand_fonts():
    """Registra Space Grotesk / JetBrains Mono se os .ttf existirem no
    build. Retorna os nomes de fonte a usar (o nome custom se registrou
    com sucesso, senão "Roboto" — a fonte padrão do Kivy, que está
    sempre disponível). Isso evita usar um font_name não resolvido, que
    quebraria a renderização do texto."""
    base = os.path.join(os.path.dirname(__file__), "assets", "fonts")
    display_path = os.path.join(base, "SpaceGrotesk.ttf")
    mono_path = os.path.join(base, "JetBrainsMono.ttf")

    font_display = "Roboto"
    font_mono = "Roboto"

    try:
        if os.path.exists(display_path):
            LabelBase.register(name=FONT_DISPLAY, fn_regular=display_path)
            font_display = FONT_DISPLAY
    except Exception:
        pass

    try:
        if os.path.exists(mono_path):
            LabelBase.register(name=FONT_MONO, fn_regular=mono_path)
            font_mono = FONT_MONO
    except Exception:
        pass

    return font_display, font_mono


if _IMPORT_ERROR is not None:
    # Fallback mínimo: um app Kivy "puro" (sem KivyMD) só pra mostrar o
    # erro. Usa só kivy.app/kivy.uix.label, que são o núcleo mais básico
    # do framework -- se isso também falhar, não tem mais o que fazer
    # por software.
    class NoteMaxApp(App):
        def build(self):
            return Label(
                text="Falha ao carregar o NOTE MAX:\n\n" + _IMPORT_ERROR,
                halign="left",
                valign="top",
                text_size=(360, None),
            )

else:

    class NoteMaxApp(MDApp):
        def build(self):
            # Qualquer exceção aqui, antes tirava o app do ar sem
            # explicação nenhuma (só fechava). Agora mostra o erro em
            # tela e grava um arquivo de log.
            try:
                return self._build_real()
            except Exception:
                tb = traceback.format_exc()
                self._salvar_log_erro(tb)
                return MDLabel(
                    text=(
                        "Erro ao iniciar o NOTE MAX:\n\n"
                        + tb
                        + "\n\nEsse texto também foi salvo em crash_log.txt"
                    ),
                    halign="left",
                    valign="top",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1),
                )

        def _salvar_log_erro(self, tb: str):
            try:
                path = os.path.join(self.user_data_dir, "crash_log.txt")
                with open(path, "w", encoding="utf-8") as f:
                    f.write(tb)
            except Exception:
                pass  # se nem isso funcionar, não tem mais o que fazer

        def _build_real(self):
            self.title = "NOTE MAX"
            self.colors = COLORS
            self.font_display, self.font_mono = _register_brand_fonts()

            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_palette = "Teal"
            Window.clearcolor = COLORS["bg"]

            # Espaço reservado pra barra de status / barra de navegação do
            # Android (ver _calcular_insets_sistema) -- os .kv usam
            # app.inset_top / app.inset_bottom pra empurrar o conteúdo pra
            # fora dessas áreas.
            self.inset_top, self.inset_bottom = _calcular_insets_sistema()

            # Serviços compartilhados entre todas as telas. Os arquivos de
            # dados (senha mestra criptografada e cache SQLite) usam
            # user_data_dir — a pasta privada do app garantida gravável
            # pelo Kivy em qualquer plataforma. Um caminho relativo tipo
            # "cache.db" pode cair num diretório sem suporte a lock de
            # arquivo no Android, causando "disk I/O error".
            os.makedirs(self.user_data_dir, exist_ok=True)
            self.crypto_service = CryptoService(
                store_path=os.path.join(self.user_data_dir, "secure_data.json")
            )
            self.notion_service = NotionService()
            self.cache_service = CacheService(
                db_path=os.path.join(self.user_data_dir, "cache.db")
            )
            self.integrations_service = IntegrationsService(
                store_path=os.path.join(self.user_data_dir, "integrations.json")
            )

            # Carrega os arquivos .kv (theme.kv primeiro: define as regras
            # globais de cor/fonte usadas pelos demais)
            Builder.load_file("kv/theme.kv")
            Builder.load_file("kv/splash_screen.kv")
            Builder.load_file("kv/lock_screen.kv")
            Builder.load_file("kv/ticket_list.kv")
            Builder.load_file("kv/ticket_detail.kv")
            Builder.load_file("kv/ticket_create.kv")
            Builder.load_file("kv/integrations.kv")

            sm = MDScreenManager()
            sm.notion_service = self.notion_service
            sm.crypto_service = self.crypto_service
            sm.cache_service = self.cache_service
            sm.integrations_service = self.integrations_service
            sm.master_password = None

            lock = LockScreen(name="lock_screen")
            lock.crypto_service = self.crypto_service

            sm.add_widget(SplashScreen(name="splash_screen"))
            sm.add_widget(lock)
            sm.add_widget(TicketListScreen(name="ticket_list"))
            sm.add_widget(TicketDetailScreen(name="ticket_detail"))
            sm.add_widget(TicketCreateScreen(name="ticket_create"))
            sm.add_widget(IntegrationsScreen(name="integrations"))

            # Se o Notion já tinha um token salvo antes desta versão (que
            # introduziu o IntegrationsService), marca ele como conectado
            # pra tela de Integrações refletir o estado real assim que o
            # usuário desbloquear.
            if self.crypto_service.has_saved_token():
                self.integrations_service.set_conectado("notion", True)

            # A splash animada (dentro do app) aparece primeiro e some
            # sozinha depois de ~1.6s, indo pra tela de senha.
            sm.current = "splash_screen"
            return sm


if __name__ == "__main__":
    NoteMaxApp().run()
