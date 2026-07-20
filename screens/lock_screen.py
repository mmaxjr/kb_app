"""
Tela de senha mestra: desbloqueia (Notion ou somente local), ou
(primeiro acesso) cria a senha mestra.

No primeiro acesso, o token do Notion é OPCIONAL: se o usuário deixar
o campo em branco, o app funciona só com armazenamento no dispositivo
(nenhuma nota tenta sincronizar). Se preencher, integra com o Notion
normalmente. Dá pra voltar aqui depois e reconfigurar.
"""
from kivymd.uix.screen import MDScreen

from utils.ui import mostrar_aviso


class LockScreen(MDScreen):
    crypto_service = None  # injetado no main.py

    def on_pre_enter(self, *args):
        self._mostrar_apenas(self.crypto_service.has_saved_token())

    def _mostrar_apenas(self, mostrar_unlock: bool):
        """Alterna entre unlock_box e setup_box. Os dois já têm
        `size_hint_y: None` e `height: self.minimum_height` fixados no
        .kv (cada campo tem altura própria), então aqui só zero a
        altura do box escondido -- sem isso ele continuaria ocupando
        espaço no layout mesmo invisível (era por isso que os campos
        apareciam bem mais pra baixo, com um vão enorme no meio)."""
        unlock_box = self.ids.unlock_box
        setup_box = self.ids.setup_box

        unlock_box.opacity = 1 if mostrar_unlock else 0
        unlock_box.disabled = not mostrar_unlock
        unlock_box.height = unlock_box.minimum_height if mostrar_unlock else 0

        setup_box.opacity = 0 if mostrar_unlock else 1
        setup_box.disabled = mostrar_unlock
        setup_box.height = setup_box.minimum_height if not mostrar_unlock else 0

    def unlock(self, password: str):
        token = self.crypto_service.load_notion_token(password)
        if token is None:
            mostrar_aviso("Senha incorreta")
            return
        if token:
            self.manager.notion_service.set_token(token)
            # O database_id não é segredo (fica no integrations.json, não
            # criptografado) -- sem reaplicar ele aqui a cada desbloqueio,
            # o NotionService voltaria a ficar sem destino nenhum e toda
            # sincronização falharia de novo.
            config_notion = self.manager.integrations_service.get_config("notion")
            database_id = config_notion.get("database_id", "")
            if database_id:
                self.manager.notion_service.set_database_id(database_id)
        # Guarda a senha mestra em memória pelo resto da sessão -- é o que
        # permite salvar NOVOS segredos depois (ex.: conectar o Supabase
        # na tela de Integrações) sem pedir a senha de novo a cada ação.
        # Nunca é persistida em disco, só fica na RAM enquanto o app roda.
        self.manager.master_password = password
        self.manager.current = "ticket_list"

    def setup(self, token: str, database_id: str, password: str, password_confirm: str):
        token = (token or "").strip()
        database_id = (database_id or "").strip()

        if not password:
            mostrar_aviso("Crie uma senha mestra")
            return
        if password != password_confirm:
            mostrar_aviso("As senhas não coincidem")
            return

        self.crypto_service.save_notion_token(token, password)
        self.manager.master_password = password

        if token:
            self.manager.notion_service.set_token(token)
            self.manager.integrations_service.set_conectado("notion", True)
            self.manager.integrations_service.set_destino_ativo("notion")
            if database_id:
                self.manager.notion_service.set_database_id(database_id)
                self.manager.integrations_service.set_config("notion", database_id=database_id)
                mostrar_aviso("Configurado com o Notion")
            else:
                mostrar_aviso(
                    "Token salvo, mas falta o ID do banco de dados -- "
                    "sem ele a sincronização não funciona. Configure em Integrações."
                )
        else:
            mostrar_aviso("Configurado para uso somente no dispositivo")

        self.manager.current = "ticket_list"
