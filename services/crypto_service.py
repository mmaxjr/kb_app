"""
Criptografia da senha mestra / token do Notion.

O token do Notion nunca fica salvo em texto puro: é criptografado com uma
chave derivada da senha mestra (SHA-256 -> base64 -> Fernet). Se a senha
estiver errada, o decrypt() falha silenciosamente (retorna None) -- é assim
que o app detecta senha incorreta sem jamais guardar a senha em si.
"""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from kivy.storage.jsonstore import JsonStore


class CryptoService:
    def __init__(self, store_path: str = "secure_data.json"):
        self.store = JsonStore(store_path)

    def _derive_key(self, master_password: str) -> bytes:
        digest = hashlib.sha256(master_password.encode()).digest()
        return base64.urlsafe_b64encode(digest)

    def has_saved_token(self) -> bool:
        return self.store.exists("notion_token")

    def save_notion_token(self, token: str, master_password: str) -> None:
        key = self._derive_key(master_password)
        f = Fernet(key)
        encrypted = f.encrypt(token.encode()).decode()
        self.store.put("notion_token", value=encrypted)

    def load_notion_token(self, master_password: str) -> str | None:
        if not self.store.exists("notion_token"):
            return None
        key = self._derive_key(master_password)
        f = Fernet(key)
        encrypted = self.store.get("notion_token")["value"]
        try:
            return f.decrypt(encrypted.encode()).decode()
        except (InvalidToken, Exception):
            return None  # senha errada
