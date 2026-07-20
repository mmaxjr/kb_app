"""
Gerador de PDF minimalista, sem dependências externas (nem reportlab,
nem fpdf2). Escreve a estrutura do PDF manualmente — suficiente para
exportar uma nota como texto simples, com quebra de página automática.

Motivo de não usar uma lib pronta: pacotes com extensão nativa
(como o "cryptography" deste projeto) já causaram builds quebrados
no Android. Isso aqui é puro Python stdlib, sem risco de build.
"""
from textwrap import wrap

PAGE_WIDTH = 595   # A4 em pontos (72dpi)
PAGE_HEIGHT = 842
MARGIN = 50
FONT_SIZE = 11
LINE_HEIGHT = 15
CHARS_PER_LINE = 88  # aproximação pra Helvetica 11pt numa página A4


def _escape(text: str) -> str:
    return (
        text.replace("\\", r"\\")
        .replace("(", r"\(")
        .replace(")", r"\)")
    )


def _wrap_lines(text: str, width: int = CHARS_PER_LINE):
    lines = []
    for raw_line in text.splitlines() or [""]:
        if not raw_line.strip():
            lines.append("")
            continue
        lines.extend(wrap(raw_line, width=width) or [""])
    return lines


def _paginate(lines, lines_per_page):
    lines_per_page = max(1, lines_per_page)
    pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
    return pages or [[]]


def build_pdf(title: str, sections: list) -> bytes:
    """sections: lista de tuplas (rótulo, texto). Retorna os bytes do PDF."""
    lines_per_page = (PAGE_HEIGHT - 2 * MARGIN) // LINE_HEIGHT

    all_lines = [title or "(sem título)", ""]
    for label, text in sections:
        if not text:
            continue
        all_lines.append(f"{label}:")
        all_lines.extend(_wrap_lines(str(text)))
        all_lines.append("")

    pages_lines = _paginate(all_lines, int(lines_per_page))

    catalog_id = 1
    pages_id = 2
    font_id = 3

    def page_id(i):
        return 4 + i * 2

    def content_id(i):
        return 5 + i * 2

    num_pages = len(pages_lines)
    objects = {}

    kids = " ".join(f"{page_id(i)} 0 R" for i in range(num_pages))
    objects[catalog_id] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>"
    objects[pages_id] = f"<< /Type /Pages /Kids [{kids}] /Count {num_pages} >>"
    objects[font_id] = (
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
        "/Encoding /WinAnsiEncoding >>"
    )

    for i, lines in enumerate(pages_lines):
        stream_parts = [
            f"BT /F1 {FONT_SIZE} Tf {MARGIN} {PAGE_HEIGHT - MARGIN} Td {LINE_HEIGHT} TL"
        ]
        first = True
        for line in lines:
            escaped = _escape(line)
            if first:
                stream_parts.append(f"({escaped}) Tj")
                first = False
            else:
                stream_parts.append(f"T* ({escaped}) Tj")
        stream_parts.append("ET")
        stream_bytes = "\n".join(stream_parts).encode("latin-1", errors="replace")

        objects[page_id(i)] = (
            f"<< /Type /Page /Parent {pages_id} 0 R "
            f"/Resources << /Font << /F1 {font_id} 0 R >> >> "
            f"/MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Contents {content_id(i)} 0 R >>"
        )
        objects[content_id(i)] = ("STREAM", stream_bytes)

    buf = bytearray()
    buf += b"%PDF-1.4\n"
    offsets = {}
    max_id = max(objects.keys())

    for obj_id in range(1, max_id + 1):
        offsets[obj_id] = len(buf)
        body = objects[obj_id]
        if isinstance(body, tuple) and body[0] == "STREAM":
            stream_bytes = body[1]
            buf += f"{obj_id} 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n".encode("latin-1")
            buf += stream_bytes
            buf += b"\nendstream\nendobj\n"
        else:
            buf += f"{obj_id} 0 obj\n{body}\nendobj\n".encode("latin-1")

    xref_offset = len(buf)
    buf += f"xref\n0 {max_id + 1}\n".encode("latin-1")
    buf += b"0000000000 65535 f \n"
    for obj_id in range(1, max_id + 1):
        buf += f"{offsets[obj_id]:010d} 00000 n \n".encode("latin-1")

    buf += (
        f"trailer\n<< /Size {max_id + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode("latin-1")

    return bytes(buf)
