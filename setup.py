from setuptools import setup
import os

APP = ['mac_app.py']
DATA_FILES = []

# Иконка и ресурсы (необязательны). Если файла/папки нет, py2app продолжит без них
icon_path = os.path.join('assets', 'app_icon.icns')
if not os.path.exists(icon_path):
    icon_path = None

resources = ['assets'] if os.path.isdir('assets') else []

OPTIONS = {
    'argv_emulation': True,
    'iconfile': icon_path,
    'resources': resources,
    # Явно включаем модули, которых не хватает на старте (__boot__ -> pkg_resources -> jaraco.*)
    'packages': ['pkg_resources', 'setuptools'],
    # Включаем только jaraco.* — autocommand/more_itertools тянутся как vendored-варианты внутри setuptools
    'includes': ['jaraco.text', 'jaraco.functools', 'jaraco.context'],
    'plist': {
        'CFBundleName': 'MTimer',
        'CFBundleDisplayName': 'MTimer',
        'CFBundleIdentifier': 'com.macik.timer',
        # Версии для стандартного About-панеля
        'CFBundleShortVersionString': '1.0.0',
        'CFBundleVersion': '1',
    # Авторские данные (будут показаны в About) — переносы строк через \n
    'NSHumanReadableCopyright': '© 2025 Maciborka Vitalik\nhttps://it-world.com.ua\nmaciborka@gmail.com',
    # Инфо-строка (устаревшая, но полезна в некоторых местах) — тоже с переносами строк
    'CFBundleGetInfoString': 'MTimer — Time tracking app.\nAuthor: Maciborka Vitalik\nhttps://it-world.com.ua/\nmaciborka@gmail.com',
        # Категория приложения для macOS
        'LSApplicationCategoryType': 'public.app-category.productivity',
    }
}

setup(
    app=APP,
    name='MTimer',
    author='Maciborka Vitalik',
    author_email='maciborka@gmail.com',
    url='https://it-world.com.ua/',
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
