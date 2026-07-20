"""
Modelo de dados de um ticket da base de conhecimento.
"""
from dataclasses import dataclass, field


@dataclass
class Ticket:
    id: str = ""
    titulo: str = ""
    descricao: str = ""
    solucao: str = ""
    categoria: str = ""
    tags: list[str] = field(default_factory=list)
    sincronizado: bool = False
    local_only: bool = False  # True = salva só no dispositivo, nunca sobe pro Notion
    criado_em: str = ""  # ISO 8601 -- usado pro "há 2h / ontem / 3 dias" na lista

    @classmethod
    def from_notion_page(cls, page: dict) -> "Ticket":
        """Converte a resposta bruta da Notion API em um Ticket."""
        props = page.get("properties", {})

        def _title(prop_name):
            arr = props.get(prop_name, {}).get("title", [])
            return arr[0]["text"]["content"] if arr else ""

        def _rich_text(prop_name):
            arr = props.get(prop_name, {}).get("rich_text", [])
            return arr[0]["text"]["content"] if arr else ""

        def _select(prop_name):
            sel = props.get(prop_name, {}).get("select")
            return sel["name"] if sel else ""

        def _multi_select(prop_name):
            arr = props.get(prop_name, {}).get("multi_select", [])
            return [t["name"] for t in arr]

        return cls(
            id=page.get("id", ""),
            titulo=_title("Título"),
            descricao=_rich_text("Descrição"),
            solucao=_rich_text("Solução"),
            categoria=_select("Categoria"),
            tags=_multi_select("Tags"),
            sincronizado=True,
            criado_em=page.get("created_time", ""),
        )

    @classmethod
    def from_row(cls, row) -> "Ticket":
        """Converte uma linha do SQLite (cache local) em um Ticket."""
        return cls(
            id=row[0],
            titulo=row[1],
            descricao=row[2],
            solucao=row[3],
            categoria=row[4],
            tags=row[5].split(",") if row[5] else [],
            sincronizado=bool(row[6]),
            local_only=bool(row[7]) if len(row) > 7 else False,
            criado_em=row[8] if len(row) > 8 and row[8] else "",
        )
