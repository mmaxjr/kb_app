[app]
title = KB App
package.name = kbapp
package.domain = org.kbapp

source.dir = .
source.include_exts = py,kv,png,jpg,atlas

version = 0.1
requirements = python3,kivy,kivymd,notion-client,cryptography

orientation = portrait
fullscreen = 0

android.permissions = INTERNET

# Build só para 64 bits: evita bug de cross-compile do pacote
# "cryptography" (Rust) para armeabi-v7a (32 bits), e já é o formato
# exigido pela Play Store para apps novos.
android.archs = arm64-v8a

# Mira a versão mais recente do Android (API 36 = Android 16).
android.api = 36
android.minapi = 24
android.ndk_api = 24

[buildozer]
log_level = 2
warn_on_root = 1
