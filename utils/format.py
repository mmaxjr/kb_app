"""
Helpers de formatação usados na tela de notas: tempo relativo
("há 2h", "ontem", "3 dias"), cor determinística por categoria e
preview curto de um texto longo.
"""
from datetime import datetime, timezone


def _parse_iso(value: str):
    if not value:
        return None
    v = value.strip()
    if v.endswith("Z"):
        v = v[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def tempo_relativo(iso_str: str) -> str:
    """Converte um timestamp ISO (nosso ou o `created_time` do Notion)
    num texto curto tipo "há 2h", "ontem", "3 dias". String vazia ou
    inválida retorna "" (o card simplesmente não mostra o horário)."""
    dt = _parse_iso(iso_str)
    if dt is None:
        return ""

    agora = datetime.now(timezone.utc)
    segundos = max(0.0, (agora - dt).total_seconds())
    minutos = segundos / 60
    horas = minutos / 60
    dias = horas / 24

    if minutos < 1:
        return "agora"
    if minutos < 60:
        return f"há {int(minutos)}min"
    if horas < 24:
        return f"há {int(horas)}h"
    if dias < 2:
        return "ontem"
    if dias < 7:
        return f"há {int(dias)} dias"
    if dias < 30:
        return f"há {int(dias / 7)} sem"
    if dias < 365:
        return f"há {int(dias / 30)} m"
    return f"há {int(dias / 365)} a"


def cor_categoria(categoria: str, chip_colors: list):
    """Escolhe uma cor da paleta de forma determinística: a mesma
    categoria sempre cai na mesma cor."""
    if not categoria or not chip_colors:
        return chip_colors[0] if chip_colors else (1, 1, 1, 1)
    indice = sum(ord(c) for c in categoria) % len(chip_colors)
    return chip_colors[indice]


def preview_texto(texto: str, max_len: int = 70) -> str:
    """Colapsa quebras de linha/espaços e corta com "..." se passar de
    max_len caracteres."""
    if not texto:
        return ""
    limpo = " ".join(texto.split())
    if len(limpo) > max_len:
        return limpo[:max_len].rstrip() + "..."
    return limpo
