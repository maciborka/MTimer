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
        'custom_period': 'Custom Period',
        'from_date': 'From:',
        'to_date': 'To:',
        'apply': 'Apply',
        
        # Проекты
        'all_projects': 'All Projects',
        'new_project': 'New Project',
        'project_name': 'Project name:',
        'company': 'Company:',
        'no_company': 'No company',
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
        
        # Отметка как оплаченное
        'mark_as_paid_title': 'Mark as Paid',
        'mark_as_paid_message': 'Mark this session as paid? It will be hidden from the main view.',
        'paid': 'Paid',
        
        # Настройки проектов
        'settings': 'Settings',
        'statistics': 'Statistics',
        'project_settings': 'Project Settings',
        'edit_project': 'Edit Project',
        'save': 'Save',
        'project': 'Project',
        'rate': 'Rate ($/h)',
        'delete_project': 'Delete Project',
        'confirm_delete_project': 'Are you sure you want to delete this project? This action cannot be undone.',
        'cannot_delete_project': 'Cannot delete project with existing sessions',
        
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
        
        # Настройки и бекапы
        'system_settings': 'System',
        'data': 'Data',
        'backup_db': 'Backup Database',
        'backup_description': 'Save a copy of the database',
        'restore_from_backup': 'Restore from Backup',
        'restore_description': 'Load database from backup file',
        'reminder_interval': 'Reminder interval:',
        'minutes': 'minutes',
        'reminder_description': 'How often to show reminder about current activity (specify number of minutes)',
        'notification_sound': 'Notification sound:',
        'preview_sound': 'Preview',
        'sound_glass': 'Glass',
        'sound_ping': 'Ping',
        'sound_pop': 'Pop',
        'sound_purr': 'Purr',
        'sound_sosumi': 'Sosumi',
        'sound_submarine': 'Submarine',
        'sound_blow': 'Blow',
        'sound_bottle': 'Bottle',
        'sound_frog': 'Frog',
        'sound_funk': 'Funk',
        'sound_hero': 'Hero',
        'sound_morse': 'Morse',
        'sound_tink': 'Tink',
        'sound_basso': 'Basso',
        'save_backup_title': 'Save Database Backup',
        'backup_created': 'Backup created successfully',
        'database_saved_to': 'Database saved to:',
        'backup_error': 'Backup Error',
        'restore_title': 'Restore from Backup',
        'restore_warning': 'WARNING: Current database will be replaced with selected backup. All unsaved data will be lost. It is recommended to create a backup of current database first.\n\nContinue?',
        'restore_continue': 'Continue',
        'select_backup_file': 'Select backup file',
        'database_restored': 'Restore completed',
        'database_restore_success': 'Database successfully restored from backup. Restart the application to apply changes.',
        'restore_error': 'Restore Error',
        'error': 'Error',
        'enter_integer': 'Enter whole number of minutes (e.g., 60)',
        'interval_range': 'Interval must be between 1 and 1440 minutes (24 hours)',
        'setting_saved': 'Setting saved',
        'interval_saved': 'Reminder interval set: {0} minutes.\n\nNew interval will be applied on next timer start.',
        
        # Напоминания
        'still_working_question': 'Are you still working on this task?',
        'yes': 'Yes',
        'no': 'No',
        
        # Статистика
        'all_tasks': 'Statistics (All Tasks)',
        'period': 'Period:',
        'all': 'All',
        
        # Настройка языка
        'interface_language': 'Interface Language:',
        'language_english': 'English',
        'language_russian': 'Russian',
        'language_ukrainian': 'Ukrainian',
        'language_hungarian': 'Hungarian',
        'language_description': 'Select interface language',
        'language_saved': 'Language changed to {0}.\n\nRestart the application to apply changes.',
        
        # Меню "Данные"
        'data_menu': 'Data',
        'companies_menu': 'Companies',
        'projects_menu': 'Projects',
        'work_types_menu': 'Work Types',
        
        # Интеграции
        'integrations': 'Integrations',
        'integrations_placeholder': 'Integration settings will be here\n(GitHub, Jira, Slack, etc.)',
        
        # Управление компаниями
        'manage_companies': 'Manage Companies',
        'code': 'Code',
        'company_name': 'Company Name',
        'add': 'Add',
        'add_company': 'Add Company',
        'identification_code': 'Identification Code:',
        'enter_code_and_name': 'Enter identification code and full company name',
        'edit_company': 'Edit Company',
        'change_code_and_name': 'Change code and company name',
        'full_company_name': 'Full company name',
        
        # Управление видами работ
        'manage_work_types': 'Manage Work Types',
        'name': 'Name',
        'description': 'Description',
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
        'custom_period': 'Свой период',
        'from_date': 'С:',
        'to_date': 'По:',
        'apply': 'Применить',
        
        # Проекты
        'all_projects': 'Все проекты',
        'new_project': 'Новый проект',
        'project_name': 'Название проекта:',        'company': 'Компания:',
        'no_company': 'Без компании',        'hourly_rate': 'Ставка ($/ч):',
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
        
        # Отметка как оплаченное
        'mark_as_paid_title': 'Отметить как оплаченное',
        'mark_as_paid_message': 'Отметить эту задачу как оплаченную? Она будет скрыта из основного окна.',
        'paid': 'Оплачено',
        
        # Настройки проектов
        'settings': 'Настройки',
        'statistics': 'Статистика',
        'project_settings': 'Настройки проекта',
        'edit_project': 'Редактировать проект',
        'save': 'Сохранить',
        'project': 'Проект',
        'rate': 'Ставка (₽/ч)',
        'delete_project': 'Удалить проект',
        'confirm_delete_project': 'Вы уверены, что хотите удалить этот проект? Это действие нельзя отменить.',
        'cannot_delete_project': 'Невозможно удалить проект с существующими задачами',
        
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
        
        # Настройки и бекапы
        'system_settings': 'Системные',
        'data': 'Данные',
        'backup_db': 'Создать бекап БД',
        'backup_description': 'Сохранить копию базы данных',
        'restore_from_backup': 'Восстановить из бекапа',
        'restore_description': 'Загрузить базу данных из файла бекапа',
        'reminder_interval': 'Интервал напоминаний:',
        'minutes': 'минут',
        'reminder_description': 'Как часто показывать напоминание о текущей активности (укажите количество минут)',
        'notification_sound': 'Звук уведомления:',
        'preview_sound': 'Прослушать',
        'sound_glass': 'Стекло',
        'sound_ping': 'Пинг',
        'sound_pop': 'Поп',
        'sound_purr': 'Мурлыканье',
        'sound_sosumi': 'Сосуми',
        'sound_submarine': 'Подлодка',
        'sound_blow': 'Дуновение',
        'sound_bottle': 'Бутылка',
        'sound_frog': 'Лягушка',
        'sound_funk': 'Фанк',
        'sound_hero': 'Герой',
        'sound_morse': 'Морзе',
        'sound_tink': 'Звон',
        'sound_basso': 'Бассо',
        'save_backup_title': 'Сохранить бекап базы данных',
        'backup_created': 'Бекап создан успешно',
        'database_saved_to': 'База данных сохранена в:',
        'backup_error': 'Ошибка создания бекапа',
        'restore_title': 'Восстановление из бекапа',
        'restore_warning': 'ВНИМАНИЕ: Текущая база данных будет заменена на выбранный бекап. Все несохраненные данные будут потеряны. Рекомендуется сначала создать бекап текущей базы.\n\nПродолжить?',
        'restore_continue': 'Продолжить',
        'select_backup_file': 'Выберите файл бекапа',
        'database_restored': 'Восстановление завершено',
        'database_restore_success': 'База данных успешно восстановлена из бекапа. Перезапустите приложение для применения изменений.',
        'restore_error': 'Ошибка восстановления',
        'error': 'Ошибка',
        'enter_integer': 'Введите целое число минут (например: 60)',
        'interval_range': 'Интервал должен быть от 1 до 1440 минут (24 часа)',
        'setting_saved': 'Настройка сохранена',
        'interval_saved': 'Интервал напоминаний установлен: {0} минут.\n\nНовый интервал будет применен при следующем запуске таймера.',
        
        # Напоминания
        'still_working_question': 'Вы еще работаете над этой задачей?',
        'yes': 'Да',
        'no': 'Нет',
        
        # Статистика
        'all_tasks': 'Статистика (Все задачи)',
        'period': 'Период:',
        'all': 'Все',
        
        # Настройка языка
        'interface_language': 'Язык интерфейса:',
        'language_english': 'Английский',
        'language_russian': 'Русский',
        'language_ukrainian': 'Украинский',
        'language_hungarian': 'Венгерский',
        'language_description': 'Выберите язык интерфейса',
        'language_saved': 'Язык изменен на {0}.\n\nПерезапустите приложение для применения изменений.',
        
        # Меню "Данные"
        'data_menu': 'Данные',
        'companies_menu': 'Компании',
        'projects_menu': 'Проекты',
        'work_types_menu': 'Виды работ',
        
        # Интеграции
        'integrations': 'Интеграции',
        'integrations_placeholder': 'Здесь будут настройки интеграций\n(GitHub, Jira, Slack и др.)',
        
        # Управление компаниями
        'manage_companies': 'Управление компаниями',
        'code': 'Код',
        'company_name': 'Название компании',
        'add': 'Добавить',
        'add_company': 'Добавить компанию',
        'identification_code': 'Идентификационный код:',
        'enter_code_and_name': 'Введите идентификационный код и полное название компании',
        'edit_company': 'Редактирование компании',
        'change_code_and_name': 'Измените код и название компании',
        'full_company_name': 'Полное название компании',
        
        # Управление видами работ
        'manage_work_types': 'Управление видами работ',
        'name': 'Название',
        'description': 'Описание',
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
        'custom_period': 'Свій період',
        'from_date': 'З:',
        'to_date': 'По:',
        'apply': 'Застосувати',
        
        # Проекти
        'all_projects': 'Всі проекти',
        'new_project': 'Новий проект',
        'project_name': 'Назва проекту:',        'company': 'Компанія:',
        'no_company': 'Без компанії',        'hourly_rate': 'Ставка ($/година):',
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
        
        # Відмітка як оплачене
        'mark_as_paid_title': 'Позначити як оплачене',
        'mark_as_paid_message': 'Позначити це завдання як оплачене? Воно буде приховане з основного вікна.',
        'paid': 'Оплачено',
        
        # Налаштування проектів
        'settings': 'Налаштування',
        'statistics': 'Статистика',
        'project_settings': 'Налаштування проектів',
        'edit_project': 'Змінити проект',
        'save': 'Зберегти',
        'project': 'Проект',
        'rate': 'Ставка ($/година)',
        'delete_project': 'Видалити проект',
        'confirm_delete_project': 'Ви впевнені, що хочете видалити цей проект? Цю дію не можна скасувати.',
        'cannot_delete_project': 'Неможливо видалити проект з існуючими задачами',
        
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
        
        # Налаштування та бекапи
        'system_settings': 'Системні',
        'data': 'Дані',
        'backup_db': 'Створити бекап БД',
        'backup_description': 'Зберегти копію бази даних',
        'restore_from_backup': 'Відновити з бекапу',
        'restore_description': 'Завантажити базу даних з файлу бекапу',
        'reminder_interval': 'Інтервал нагадувань:',
        'minutes': 'хвилин',
        'reminder_description': 'Як часто показувати нагадування про поточну активність (вкажіть кількість хвилин)',
        'notification_sound': 'Звук сповіщення:',
        'preview_sound': 'Прослухати',
        'sound_glass': 'Скло',
        'sound_ping': 'Пінг',
        'sound_pop': 'Поп',
        'sound_purr': 'Муркотіння',
        'sound_sosumi': 'Сосумі',
        'sound_submarine': 'Підводний човен',
        'sound_blow': 'Подув',
        'sound_bottle': 'Пляшка',
        'sound_frog': 'Жаба',
        'sound_funk': 'Фанк',
        'sound_hero': 'Герой',
        'sound_morse': 'Морзе',
        'sound_tink': 'Дзвін',
        'sound_basso': 'Бассо',
        'save_backup_title': 'Зберегти бекап бази даних',
        'backup_created': 'Бекап створено успішно',
        'database_saved_to': 'База даних збережена в:',
        'backup_error': 'Помилка створення бекапу',
        'restore_title': 'Відновлення з бекапу',
        'restore_warning': 'УВАГА: Поточна база даних буде замінена на обраний бекап. Всі незбережені дані будуть втрачені. Рекомендується спочатку створити бекап поточної бази.\n\nПродовжити?',
        'restore_continue': 'Продовжити',
        'select_backup_file': 'Оберіть файл бекапу',
        'database_restored': 'Відновлення завершено',
        'database_restore_success': 'Базу даних успішно відновлено з бекапу. Перезапустіть програму для застосування змін.',
        'restore_error': 'Помилка відновлення',
        'error': 'Помилка',
        'enter_integer': 'Введіть ціле число хвилин (наприклад: 60)',
        'interval_range': 'Інтервал повинен бути від 1 до 1440 хвилин (24 години)',
        'setting_saved': 'Налаштування збережено',
        'interval_saved': 'Інтервал нагадувань встановлено: {0} хвилин.\n\nНовий інтервал буде застосовано при наступному запуску таймера.',
        
        # Нагадування
        'still_working_question': 'Ви ще працюєте над цим завданням?',
        'yes': 'Так',
        'no': 'Ні',
        
        # Статистика
        'all_tasks': 'Статистика (Всі завдання)',
        'period': 'Період:',
        'all': 'Всі',
        
        # Налаштування мови
        'interface_language': 'Мова інтерфейсу:',
        'language_english': 'Англійська',
        'language_russian': 'Російська',
        'language_ukrainian': 'Українська',
        'language_hungarian': 'Угорська',
        'language_description': 'Оберіть мову інтерфейсу',
        'language_saved': 'Мову змінено на {0}.\n\nПерезапустіть програму для застосування змін.',
        
        # Меню "Дані"
        'data_menu': 'Дані',
        'companies_menu': 'Компанії',
        'projects_menu': 'Проекти',
        'work_types_menu': 'Види робіт',
        
        # Інтеграції
        'integrations': 'Інтеграції',
        'integrations_placeholder': 'Тут будуть налаштування інтеграцій\n(GitHub, Jira, Slack та ін.)',
        
        # Управління компаніями
        'manage_companies': 'Управління компаніями',
        'code': 'Код',
        'company_name': 'Назва компанії',
        'add': 'Додати',
        'add_company': 'Додати компанію',
        'identification_code': 'Ідентифікаційний код:',
        'enter_code_and_name': 'Введіть ідентифікаційний код та повну назву компанії',
        'edit_company': 'Редагування компанії',
        'change_code_and_name': 'Змініть код і назву компанії',
        'full_company_name': 'Повна назва компанії',
        
        # Управління видами робіт
        'manage_work_types': 'Управління видами робіт',
        'name': 'Назва',
        'description': 'Опис',
    },
    'hu': {
        # Основні елементи
        'app_name': 'MTimer',
        'show': 'Mutat',
        'show_app': 'MTimer mutatása',
        'quit': 'Kilépés',
        'start': 'Start',
        'stop': 'Stop',
        'continue': '▶ Folytatás',
        
        # Szűrők
        'today': 'Ma',
        'week': 'Hét',
        'month': 'Hónap',
        'custom_period': 'Egyéni időszak',
        'from_date': 'Ettől:',
        'to_date': 'Eddig:',
        'apply': 'Alkalmazás',
        
        # Projektek
        'all_projects': 'Minden projekt',
        'new_project': 'Új projekt',
        'project_name': 'Projekt neve:',        'company': 'Cég:',
        'no_company': 'Cég nélkül',        'hourly_rate': 'Óradíj ($/ó):',
        'create': 'Létrehozás',
        'cancel': 'Mégse',
        
        # Táblázat
        'description_project': 'Leírás / Projekt',
        'time': 'Idő',
        'duration': 'Időtartam',
        'no_name': 'Név nélkül',
        'no_description': 'Leírás nélkül',
        'running': 'Fut...',
        
        # Leírás
        'enter_description': 'Írj leírást...',
        'default_description': 'Programozás',
        
        # Figyelmeztetések
        'please_select_project': 'Kérlek válassz projektet!',
        'stop_current_timer': 'Először állítsd le a jelenlegi időmérőt',
        'ok': 'OK',
        
        # Összegzés
        'total': 'ÖSSZESEN',
        'today_label': 'MA',
        'week_label': 'EZ A HÉT',
        'month_label': 'EZ A HÓNAP',
        
        # Értesítések
        'timer_started': 'Időmérő elindítva',
        'timer_stopped': 'Időmérő leállítva',
        
        # Állapotsor menü
        'recent_tasks': 'Legutóbbi feladatok:',
        
        # Bejegyzések törlése
        'delete_session': 'Munkamenet törlése',
        'delete_confirm_title': 'Törlés megerősítése',
        'delete_confirm_message': 'Biztosan törölni szeretnéd ezt a munkamenetet? Ez a művelet nem vonható vissza.',
        'delete': 'Törlés',
        
        # Fizetve jelölés
        'mark_as_paid_title': 'Fizetettként megjelölés',
        'mark_as_paid_message': 'Megjelöljük ezt a feladatot fizetettként? El lesz rejtve a fő nézetből.',
        'paid': 'Fizetve',
        
        # Projekt beállítások
        'settings': 'Beállítások',
        'statistics': 'Statisztika',
        'project_settings': 'Projekt beállítások',
        'edit_project': 'Projekt szerkesztése',
        'save': 'Mentés',
        'project': 'Projekt',
        'rate': 'Díj ($/ó)',
        'delete_project': 'Projekt törlése',
        'confirm_delete_project': 'Biztosan törölni szeretnéd ezt a projektet? Ez a művelet nem vonható vissza.',
        'cannot_delete_project': 'Nem lehet törölni a projektet meglévő feladatokkal',
        
        # Alkalmazás menü
        'about': 'Az MTimer névjegye',
        'preferences': 'Beállítások…',
        'services': 'Szolgáltatások',
        'hide': 'MTimer elrejtése',
        'hide_others': 'Mások elrejtése',
        'show_all': 'Összes mutatása',
        'edit': 'Szerkesztés',
        'undo': 'Visszavonás',
        'redo': 'Újra',
        'cut': 'Kivágás',
        'copy': 'Másolás',
        'paste': 'Beillesztés',
        'select_all': 'Összes kijelölése',
        'window': 'Ablak',
        'minimize': 'Kis méret',
        'zoom': 'Nagyítás',
        'close': 'Bezárás',
        'bring_all_to_front': 'Összes előtérbe',
        
        # Beállítások és mentések
        'system_settings': 'Rendszer',
        'data': 'Adatok',
        'backup_db': 'Adatbázis mentése',
        'backup_description': 'Adatbázis másolatának mentése',
        'restore_from_backup': 'Visszaállítás mentésből',
        'restore_description': 'Adatbázis betöltése mentési fájlból',
        'reminder_interval': 'Emlékeztető időköze:',
        'minutes': 'perc',
        'reminder_description': 'Milyen gyakran jelenjen meg emlékeztető a jelenlegi tevékenységről (adj meg perceket)',
        'notification_sound': 'Értesítési hang:',
        'preview_sound': 'Meghallgat',
        'sound_glass': 'Üveg',
        'sound_ping': 'Ping',
        'sound_pop': 'Pop',
        'sound_purr': 'Dorombolás',
        'sound_sosumi': 'Sosumi',
        'sound_submarine': 'Tengeralattjáró',
        'sound_blow': 'Fújás',
        'sound_bottle': 'Üveg',
        'sound_frog': 'Béka',
        'sound_funk': 'Funk',
        'sound_hero': 'Hős',
        'sound_morse': 'Morse',
        'sound_tink': 'Csengő',
        'sound_basso': 'Basso',
        'save_backup_title': 'Adatbázis mentés mentése',
        'backup_created': 'Mentés sikeresen létrehozva',
        'database_saved_to': 'Adatbázis mentve ide:',
        'backup_error': 'Mentési hiba',
        'restore_title': 'Visszaállítás mentésből',
        'restore_warning': 'FIGYELEM: A jelenlegi adatbázis felül lesz írva a kiválasztott mentéssel. Minden nem mentett adat el fog veszni. Javasolt előbb mentést készíteni a jelenlegi adatbázisról.\n\nFolytatod?',
        'restore_continue': 'Folytatás',
        'select_backup_file': 'Válassz mentési fájlt',
        'database_restored': 'Visszaállítás befejezve',
        'database_restore_success': 'Adatbázis sikeresen visszaállítva a mentésből. Indítsd újra az alkalmazást a változások alkalmazásához.',
        'restore_error': 'Visszaállítási hiba',
        'error': 'Hiba',
        'enter_integer': 'Adj meg egész számot percekben (pl.: 60)',
        'interval_range': 'Az időköznek 1 és 1440 perc között kell lennie (24 óra)',
        'setting_saved': 'Beállítás mentve',
        'interval_saved': 'Emlékeztető időköz beállítva: {0} perc.\n\nAz új időköz a következő időmérő indításkor lép életbe.',
        
        # Emlékeztetők
        'still_working_question': 'Még mindig ezen a feladaton dolgozol?',
        'yes': 'Igen',
        'no': 'Nem',
        
        # Statisztika
        'all_tasks': 'Statisztika (Minden feladat)',
        'period': 'Időszak:',
        'all': 'Összes',
        
        # Nyelv beállítások
        'interface_language': 'Felület nyelve:',
        'language_english': 'Angol',
        'language_russian': 'Orosz',
        'language_ukrainian': 'Ukrán',
        'language_hungarian': 'Magyar',
        'language_description': 'Válaszd ki a felület nyelvét',
        'language_saved': 'Nyelv megváltoztatva: {0}.\n\nIndítsd újra az alkalmazást a változások alkalmazásához.',
        
        # "Adatok" menü
        'data_menu': 'Adatok',
        'companies_menu': 'Cégek',
        'projects_menu': 'Projektek',
        'work_types_menu': 'Munkatípusok',
        
        # Integrációk
        'integrations': 'Integrációk',
        'integrations_placeholder': 'Itt lesznek az integrációs beállítások\n(GitHub, Jira, Slack stb.)',
        
        # Cégek kezelése
        'manage_companies': 'Cégek kezelése',
        'code': 'Kód',
        'company_name': 'Cégnév',
        'add': 'Hozzáadás',
        'add_company': 'Cég hozzáadása',
        'identification_code': 'Azonosító kód:',
        'enter_code_and_name': 'Add meg az azonosító kódot és a teljes cégnevet',
        'edit_company': 'Cég szerkesztése',
        'change_code_and_name': 'Módosítsd a kódot és a cégnevet',
        'full_company_name': 'Teljes cégnév',
        
        # Munkatípusok kezelése
        'manage_work_types': 'Munkatípusok kezelése',
        'name': 'Név',
        'description': 'Leírás',
    }
}


class Localization:
    """Класс для управления локализацией приложения"""
    
    def __init__(self):
        # Сначала пробуем загрузить сохраненный язык
        saved_lang = self._load_saved_language()
        if saved_lang:
            self.current_language = saved_lang
            print(f"[Localization] Loaded saved language: {saved_lang}")
        else:
            self.current_language = self._detect_system_language()
    
    def _load_saved_language(self):
        """Загружает сохраненный язык из NSUserDefaults"""
        try:
            from Foundation import NSUserDefaults
            defaults = NSUserDefaults.standardUserDefaults()
            saved_lang = defaults.stringForKey_("interfaceLanguage")
            if saved_lang and saved_lang in TRANSLATIONS:
                return str(saved_lang)
        except Exception as e:
            print(f"[Localization] Failed to load saved language: {e}")
        return None
        
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
                elif first_lang.startswith('hu'):
                    detected_lang = 'hu'
            
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
                elif lang_code == 'hu':
                    detected_lang = 'hu'
                    
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
                    elif lang == 'hu':
                        detected_lang = 'hu'
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
