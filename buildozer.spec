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

[buildozer]
log_level = 2
warn_on_root = 1
