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

    def has_saved_token(self) -> bool:
        return self.store.exists("notion_token")

    def save_notion_token(self, token: str, master_password: str) -> None:
        key = self._derive_key(master_password)
        iv = os.urandom(16)
        counter = pyaes.Counter(initial_value=int.from_bytes(iv, "big"))
        aes = pyaes.AESModeOfOperationCTR(key, counter=counter)
        plaintext = token.encode("utf-8") + _MAGIC
        ciphertext = aes.encrypt(plaintext)
        payload = base64.urlsafe_b64encode(iv + ciphertext).decode("ascii")
        self.store.put("notion_token", value=payload)

    def load_notion_token(self, master_password: str) -> str | None:
        if not self.store.exists("notion_token"):
            return None
        try:
            raw = base64.urlsafe_b64decode(self.store.get("notion_token")["value"])
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
