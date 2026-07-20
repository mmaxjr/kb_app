"""
Tela de splash ANIMADA, mostrada assim que o Kivy termina de
inicializar e some sozinha depois de ~1.4s, indo pra tela de senha.

Isso existe porque a splash nativa do Android (assets/presplash.png,
configurada no buildozer.spec) é só uma imagem estática -- ela é
mostrada pelo sistema operacional antes do Python sequer começar a
rodar, então não tem como animá-la. A splash de verdade, com o logo
pulsando, só pode acontecer aqui dentro, depois que o Kivy já está
de pé.
"""
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.graphics import Color, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivymd.uix.screen import MDScreen

from theme import COLORS


class LoadingBar(Widget):
    """Barra de progresso simples, desenhada no canvas, que preenche
    de verdade da esquerda pra direita (animada em SplashScreen). É
    diferente da presplash nativa do Android: essa aqui roda depois
    que o Kivy já subiu, então consegue animar de verdade."""

    progress = NumericProperty(0)  # 0.0 a 1.0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*COLORS["border"])
            self._trilho = RoundedRectangle(radius=[dp(3)])
            Color(*COLORS["accent"])
            self._preenchido = RoundedRectangle(radius=[dp(3)])
        self.bind(pos=self._redesenhar, size=self._redesenhar, progress=self._redesenhar)

    def _redesenhar(self, *args):
        self._trilho.pos = self.pos
        self._trilho.size = self.size
        largura = max(0.0, min(1.0, self.progress)) * self.size[0]
        self._preenchido.pos = self.pos
        self._preenchido.size = (largura, self.size[1])


Factory.register("LoadingBar", cls=LoadingBar)


class SplashScreen(MDScreen):
    _blink_event = None
    _pulse_anim = None
    _progress_anim = None

    def on_enter(self, *args):
        self._blink_event = Clock.schedule_interval(self._toggle_cursor, 0.5)

        icon = self.ids.get("splash_icon")
        if icon:
            self._pulse_anim = Animation(opacity=0.55, duration=0.9) + Animation(
                opacity=1, duration=0.9
            )
            self._pulse_anim.repeat = True
            self._pulse_anim.start(icon)

        barra = self.ids.get("splash_bar")
        if barra:
            barra.progress = 0
            self._progress_anim = Animation(progress=1, duration=1.3, t="out_quad")
            self._progress_anim.start(barra)

        Clock.schedule_once(lambda dt: self._ir_para_lock(), 1.4)

    def _toggle_cursor(self, _dt):
        lbl = self.ids.get("splash_status")
        if not lbl:
            return
        lbl.text = (
            "CARREGANDO DADOS "
            if lbl.text.endswith("_")
            else "CARREGANDO DADOS_"
        )

    def _ir_para_lock(self):
        if self.manager and self.manager.current == "splash_screen":
            self.manager.current = "lock_screen"

    def on_leave(self, *args):
        if self._blink_event:
            self._blink_event.cancel()
            self._blink_event = None
        if self._pulse_anim:
            self._pulse_anim.cancel_all(self.ids.get("splash_icon"))
            self._pulse_anim = None
        if self._progress_anim:
            self._progress_anim.cancel_all(self.ids.get("splash_bar"))
            self._progress_anim = None
