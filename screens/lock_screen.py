"""
Tela de senha mestra: desbloqueia o token do Notion salvo,
ou (primeiro acesso) permite colar o token + criar a senha mestra.
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar


class LockScreen(MDScreen):
    crypto_service = None  # injetado no main.py

    def on_pre_enter(self, *args):
        self.ids.setup_box.opacity = 0
        self.ids.setup_box.disabled = True
        self.ids.unlock_box.opacity = 1
        self.ids.unlock_box.disabled = False

        if not self.crypto_service.has_saved_token():
            # Primeiro acesso: pede token do Notion + senha mestra nova
            self.ids.unlock_box.opacity = 0
            self.ids.unlock_box.disabled = True
            self.ids.setup_box.opacity = 1
            self.ids.setup_box.disabled = False

    def unlock(self, password: str):
        token = self.crypto_service.load_notion_token(password)
        if token:
            self.manager.notion_service.set_token(token)
            self.manager.current = "ticket_list"
        else:
            Snackbar(text="Senha incorreta").open()

    def setup(self, token: str, password: str, password_confirm: str):
        if not token or not password:
            Snackbar(text="Preencha o token e a senha").open()
            return
        if password != password_confirm:
            Snackbar(text="As senhas não coincidem").open()
            return

        self.crypto_service.save_notion_token(token, password)
        self.manager.notion_service.set_token(token)
        Snackbar(text="Configurado com sucesso").open()
        self.manager.current = "ticket_list"
