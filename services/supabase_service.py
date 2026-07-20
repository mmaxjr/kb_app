"""
Cliente mínimo para o Supabase, usando a REST API do PostgREST direto
via httpx (já é dependência do notion-client, então não adiciona peso
nenhum ao build). Não precisa de SDK nem de OAuth -- só URL do projeto
+ chave anon/service, exatamente como Notion precisa só de um token.
"""
import httpx

_TABELA = "notemax_tickets"


class SupabaseService:
    def __init__(self, project_url: str = "", api_key: str = ""):
        self.project_url = (project_url or "").rstrip("/")
        self.api_key = api_key or ""

    def is_ready(self) -> bool:
        return bool(self.project_url and self.api_key)

    def _headers(self):
        return {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def testar_conexao(self) -> bool:
        """Faz um GET simples só pra confirmar que URL + chave são válidos."""
        try:
            resp = httpx.get(
                f"{self.project_url}/rest/v1/{_TABELA}?limit=1",
                headers=self._headers(),
                timeout=10,
            )
            return resp.status_code < 500 and resp.status_code != 401
        except Exception:
            return False

    def criar_ticket(self, ticket) -> dict:
        payload = {
            "id": ticket.id,
            "titulo": ticket.titulo,
            "descricao": ticket.descricao,
            "solucao": ticket.solucao,
            "categoria": ticket.categoria,
            "tags": ",".join(ticket.tags or []),
        }
        resp = httpx.post(
            f"{self.project_url}/rest/v1/{_TABELA}",
            headers=self._headers(),
            json=payload,
            timeout=15,
        )
        resp.raise_for_status()
        dados = resp.json()
        return dados[0] if isinstance(dados, list) and dados else dados

    def listar_tickets(self) -> list:
        resp = httpx.get(
            f"{self.project_url}/rest/v1/{_TABELA}?select=*",
            headers=self._headers(),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()
