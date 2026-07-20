"""
Toda a comunicação com a Notion API.
"""
from notion_client import Client


class NotionService:
    def __init__(self, database_id: str = ""):
        self.client: Client | None = None
        self.database_id = database_id

    def set_token(self, token: str) -> None:
        self.client = Client(auth=token)

    def set_database_id(self, database_id: str) -> None:
        self.database_id = (database_id or "").strip()

    def is_ready(self) -> bool:
        """True só quando tem token E um database_id de verdade -- sem
        essas duas coisas, toda chamada à API do Notion falha (404 no
        database). O valor padrão antigo era o texto literal
        "SEU_DATABASE_ID", que nunca é um ID válido -- ninguém tinha como
        configurar o database_id de verdade em lugar nenhum do app, então
        a sincronização com o Notion falhava sempre, silenciosamente."""
        return self.client is not None and bool(self.database_id)

    def _exigir_pronto(self):
        if self.client is None:
            raise RuntimeError("Notion sem token configurado")
        if not self.database_id:
            raise RuntimeError(
                "Notion sem database_id configurado -- vá em Integrações e "
                "informe o ID do banco de dados do Notion"
            )

    def create_ticket(self, titulo, descricao, solucao, categoria, tags):
        self._exigir_pronto()
        return self.client.pages.create(
            parent={"database_id": self.database_id},
            properties={
                "Título": {"title": [{"text": {"content": titulo}}]},
                "Descrição": {"rich_text": [{"text": {"content": descricao}}]},
                "Solução": {"rich_text": [{"text": {"content": solucao}}]},
                "Categoria": {"select": {"name": categoria}},
                "Tags": {"multi_select": [{"name": t} for t in tags]},
            },
        )

    def list_tickets(self, filtro: dict | None = None):
        self._exigir_pronto()
        query = {"database_id": self.database_id}
        if filtro:
            query["filter"] = filtro
        return self.client.databases.query(**query)

    def search_tickets(self, texto: str):
        self._exigir_pronto()
        return self.client.databases.query(
            database_id=self.database_id,
            filter={
                "or": [
                    {"property": "Título", "title": {"contains": texto}},
                    {"property": "Descrição", "rich_text": {"contains": texto}},
                ]
            },
        )

    def update_ticket(self, page_id: str, **props):
        self._exigir_pronto()
        properties = {}
        if "titulo" in props:
            properties["Título"] = {"title": [{"text": {"content": props["titulo"]}}]}
        if "descricao" in props:
            properties["Descrição"] = {"rich_text": [{"text": {"content": props["descricao"]}}]}
        if "solucao" in props:
            properties["Solução"] = {"rich_text": [{"text": {"content": props["solucao"]}}]}
        if "categoria" in props:
            properties["Categoria"] = {"select": {"name": props["categoria"]}}
        if "tags" in props:
            properties["Tags"] = {"multi_select": [{"name": t} for t in props["tags"]]}
        return self.client.pages.update(page_id=page_id, properties=properties)
