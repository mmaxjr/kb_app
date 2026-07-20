"""
Identidade visual do NOTE MAX.

Paleta e tipografia extraídas do guia de marca (fundo escuro,
tom técnico/terminal). Centralizado aqui para ser usado em todos
os arquivos .kv via `app.colors['...']`.
"""


def _hex(h: str, alpha: float = 1.0):
    h = h.lstrip("#")
    r = int(h[0:2], 16) / 255
    g = int(h[2:4], 16) / 255
    b = int(h[4:6], 16) / 255
    return (r, g, b, alpha)


COLORS = {
    "bg": _hex("05070A"),           # fundo
    "surface": _hex("10161F"),      # superfície (cards, app bar, inputs)
    "surface_alt": _hex("131A24"),  # variação da superfície (tiles do logo)
    "accent": _hex("00E6B8"),       # acento principal
    "accent_dark": _hex("00B894"),  # acento (gradiente/estado pressed)
    "accent_light": _hex("5DF5D6"), # acento (gradiente claro)
    "alert": _hex("FFB454"),        # alerta / destaque secundário
    "text": _hex("E8EDF2"),         # texto padrão
    "text_bright": _hex("F4F7F9"),  # texto de destaque/headings
    "text_dim": _hex("7C8A9A"),     # texto secundário
    "border": _hex("FFFFFF", 0.08), # bordas sutis sobre a superfície
}

# Nomes de fonte registrados em main.py (com fallback silencioso caso os
# arquivos .ttf não estejam presentes no build).
FONT_DISPLAY = "NMDisplay"   # Space Grotesk — logotipo, títulos
FONT_MONO = "NMMono"         # JetBrains Mono — labels técnicos, dados
