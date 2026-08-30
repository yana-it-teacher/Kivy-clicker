[app]
# Використовувати найновішу гілку python-for-android
p4a.branch = master
# Назва гри
title = Jungle Clicker

# Ім'я пакета
package.name = jungleclicker
package.domain = org.jungleclicker

# Директорія з вихідним кодом (крапка означає поточну папку)
source.dir = .

# Розширення файлів, які будуть запаковані в APK
source.include_exts = py,png,jpg,kv,atlas,ttf,mp3,ogg

# Папки та файли, які потрібно додатково включити
source.include_patterns = assets/*,assets/images/*,assets/audio/*,assets/fonts/*

# Версія програми
version = 1.0

# Залежності (модулі Python)
requirements = python3,kivy

# Орієнтація екрана
orientation = portrait

# Архітектура (для підтримки більшості сучасних пристроїв)
android.archs = arm64-v8a, armeabi-v7a

# Дозволити бекап додатку (стандартне налаштування)
android.allow_backup = True

[buildozer]
# Рівень логування (2 - показувати детальну інформацію при збірці)
log_level = 2
warn_on_root = 1
