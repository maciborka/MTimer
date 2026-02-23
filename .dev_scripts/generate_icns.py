#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генерация .icns из PNG-иконки для macOS.
Требуется наличие утилиты `iconutil` (часть Xcode Command Line Tools).

Создаёт каталог assets/app_icon.iconset и формирует assets/app_icon.icns.
"""
import os
import shutil
import subprocess
from pathlib import Path

BASE = Path(__file__).parent
ASSETS = BASE / 'assets'
PNG = ASSETS / 'app_icon.png'
ICONSET = ASSETS / 'app_icon.iconset'
ICNS = ASSETS / 'app_icon.icns'

# Карта размеров для iconset
SIZES = [
    (16, 1), (16, 2),
    (32, 1), (32, 2),
    (128, 1), (128, 2),
    (256, 1), (256, 2),
    (512, 1), (512, 2),
]


def ensure_png_exists():
    if not PNG.exists():
        # Попробуем сгенерировать PNG базовой иконки
        create_icon = BASE / 'create_icon.py'
        if create_icon.exists():
            print('PNG-иконка не найдена. Запускаю create_icon.py...')
            subprocess.check_call(['python3', str(create_icon)])
        else:
            raise FileNotFoundError(f'Не найден {PNG}. Положите app_icon.png в assets или запустите create_icon.py')


def prepare_iconset():
    if ICONSET.exists():
        shutil.rmtree(ICONSET)
    ICONSET.mkdir(parents=True, exist_ok=True)

    # Для простоты ресайзим из базового PNG во все нужные размеры
    from PIL import Image
    base = Image.open(PNG).convert('RGBA')

    for size, scale in SIZES:
        px = size * scale
        img = base.resize((px, px), Image.Resampling.LANCZOS)
        name = f'icon_{size}x{size}' + (f'@{scale}x' if scale > 1 else '') + '.png'
        out = ICONSET / name
        img.save(out, 'PNG')
        print('✓', out)


def build_icns():
    try:
        subprocess.check_call(['iconutil', '-c', 'icns', str(ICONSET), '-o', str(ICNS)])
    except FileNotFoundError:
        raise RuntimeError('Не найдена утилита iconutil. Установите Xcode Command Line Tools: xcode-select --install')


if __name__ == '__main__':
    ensure_png_exists()
    prepare_iconset()
    build_icns()
    print(f'\nГотово: {ICNS}')
