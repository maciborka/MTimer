#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Генератор простой иконки для MacikTimer
Создаёт PNG иконку с таймером
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os
    
    def create_app_icon():
        # Создаём иконку 512x512 (можно масштабировать)
        size = 512
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Синий градиент фон (круг)
        center = size // 2
        radius = size // 2 - 20
        
        # Рисуем круглый фон (синий как в приложении)
        draw.ellipse(
            [center - radius, center - radius, center + radius, center + radius],
            fill=(32, 133, 245, 255)  # Синий цвет из приложения
        )
        
        # Белая внешняя граница
        border_width = 8
        draw.ellipse(
            [center - radius, center - radius, center + radius, center + radius],
            outline=(255, 255, 255, 255),
            width=border_width
        )
        
        # Рисуем циферблат (упрощённый)
        clock_radius = radius - 60
        
        # Белые метки часов (12, 3, 6, 9)
        mark_length = 30
        mark_width = 6
        for angle in [0, 90, 180, 270]:
            import math
            rad = math.radians(angle - 90)
            x1 = center + (clock_radius - mark_length) * math.cos(rad)
            y1 = center + (clock_radius - mark_length) * math.sin(rad)
            x2 = center + clock_radius * math.cos(rad)
            y2 = center + clock_radius * math.sin(rad)
            draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 255), width=mark_width)
        
        # Стрелки часов
        # Часовая стрелка (короткая, толстая) - на 10 часов
        import math
        hour_angle = math.radians(300 - 90)  # 10 часов
        hour_length = clock_radius * 0.5
        hour_x = center + hour_length * math.cos(hour_angle)
        hour_y = center + hour_length * math.sin(hour_angle)
        draw.line([(center, center), (hour_x, hour_y)], fill=(255, 255, 255, 255), width=12)
        
        # Минутная стрелка (длинная, средняя) - на 2 часа
        minute_angle = math.radians(60 - 90)  # 2 часа (10 минут)
        minute_length = clock_radius * 0.75
        minute_x = center + minute_length * math.cos(minute_angle)
        minute_y = center + minute_length * math.sin(minute_angle)
        draw.line([(center, center), (minute_x, minute_y)], fill=(255, 255, 255, 255), width=8)
        
        # Центральная точка
        dot_radius = 15
        draw.ellipse(
            [center - dot_radius, center - dot_radius, center + dot_radius, center + dot_radius],
            fill=(255, 255, 255, 255)
        )
        
        # Сохраняем
        base_dir = os.path.dirname(__file__)
        assets_dir = os.path.join(base_dir, 'assets')
        os.makedirs(assets_dir, exist_ok=True)
        
        output_path = os.path.join(assets_dir, 'app_icon.png')
        img.save(output_path, 'PNG')
        print(f"✓ Иконка создана: {output_path}")
        
        # Создаём также меньшие размеры для использования в диалогах
        for size_name, px in [('128', 128), ('64', 64), ('32', 32)]:
            small = img.resize((px, px), Image.Resampling.LANCZOS)
            small_path = os.path.join(assets_dir, f'app_icon_{size_name}.png')
            small.save(small_path, 'PNG')
            print(f"✓ Создана иконка {size_name}x{size_name}: {small_path}")
        
        return output_path

    if __name__ == '__main__':
        create_app_icon()

except ImportError:
    print("Pillow не установлен. Устанавливаю...")
    import subprocess
    subprocess.check_call(['pip3', 'install', 'Pillow'])
    print("\nПопробуйте запустить скрипт снова:")
    print("  python3 create_icon.py")
