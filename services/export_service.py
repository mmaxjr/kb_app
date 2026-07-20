"""
Exportação de notas para .txt e .pdf.

Os arquivos são salvos em `App.user_data_dir/exports` — pasta privada
do próprio app, garantida gravável tanto no Android (sem precisar de
permissão de armazenamento, compatível com scoped storage) quanto no
desktop, sem depender de bibliotecas nativas.
"""
import os
import re
import time

from services.pdf_writer import build_pdf


def _safe_filename(text: str) -> str:
    text = (text or "").strip() or "nota"
    text = re.sub(r"[^\w\-. ]", "", text, flags=re.UNICODE)
    text = re.sub(r"\s+", "_", text)
    return text[:60] or "nota"


def _timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")


def export_txt(ticket, dest_dir: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    titulo = ticket.titulo or "(sem título)"
    filename = f"{_safe_filename(ticket.titulo)}_{_timestamp()}.txt"
    path = os.path.join(dest_dir, filename)

    lines = [
        titulo,
        "=" * len(titulo),
        "",
        f"Categoria: {ticket.categoria or '-'}",
        f"Tags: {', '.join(ticket.tags) if ticket.tags else '-'}",
        "",
        "Descrição:",
        ticket.descricao or "-",
        "",
        "Solução:",
        ticket.solucao or "-",
        "",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return path


def export_pdf(ticket, dest_dir: str) -> str:
    os.makedirs(dest_dir, exist_ok=True)
    filename = f"{_safe_filename(ticket.titulo)}_{_timestamp()}.pdf"
    path = os.path.join(dest_dir, filename)

    sections = [
        ("Categoria", ticket.categoria or "-"),
        ("Tags", ", ".join(ticket.tags) if ticket.tags else "-"),
        ("Descrição", ticket.descricao or "-"),
        ("Solução", ticket.solucao or "-"),
    ]
    pdf_bytes = build_pdf(ticket.titulo or "(sem título)", sections)
    with open(path, "wb") as f:
        f.write(pdf_bytes)
    return path
