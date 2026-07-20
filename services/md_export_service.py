"""
Grava uma nota como arquivo .md organizado em pastas por categoria --
usado pelas integrações do tipo "md_pasta" (Obsidian de verdade; Google
Drive/OneDrive usarão a mesma função assim que o OAuth de cada um
estiver configurado, já que o formato final é o mesmo .md por pasta).
"""
import os
import re


def _slug(texto: str) -> str:
    texto = (texto or "").strip() or "sem_categoria"
    texto = re.sub(r"[^\w\-áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ ]", "", texto, flags=re.UNICODE)
    return texto.replace(" ", "_") or "sem_categoria"


def _slug_arquivo(texto: str) -> str:
    texto = (texto or "nota").strip() or "nota"
    texto = re.sub(r"[^\w\- ]", "", texto, flags=re.UNICODE)
    return texto.replace(" ", "_")[:60] or "nota"


def caminho_pasta(base_dir: str, categoria: str) -> str:
    return os.path.join(base_dir, _slug(categoria))


def gravar_md(ticket, base_dir: str) -> str:
    """Grava `base_dir/<categoria>/<titulo>.md` e retorna o caminho final."""
    pasta = caminho_pasta(base_dir, ticket.categoria)
    os.makedirs(pasta, exist_ok=True)

    nome_arquivo = f"{_slug_arquivo(ticket.titulo)}.md"
    caminho = os.path.join(pasta, nome_arquivo)

    tags = " ".join(f"#{t.strip().replace(' ', '_')}" for t in (ticket.tags or []) if t.strip())
    linhas = [
        f"# {ticket.titulo or '(sem título)'}",
        "",
        f"**Categoria:** {ticket.categoria or '-'}",
    ]
    if tags:
        linhas.append(f"**Tags:** {tags}")
    linhas += [
        "",
        "## Descrição",
        ticket.descricao or "-",
        "",
        "## Solução",
        ticket.solucao or "-",
        "",
    ]
    with open(caminho, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas))
    return caminho
