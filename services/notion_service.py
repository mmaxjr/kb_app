"""
Toda a comunicação com a Notion API.
"""
from notion_client import Client


class NotionService:
    def __init__(self, database_id: str = "SEU_DATABASE_ID"):
        self.client: Client | None = None
        self.database_id = database_id

    def set_token(self, token: str) -> None:
        self.client = Client(auth=token)

    def is_ready(self) -> bool:
        return self.client is not None

    def create_ticket(self, titulo, descricao, solucao, categoria, tags):
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
        query = {"database_id": self.database_id}
        if filtro:
            query["filter"] = filtro
        return self.client.databases.query(**query)

    def search_tickets(self, texto: str):
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
