"""
Snackbar (aviso rápido na base da tela) que funciona de verdade nesta
versão do KivyMD.

Em KivyMD 1.2.0 a classe `Snackbar` é só um alias depreciado de
`MDSnackbar`, que espera um widget (ex.: MDLabel) como filho -- NÃO
aceita mais um kwarg `text=`. Chamar `Snackbar(text="...")` (como o
resto do app fazia antes) levanta `TypeError` toda vez que qualquer tela
tenta mostrar um aviso -- inclusive salvar a senha mestra, criar nota,
editar nota, conectar uma integração. Isso é reproduzível 100% das vezes
e é a explicação mais provável para os fechamentos "sem erro nenhum"
relatados: o clique dispara o Snackbar quebrado, a exceção sobe pelo
`on_release`, e dependendo do aparelho isso pode nem chegar a mostrar o
popup de erro antes de a Activity do Android cair.

Use `mostrar_aviso("mensagem")` em vez de `Snackbar(text="mensagem")`
em qualquer tela nova.
"""
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar


def mostrar_aviso(texto: str, duration: float = 2.5) -> None:
    MDSnackbar(
        MDLabel(
            text=texto,
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1),
        ),
        duration=duration,
    ).open()
