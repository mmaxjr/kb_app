"""
NOTE MAX - ponto de entrada.
Carrega o App KivyMD, registra as telas no ScreenManager
e injeta os serviços (Notion, crypto, cache) em cada tela.
"""
import os

from kivy.core.text import LabelBase
from kivy.lang import Builder
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.uix.screenmanager import MDScreenManager

from screens.lock_screen import LockScreen
from screens.ticket_list import TicketListScreen
from screens.ticket_detail import TicketDetailScreen
from screens.ticket_create import TicketCreateScreen

from services.crypto_service import CryptoService
from services.notion_service import NotionService
from services.cache_service import CacheService

from theme import COLORS, FONT_DISPLAY, FONT_MONO


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


class NoteMaxApp(MDApp):
    def build(self):
        self.title = "NOTE MAX"
        self.colors = COLORS
        self.font_display, self.font_mono = _register_brand_fonts()

        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Teal"
        Window.clearcolor = COLORS["bg"]

        # Serviços compartilhados entre todas as telas
        self.crypto_service = CryptoService()
        self.notion_service = NotionService()
        self.cache_service = CacheService()

        # Carrega os arquivos .kv (theme.kv primeiro: define as regras
        # globais de cor/fonte usadas pelos demais)
        Builder.load_file("kv/theme.kv")
        Builder.load_file("kv/lock_screen.kv")
        Builder.load_file("kv/ticket_list.kv")
        Builder.load_file("kv/ticket_detail.kv")
        Builder.load_file("kv/ticket_create.kv")

        sm = MDScreenManager()
        sm.notion_service = self.notion_service
        sm.crypto_service = self.crypto_service
        sm.cache_service = self.cache_service

        lock = LockScreen(name="lock_screen")
        lock.crypto_service = self.crypto_service

        sm.add_widget(lock)
        sm.add_widget(TicketListScreen(name="ticket_list"))
        sm.add_widget(TicketDetailScreen(name="ticket_detail"))
        sm.add_widget(TicketCreateScreen(name="ticket_create"))

        sm.current = "lock_screen"
        return sm


if __name__ == "__main__":
    NoteMaxApp().run()
