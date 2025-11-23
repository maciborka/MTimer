# -*- coding: utf-8 -*-
"""
Модуль локализации для поддержки украинского, русского и английского языков
"""

import locale
import os

# Словари переводов
TRANSLATIONS = {
    'en': {
        # Основные элементы
        'app_name': 'MTimer',
        'show': 'Show',
        'show_app': 'Show MTimer',
        'quit': 'Quit',
        'start': 'Start',
        'stop': 'Stop',
        'continue': '▶ Continue',
        
        # Фильтры
        'today': 'Today',
        'week': 'Week',
        'month': 'Month',
        
        # Проекты
        'all_projects': 'All Projects',
        'new_project': 'New Project',
        'project_name': 'Project name:',
        'hourly_rate': 'Hourly rate ($/h):',
        'create': 'Create',
        'cancel': 'Cancel',
        
        # Таблица
        'description_project': 'Description / Project',
        'time': 'Time',
        'duration': 'Duration',
        'no_name': 'No name',
        'no_description': 'No description',
        'running': 'Running...',
        
        # Описание
        'enter_description': 'Enter description...',
        'default_description': 'Programming',
        
        # Предупреждения
        'please_select_project': 'Please select a project!',
        'stop_current_timer': 'Stop current timer first',
        'ok': 'Ok',
        
        # Итоги
        'total': 'TOTAL',
        'today_label': 'TODAY',
        'week_label': 'WEEK',
        'month_label': 'MONTH',
        
        # Уведомления
        'timer_started': 'Timer started',
        'timer_stopped': 'Timer stopped',
        
        # Меню статус-бара
        'recent_tasks': 'Recent tasks:',
        
        # Удаление записей
        'delete_session': 'Delete Session',
        'delete_confirm_title': 'Confirm Deletion',
        'delete_confirm_message': 'Are you sure you want to delete this session? This action cannot be undone.',
        'delete': 'Delete',
        
        # Настройки проектов
        'settings': 'Settings',
        'statistics': 'Statistics',
        'project_settings': 'Project Settings',
        'edit_project': 'Edit Project',
        'save': 'Save',
        'project': 'Project',
        'rate': 'Rate ($/h)',
        
        # Меню приложения
        'about': 'About MTimer',
        'preferences': 'Preferences…',
        'services': 'Services',
        'hide': 'Hide MTimer',
        'hide_others': 'Hide Others',
        'show_all': 'Show All',
        'edit': 'Edit',
        'undo': 'Undo',
        'redo': 'Redo',
        'cut': 'Cut',
        'copy': 'Copy',
        'paste': 'Paste',
        'select_all': 'Select All',
        'window': 'Window',
        'minimize': 'Minimize',
        'zoom': 'Zoom',
        'close': 'Close',
        'bring_all_to_front': 'Bring All to Front',
    },
    'ru': {
        # Основные элементы
        'app_name': 'MTimer',
        'show': 'Показать',
        'show_app': 'Показать MTimer',
        'quit': 'Выйти',
        'start': 'Старт',
        'stop': 'Стоп',
        'continue': '▶ Продолжить',
        
        # Фильтры
        'today': 'Сегодня',
        'week': 'Неделя',
        'month': 'Месяц',
        
        # Проекты
        'all_projects': 'Все проекты',
        'new_project': 'Новый проект',
        'project_name': 'Название проекта:',
        'hourly_rate': 'Ставка ($/ч):',
        'create': 'Создать',
        'cancel': 'Отмена',
        
        # Таблица
        'description_project': 'Описание / Проект',
        'time': 'Время',
        'duration': 'Длительность',
        'no_name': 'Без названия',
        'no_description': 'Без описания',
        'running': 'Идет...',
        
        # Описание
        'enter_description': 'Введите описание...',
        'default_description': 'Программирование',
        
        # Предупреждения
        'please_select_project': 'Пожалуйста, выберите проект!',
        'stop_current_timer': 'Сначала остановите текущий таймер',
        'ok': 'Ок',
        
        # Итоги
        'total': 'ВСЕГО',
        'today_label': 'СЕГОДНЯ',
        'week_label': 'ЗА НЕДЕЛЮ',
        'month_label': 'ЗА МЕСЯЦ',
        
        # Уведомления
        'timer_started': 'Таймер запущен',
        'timer_stopped': 'Таймер остановлен',
        
        # Меню статус-бара
        'recent_tasks': 'Последние задачи:',
        
        # Удаление записей
        'delete_session': 'Удалить запись',
        'delete_confirm_title': 'Подтверждение удаления',
        'delete_confirm_message': 'Вы уверены, что хотите удалить эту запись? Это действие нельзя отменить.',
        'delete': 'Удалить',
        
        # Настройки проектов
        'settings': 'Настройки',
        'statistics': 'Статистика',
        'project_settings': 'Настройки проекта',
        'edit_project': 'Редактировать проект',
        'save': 'Сохранить',
        'project': 'Проект',
        'rate': 'Ставка (₽/ч)',
        
        # Меню приложения
        'about': 'О программе MTimer',
        'preferences': 'Настройки…',
        'services': 'Службы',
        'hide': 'Скрыть MTimer',
        'hide_others': 'Скрыть остальные',
        'show_all': 'Показать все',
        'edit': 'Правка',
        'undo': 'Отменить',
        'redo': 'Повторить',
        'cut': 'Вырезать',
        'copy': 'Копировать',
        'paste': 'Вставить',
        'select_all': 'Выбрать все',
        'window': 'Окно',
        'minimize': 'Свернуть',
        'zoom': 'Увеличить',
        'close': 'Закрыть',
        'bring_all_to_front': 'Все окна — на передний план',
    },
    'uk': {
        # Основні елементи
        'app_name': 'MTimer',
        'show': 'Показати',
        'show_app': 'Показати MTimer',
        'quit': 'Вийти',
        'start': 'Старт',
        'stop': 'Стоп',
        'continue': '▶ Продовжити',
        
        # Фільтри
        'today': 'Сьогодні',
        'week': 'Тиждень',
        'month': 'Місяць',
        
        # Проекти
        'all_projects': 'Всі проекти',
        'new_project': 'Новий проект',
        'project_name': 'Назва проекту:',
        'hourly_rate': 'Ставка ($/год):',
        'create': 'Створити',
        'cancel': 'Скасувати',
        
        # Таблиця
        'description_project': 'Опис / Проект',
        'time': 'Час',
        'duration': 'Тривалість',
        'no_name': 'Без назви',
        'no_description': 'Без опису',
        'running': 'Йде...',
        
        # Опис
        'enter_description': 'Введіть опис...',
        'default_description': 'Програмування',
        
        # Попередження
        'please_select_project': 'Будь ласка, оберіть проект!',
        'stop_current_timer': 'Спочатку зупиніть поточний таймер',
        'ok': 'Гаразд',
        
        # Підсумки
        'total': 'ВСЬОГО',
        'today_label': 'СЬОГОДНІ',
        'week_label': 'ЗА ТИЖДЕНЬ',
        'month_label': 'ЗА МІСЯЦЬ',
        
        # Сповіщення
        'timer_started': 'Таймер запущено',
        'timer_stopped': 'Таймер зупинено',
        
        # Меню статус-бара
        'recent_tasks': 'Останні завдання:',
        
        # Видалення записів
        'delete_session': 'Видалити запис',
        'delete_confirm_title': 'Підтвердження видалення',
        'delete_confirm_message': 'Ви впевнені, що хочете видалити цей запис? Цю дію неможливо скасувати.',
        'delete': 'Видалити',
        
        # Налаштування проектів
        'settings': 'Налаштування',
        'statistics': 'Статистика',
        'project_settings': 'Налаштування проектів',
        'edit_project': 'Змінити проект',
        'save': 'Зберегти',
        'project': 'Проект',
        'rate': 'Ставка ($/год)',
        
        # Меню програми
        'about': 'Про програму MTimer',
        'preferences': 'Налаштування…',
        'services': 'Служби',
        'hide': 'Сховати MTimer',
        'hide_others': 'Сховати інші',
        'show_all': 'Показати всі',
        'edit': 'Правка',
        'undo': 'Скасувати',
        'redo': 'Повторити',
        'cut': 'Вирізати',
        'copy': 'Копіювати',
        'paste': 'Вставити',
        'select_all': 'Вибрати все',
        'window': 'Вікно',
        'minimize': 'Згорнути',
        'zoom': 'Збільшити',
        'close': 'Закрити',
        'bring_all_to_front': 'Всі вікна — на передній план',
    }
}


class Localization:
    """Класс для управления локализацией приложения"""
    
    def __init__(self):
        self.current_language = self._detect_system_language()
        
    def _detect_system_language(self):
        """Определяет язык системы и возвращает поддерживаемый код языка"""
        detected_lang = None
        
        try:
            # Метод 1: Пытаемся получить язык из NSLocale (предпочитаемые языки)
            from Foundation import NSLocale
            
            # Получаем список предпочитаемых языков пользователя
            preferred_languages = NSLocale.preferredLanguages()
            if preferred_languages and len(preferred_languages) > 0:
                first_lang = str(preferred_languages[0]).lower()
                print(f"[Localization] Preferred language: {first_lang}")
                
                # Извлекаем код языка (первые 2 символа)
                if first_lang.startswith('uk') or first_lang.startswith('ua'):
                    detected_lang = 'uk'
                elif first_lang.startswith('ru'):
                    detected_lang = 'ru'
                elif first_lang.startswith('en'):
                    detected_lang = 'en'
            
            # Если не определили через preferredLanguages, пробуем currentLocale
            if not detected_lang:
                current_locale = NSLocale.currentLocale()
                lang_code = str(current_locale.languageCode()).lower()
                print(f"[Localization] Current locale language: {lang_code}")
                
                if lang_code in ['uk', 'ua']:
                    detected_lang = 'uk'
                elif lang_code == 'ru':
                    detected_lang = 'ru'
                elif lang_code == 'en':
                    detected_lang = 'en'
                    
        except Exception as e:
            print(f"[Localization] NSLocale detection failed: {e}")
        
        # Метод 2: Если не получилось через Foundation, пробуем через locale
        if not detected_lang:
            try:
                system_locale = locale.getdefaultlocale()[0]
                print(f"[Localization] System locale: {system_locale}")
                if system_locale:
                    lang = system_locale.split('_')[0].lower()
                    if lang in ['uk', 'ua']:
                        detected_lang = 'uk'
                    elif lang == 'ru':
                        detected_lang = 'ru'
                    elif lang == 'en':
                        detected_lang = 'en'
            except Exception as e:
                print(f"[Localization] locale detection failed: {e}")
        
        # По умолчанию русский (так как у вас система на украинском, но хотим русский)
        if not detected_lang:
            detected_lang = 'ru'
        
        print(f"[Localization] Final detected language: {detected_lang}")
        return detected_lang
    
    def get(self, key, default=None):
        """Получает перевод для ключа"""
        translations = TRANSLATIONS.get(self.current_language, TRANSLATIONS['en'])
        return translations.get(key, default or key)
    
    def set_language(self, lang_code):
        """Устанавливает язык вручную"""
        if lang_code in TRANSLATIONS:
            self.current_language = lang_code
    
    def get_current_language(self):
        """Возвращает текущий язык"""
        return self.current_language


# Глобальный экземпляр локализации
_localization = Localization()

def t(key, default=None):
    """Функция для быстрого доступа к переводам"""
    return _localization.get(key, default)

def get_localization():
    """Возвращает экземпляр локализации"""
    return _localization
