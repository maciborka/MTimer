# -*- coding: utf-8 -*-
"""
Модуль генерации PDF отчетов для TimeM
Использует стандартный диалог печати macOS для сохранения в PDF
"""

from datetime import datetime
from localization import t


def generate_pdf_report(sessions, projects_cache, period_name, project_name, pdf_path):
    """
    Генерирует PDF отчет из сессий используя стандартный диалог печати macOS

    Args:
        sessions: список сессий для включения в отчет
        projects_cache: кеш проектов с информацией о ставках
        period_name: название периода (например "СЕГОДНЯ" или "01.01.2024 - 31.01.2024")
        project_name: название проекта (или "Все проекты")
        pdf_path: путь для сохранения PDF файла (игнорируется - пользователь выбирает в диалоге)
    """

    # Импортируем необходимые классы внутри функции
    from Cocoa import (
        NSPrintOperation,
        NSPrintInfo,
        NSTextView,
        NSMakeRect,
        NSFont,
        NSAttributedString,
        NSTextContainer,
        NSLayoutManager,
        NSTextStorage,
        NSMakeSize,
    )

    # Конвертируем sessions в словари (на случай если это sqlite3.Row)
    sessions_list = []
    for session in sessions:
        # Проверяем, является ли это настоящим словарём или нужно конвертировать
        if isinstance(session, dict):
            sessions_list.append(session)
        else:
            # Конвертируем sqlite3.Row или любой dict-like объект в словарь
            sessions_list.append(dict(session))

    # Конвертируем projects_cache в словари (на случай если это sqlite3.Row)
    projects_list = []
    for project in projects_cache:
        if isinstance(project, dict):
            projects_list.append(project)
        else:
            projects_list.append(dict(project))

    # Группируем сессии по проектам
    from collections import defaultdict

    sessions_by_project = defaultdict(list)

    for session in sessions_list:
        project_id = session.get("project_id")
        sessions_by_project[project_id].append(session)

    # Генерируем текстовое представление отчёта
    text = generate_text_report(
        sessions_by_project, projects_list, period_name, project_name
    )

    # Создаём NSTextView для многостраничного вывода
    # Размеры A4: 595 x 842 points (при 72 dpi)
    page_width = 595
    page_height = 842

    # Создаём text view с начальным размером страницы
    text_view = NSTextView.alloc().initWithFrame_(
        NSMakeRect(0, 0, page_width, page_height)
    )
    text_view.setString_(text)
    text_view.setFont_(NSFont.fontWithName_size_("Monaco", 10))

    # Настраиваем текстовый контейнер для многостраничности
    text_view.setHorizontallyResizable_(False)
    text_view.setVerticallyResizable_(True)
    text_view.textContainer().setWidthTracksTextView_(True)
    # Убираем ограничение по высоте контейнера - позволяем расти
    text_view.textContainer().setHeightTracksTextView_(False)
    text_view.textContainer().setContainerSize_(NSMakeSize(page_width, 10000000))

    # Настраиваем печать
    print_info = NSPrintInfo.sharedPrintInfo().copy()
    print_info.setHorizontalPagination_(1)  # NSAutoPagination
    print_info.setVerticalPagination_(1)  # NSAutoPagination
    print_info.setTopMargin_(50)
    print_info.setBottomMargin_(50)
    print_info.setLeftMargin_(50)
    print_info.setRightMargin_(50)

    # Создаём print operation с диалогом
    print_op = NSPrintOperation.printOperationWithView_printInfo_(text_view, print_info)
    print_op.setShowsPrintPanel_(True)  # Показываем диалог печати
    print_op.setShowsProgressPanel_(True)

    # Запускаем print operation (откроет диалог печати)
    # Пользователь сможет выбрать "Save as PDF" в диалоге
    print_op.runOperation()


def generate_text_report(
    sessions_by_project, projects_cache, period_name, project_name
):
    """Генерирует текстовое представление отчёта"""

    total_duration = 0
    total_cost = 0.0

    # Заголовок
    lines = []
    lines.append("=" * 80)
    lines.append(t("report_title").center(80))
    lines.append("=" * 80)
    lines.append("")
    lines.append(f"{t('report_period')}: {period_name}")
    lines.append(f"{t('report_project')}: {project_name}")
    lines.append(f"Создан: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    lines.append("")
    lines.append("-" * 80)

    # Таблица с сессиями
    for project_id, sessions in sessions_by_project.items():
        # Находим проект
        project = None
        if project_id:
            project = next(
                (p for p in projects_cache if p["id"] == project_id),
                None,
            )

        # Название проекта
        if project:
            proj_name = project["name"]
            hourly_rate = project.get("hourly_rate", 0) or 0
        else:
            proj_name = t("no_name")
            hourly_rate = 0

        # Заголовок проекта
        lines.append("")
        proj_text = proj_name
        if hourly_rate > 0:
            proj_text += f" (${hourly_rate:.0f}/ч)"
        lines.append(proj_text)
        lines.append("-" * 80)

        # Заголовки колонок
        header = f"{'Дата':<12} {'Время':<8} {'Задача':<30} {'Длительность':<15} {'Стоимость':<10}"
        lines.append(header)
        lines.append("-" * 80)

        # Сессии проекта
        for session in sessions:
            start_time = datetime.fromisoformat(session["start_time"])
            date_str = start_time.strftime("%d.%m.%Y")
            time_str = start_time.strftime("%H:%M")

            duration = session.get("duration", 0) or 0
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            duration_str = f"{hours}ч {minutes:02d}м"

            # Стоимость
            if hourly_rate > 0:
                duration_hours = duration / 3600.0
                cost = duration_hours * hourly_rate
                cost_str = f"${cost:.2f}"
                total_cost += cost
            else:
                cost_str = "-"

            task_name = (
                session.get("task_name")
                or session.get("description")
                or t("no_description")
            )

            # Обрезаем длинные названия
            if len(task_name) > 28:
                task_name = task_name[:25] + "..."

            line = f"{date_str:<12} {time_str:<8} {task_name:<30} {duration_str:<15} {cost_str:<10}"
            lines.append(line)

            total_duration += duration

    # Итоги
    total_hours = total_duration // 3600
    total_minutes = (total_duration % 3600) // 60
    total_seconds = total_duration % 60

    lines.append("")
    lines.append("=" * 80)
    lines.append(t("report_total"))
    lines.append(
        f"{t('report_total_time')}: {total_hours}ч {total_minutes:02d}м {total_seconds:02d}с"
    )

    if total_cost > 0:
        lines.append(f"{t('report_total_cost')}: ${total_cost:.2f}")

    lines.append("=" * 80)

    return "\n".join(lines)
