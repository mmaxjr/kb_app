"""
Criptografia da senha mestra / token do Notion.

O token do Notion nunca fica salvo em texto puro: é criptografado (AES-256
em modo CTR) com uma chave derivada da senha mestra via SHA-256. Se a senha
estiver errada, o texto decifrado sai como lixo e não bate com o marcador
mágico -- é assim que o app detecta senha incorreta sem jamais guardar a
senha em si.

Usa `pyaes` (puro Python, zero dependências nativas) em vez do pacote
`cryptography` (que usa Rust). O `cryptography` já causou dois builds
quebrados no Android por causa da extensão nativa, e há indício de que
mesmo compilando ele pode falhar ao carregar em tempo real em alguns
aparelhos -- um crash nativo que nem aparece como exceção Python. Trocar
por uma lib 100% Python elimina essa classe inteira de problema.
"""
import base64
import hashlib
import os

import pyaes
from kivy.storage.jsonstore import JsonStore

_MAGIC = b"::NOTEMAX-OK::"


class CryptoService:
    def __init__(self, store_path: str = "secure_data.json"):
        self.store = JsonStore(store_path)

    def _derive_key(self, master_password: str) -> bytes:
        # SHA-256 -> 32 bytes -> chave AES-256
        return hashlib.sha256(master_password.encode("utf-8")).digest()

    # -- API genérica: usada por qualquer segredo de integração (token do
    # Notion, chave anon do Supabase, etc.) -- cada um fica guardado sob
    # sua própria chave dentro do secure_data.json, todos cifrados com a
    # mesma senha mestra.
    def has_secret(self, nome: str) -> bool:
        return self.store.exists(nome)

    def save_secret(self, nome: str, valor: str, master_password: str) -> None:
        key = self._derive_key(master_password)
        iv = os.urandom(16)
        counter = pyaes.Counter(initial_value=int.from_bytes(iv, "big"))
        aes = pyaes.AESModeOfOperationCTR(key, counter=counter)
        plaintext = valor.encode("utf-8") + _MAGIC
        ciphertext = aes.encrypt(plaintext)
        payload = base64.urlsafe_b64encode(iv + ciphertext).decode("ascii")
        self.store.put(nome, value=payload)

    def load_secret(self, nome: str, master_password: str) -> str | None:
        if not self.store.exists(nome):
            return None
        try:
            raw = base64.urlsafe_b64decode(self.store.get(nome)["value"])
            iv, ciphertext = raw[:16], raw[16:]
            key = self._derive_key(master_password)
            counter = pyaes.Counter(initial_value=int.from_bytes(iv, "big"))
            aes = pyaes.AESModeOfOperationCTR(key, counter=counter)
            plaintext = aes.decrypt(ciphertext)
            if plaintext.endswith(_MAGIC):
                return plaintext[: -len(_MAGIC)].decode("utf-8")
            return None  # senha errada: decifra, mas vira lixo sem o marcador
        except Exception:
            return None  # senha errada / dado corrompido

    def delete_secret(self, nome: str) -> None:
        if self.store.exists(nome):
            self.store.delete(nome)

    # -- Atalhos específicos do Notion, mantidos por compatibilidade com o
    # resto do app (lock_screen, main.py) -- por baixo usam a API genérica.
    def has_saved_token(self) -> bool:
        return self.has_secret("notion_token")

    def save_notion_token(self, token: str, master_password: str) -> None:
        self.save_secret("notion_token", token, master_password)

    def load_notion_token(self, master_password: str) -> str | None:
        return self.load_secret("notion_token", master_password)
