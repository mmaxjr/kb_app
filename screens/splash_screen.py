"""
Tela de splash ANIMADA, mostrada assim que o Kivy termina de
inicializar e some sozinha depois de ~1.6s, indo pra tela de senha.

Isso existe porque a splash nativa do Android (assets/presplash.png,
configurada no buildozer.spec) é só uma imagem estática -- ela é
mostrada pelo sistema operacional antes do Python sequer começar a
rodar, então não tem como animá-la. A splash de verdade, com o logo
pulsando e a barra enchendo, só pode acontecer aqui dentro, depois que
o Kivy já está de pé.
"""
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.graphics import Color, RoundedRectangle
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget
from kivymd.uix.screen import MDScreen

from theme import COLORS


class LoadingBar(Widget):
    """Barrinha de progresso simples: um retângulo de fundo (track) e
    um retângulo de preenchimento cuja largura acompanha `progress`
    (0.0 a 1.0), animável via kivy.animation.Animation."""

    progress = NumericProperty(0.06)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        with self.canvas:
            Color(*COLORS["border"])
            self._track = RoundedRectangle(radius=[3])
            Color(*COLORS["accent"])
            self._fill = RoundedRectangle(radius=[3])
        self.bind(pos=self._redraw, size=self._redraw, progress=self._redraw)

    def _redraw(self, *_args):
        self._track.pos = self.pos
        self._track.size = self.size
        fill_w = max(6, self.width * min(1.0, max(0.0, self.progress)))
        self._fill.pos = self.pos
        self._fill.size = (fill_w, self.height)


Factory.register("LoadingBar", cls=LoadingBar)


class SplashScreen(MDScreen):
    _blink_event = None
    _pulse_anim = None

    def on_enter(self, *args):
        self._blink_event = Clock.schedule_interval(self._toggle_cursor, 0.5)

        icon = self.ids.get("splash_icon")
        if icon:
            self._pulse_anim = Animation(opacity=0.55, duration=0.9) + Animation(
                opacity=1, duration=0.9
            )
            self._pulse_anim.repeat = True
            self._pulse_anim.start(icon)

        bar = self.ids.get("loading_bar")
        if bar:
            fill_anim = Animation(progress=1.0, duration=1.6, t="out_quad")
            fill_anim.bind(on_complete=lambda *a: self._ir_para_lock())
            fill_anim.start(bar)
        else:
            # Sem a barra por algum motivo -- não trava o usuário aqui
            Clock.schedule_once(lambda dt: self._ir_para_lock(), 1.6)

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
