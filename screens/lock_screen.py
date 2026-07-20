"""
Tela de senha mestra: desbloqueia (Notion ou somente local), ou
(primeiro acesso) cria a senha mestra.

No primeiro acesso, o token do Notion é OPCIONAL: se o usuário deixar
o campo em branco, o app funciona só com armazenamento no dispositivo
(nenhuma nota tenta sincronizar). Se preencher, integra com o Notion
normalmente. Dá pra voltar aqui depois e reconfigurar.
"""
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar


class LockScreen(MDScreen):
    crypto_service = None  # injetado no main.py

    def on_pre_enter(self, *args):
        self._mostrar_apenas(self.crypto_service.has_saved_token())

    def _mostrar_apenas(self, mostrar_unlock: bool):
        """Alterna entre unlock_box e setup_box. Fundamental: o box
        escondido precisa ficar com altura 0 também, senão ele continua
        ocupando espaço no layout vertical mesmo invisível (era por
        isso que os campos apareciam "flutuando" muito mais pra baixo,
        com um vão enorme em branco no meio da tela)."""
        unlock_box = self.ids.unlock_box
        setup_box = self.ids.setup_box

        unlock_box.opacity = 1 if mostrar_unlock else 0
        unlock_box.disabled = not mostrar_unlock
        unlock_box.size_hint_y = None if not mostrar_unlock else 1
        if not mostrar_unlock:
            unlock_box.height = 0

        setup_box.opacity = 0 if mostrar_unlock else 1
        setup_box.disabled = mostrar_unlock
        setup_box.size_hint_y = None if mostrar_unlock else 1
        if mostrar_unlock:
            setup_box.height = 0

    def unlock(self, password: str):
        token = self.crypto_service.load_notion_token(password)
        if token is None:
            Snackbar(text="Senha incorreta").open()
            return
        if token:
            self.manager.notion_service.set_token(token)
        self.manager.current = "ticket_list"

    def setup(self, token: str, password: str, password_confirm: str):
        token = (token or "").strip()

        if not password:
            Snackbar(text="Crie uma senha mestra").open()
            return
        if password != password_confirm:
            Snackbar(text="As senhas não coincidem").open()
            return

        self.crypto_service.save_notion_token(token, password)

        if token:
            self.manager.notion_service.set_token(token)
            Snackbar(text="Configurado com o Notion").open()
        else:
            Snackbar(text="Configurado para uso somente no dispositivo").open()

        self.manager.current = "ticket_list"
