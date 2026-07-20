[app]
title = NOTE MAX
package.name = notemax
package.domain = org.notemax

source.dir = .
source.include_exts = py,kv,png,jpg,atlas,ttf

version = 0.1
# Versões fixas: o KivyMD 2.x reescreveu a API (MDRaisedButton, MDTopAppBar,
# Snackbar etc. mudaram/sumiram) e quebra o app, que foi escrito contra a
# API do KivyMD 1.x. Fixar evita que o build pegue uma versão incompatível.
#
# "pyaes" no lugar de "cryptography": o cryptography usa uma extensão em
# Rust que já causou dois builds quebrados nesse projeto e pode até falhar
# ao carregar em tempo real em alguns aparelhos (crash nativo, sem
# traceback Python). pyaes é puro Python, zero risco de build/runtime.
requirements = python3,kivy==2.3.1,kivymd==1.2.0,notion-client,pyaes,pillow

orientation = portrait
fullscreen = 0

# Ícone do app e tela de splash nativa (mostrada pelo Android antes do
# Python iniciar), com a identidade visual do NOTE MAX.
icon.filename = %(source.dir)s/assets/icon.png
presplash.filename = %(source.dir)s/assets/presplash.png
android.presplash_color = #05070A

android.permissions = INTERNET

# Build só para 64 bits: já é o formato exigido pela Play Store para
# apps novos (e evita retrabalho de manter 32 bits funcionando).
android.archs = arm64-v8a

# Mira a versão mais recente do Android (API 36 = Android 16).
android.api = 36
android.minapi = 24
android.ndk_api = 24

[buildozer]
log_level = 2
warn_on_root = 1
