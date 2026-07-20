"""
KB App - ponto de entrada.
Carrega o App KivyMD, registra as telas no ScreenManager
e injeta os serviços (Notion, crypto, cache) em cada tela.
"""
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


class KBApp(MDApp):
    def build(self):
        self.title = "KB App"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"

        # Serviços compartilhados entre todas as telas
        self.crypto_service = CryptoService()
        self.notion_service = NotionService()
        self.cache_service = CacheService()

        # Carrega os arquivos .kv
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
    KBApp().run()
