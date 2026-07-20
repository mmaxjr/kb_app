"""
Configuração e estado das integrações de gravação (onde as notas são
salvas): Notion, Google Drive, OneDrive, Supabase e Obsidian.

Duas famílias:
- "estruturado": grava como registro/linha num banco (Notion = página
  de database; Supabase = linha de tabela Postgres via REST/PostgREST).
- "md_pasta": grava um arquivo .md por nota, organizado em pastas por
  categoria (Google Drive, OneDrive, Obsidian).

Este módulo guarda só METADADOS (conectado ou não, qual é o destino
ativo, caminhos/URLs não sensíveis). Segredos de verdade (token,
API key) continuam passando pelo CryptoService, criptografados com a
senha mestra -- nunca ficam em texto puro aqui.
"""
from kivy.storage.jsonstore import JsonStore

INTEGRACOES = [
    {
        "id": "notion",
        "nome": "Notion",
        "icone": "database",
        "cor": "accent",
        "tipo_desc": "Database estruturado",
        "modo": "estruturado",
    },
    {
        "id": "google_drive",
        "nome": "Google Drive",
        "icone": "google-drive",
        "cor": "alert",
        "tipo_desc": ".md por pasta",
        "modo": "md_pasta",
    },
    {
        "id": "onedrive",
        "nome": "OneDrive",
        "icone": "microsoft-onedrive",
        "cor": "accent_light",
        "tipo_desc": ".md por pasta",
        "modo": "md_pasta",
    },
    {
        "id": "supabase",
        "nome": "Supabase",
        "icone": "lightning-bolt",
        "cor": "accent",
        "tipo_desc": "Tabela Postgres",
        "modo": "estruturado",
    },
    {
        "id": "obsidian",
        "nome": "Obsidian",
        "icone": "star-four-points-outline",
        "cor": "roxo",
        "tipo_desc": "Vault local (.md)",
        "modo": "md_pasta",
    },
]

# OAuth de verdade (Google Drive / OneDrive) exige um app registrado no
# Google Cloud Console / Azure AD (client id/secret) que ainda não foi
# configurado -- por isso essas duas ficam com a tela pronta, mas o
# "Conectar" delas mostra um aviso em vez de abrir o fluxo de login.
REQUER_OAUTH_PENDENTE = {"google_drive", "onedrive"}


def get_integracao(integ_id: str) -> dict | None:
    for item in INTEGRACOES:
        if item["id"] == integ_id:
            return item
    return None


class IntegrationsService:
    def __init__(self, store_path: str = "integrations.json"):
        self.store = JsonStore(store_path)

    def get_destino_ativo(self) -> str:
        if self.store.exists("destino_ativo"):
            return self.store.get("destino_ativo")["value"]
        return "notion"

    def set_destino_ativo(self, integ_id: str) -> None:
        self.store.put("destino_ativo", value=integ_id)

    def is_conectado(self, integ_id: str) -> bool:
        chave = f"conectado_{integ_id}"
        if self.store.exists(chave):
            return bool(self.store.get(chave)["value"])
        return False

    def set_conectado(self, integ_id: str, conectado: bool) -> None:
        self.store.put(f"conectado_{integ_id}", value=conectado)

    def get_config(self, integ_id: str) -> dict:
        chave = f"config_{integ_id}"
        if self.store.exists(chave):
            return self.store.get(chave)["value"]
        return {}

    def set_config(self, integ_id: str, **kwargs) -> None:
        """Dados não sensíveis (ex.: pasta local do Obsidian, URL do
        projeto Supabase). Segredos como API key vão pelo CryptoService."""
        self.store.put(f"config_{integ_id}", value=kwargs)
