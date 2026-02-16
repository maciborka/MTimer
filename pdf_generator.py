# -*- coding: utf-8 -*-
"""
Модуль генерации PDF отчетов для TimeM
Использует WebKit для конвертации HTML -> PDF
"""

from Cocoa import (
    NSPrintOperation,
    NSPrintInfo,
    NSURL,
    NSMutableDictionary,
)
from WebKit import WebView
from Foundation import NSMakeRect
from datetime import datetime
from localization import t


def generate_pdf_report(sessions, projects_cache, period_name, project_name, pdf_path):
    """
    Генерирует PDF отчет из сессий

    Args:
        sessions: список сессий для включения в отчет
        projects_cache: кеш проектов с информацией о ставках
        period_name: название периода (например "СЕГОДНЯ" или "01.01.2024 - 31.01.2024")
        project_name: название проекта (или "Все проекты")
        pdf_path: путь для сохранения PDF файла
    """

    # Группируем сессии по проектам
    from collections import defaultdict

    sessions_by_project = defaultdict(list)

    for session in sessions:
        project_id = session.get("project_id")
        sessions_by_project[project_id].append(session)

    # Генерируем HTML
    html = generate_html_report(
        sessions_by_project, projects_cache, period_name, project_name
    )

    # Создаём WebView для рендеринга HTML
    web_view = WebView.alloc().initWithFrame_(NSMakeRect(0, 0, 595, 842))  # A4 size
    web_view.mainFrame().loadHTMLString_baseURL_(html, None)

    # Ждём загрузки (для простоты используем синхронный подход)
    # В продакшене лучше использовать асинхронную загрузку
    import time

    time.sleep(0.5)  # Даём время на рендеринг

    # Настраиваем печать в PDF
    print_info = NSPrintInfo.sharedPrintInfo().copy()
    print_info.setHorizontalPagination_(1)
    print_info.setVerticalPagination_(1)
    print_info.setVerticallyCentered_(False)
    print_info.setTopMargin_(30)
    print_info.setBottomMargin_(30)
    print_info.setLeftMargin_(30)
    print_info.setRightMargin_(30)

    # Создаём print operation
    print_op = NSPrintOperation.printOperationWithView_printInfo_(
        web_view.mainFrame().frameView().documentView(), print_info
    )
    print_op.setShowsPrintPanel_(False)
    print_op.setShowsProgressPanel_(False)

    # Указываем путь к PDF файлу
    dict_obj = NSMutableDictionary.dictionaryWithDictionary_(print_info.dictionary())
    dict_obj.setObject_forKey_(pdf_path, "NSPrintSavePath")
    print_info.setDictionary_(dict_obj)
    print_info.setJobDisposition_("NSPrintSaveJob")

    # Запускаем print operation
    print_op.runOperation()


def generate_html_report(
    sessions_by_project, projects_cache, period_name, project_name
):
    """Генерирует HTML для отчёта"""

    total_duration = 0
    total_cost = 0.0

    # Начало HTML
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                margin: 20px;
                font-size: 11pt;
            }}
            h1 {{
                text-align: center;
                color: #333;
                font-size: 20pt;
                margin-bottom: 10px;
            }}
            .info {{
                color: #666;
                margin-bottom: 20px;
                font-size: 10pt;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 10px;
            }}
            th {{
                background-color: #3366CC;
                color: white;
                padding: 8px;
                text-align: left;
                font-size: 9pt;
            }}
            td {{
                padding: 6px;
                border-bottom: 1px solid #ddd;
                font-size: 9pt;
            }}
            .project-header {{
                background-color: #f0f0f0;
                font-weight: bold;
                color: #3366CC;
                padding: 8px;
                margin-top: 15px;
                font-size: 10pt;
            }}
            .total {{
                margin-top: 20px;
                padding-top: 10px;
                border-top: 2px solid #333;
                font-weight: bold;
                font-size: 11pt;
            }}
            .separator {{
                border-top: 1px solid #ccc;
                margin: 15px 0;
            }}
        </style>
    </head>
    <body>
        <h1>{t("report_title")}</h1>
        <div class="info">
            <div><strong>{t("report_period")}</strong> {period_name}</div>
            <div><strong>{t("report_project")}</strong> {project_name}</div>
            <div><strong>Создан:</strong> {datetime.now().strftime("%d.%m.%Y %H:%M")}</div>
        </div>
        <div class="separator"></div>
    """

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
        proj_text = proj_name
        if hourly_rate > 0:
            proj_text += f" (${hourly_rate:.0f}/ч)"

        html += f'<div class="project-header">{proj_text}</div>\n'
        html += "<table>\n"
        html += "<tr>\n"
        html += f"<th>{t('report_date')}</th>\n"
        html += f"<th>{t('report_time')}</th>\n"
        html += f"<th>{t('report_task')}</th>\n"
        html += f"<th>{t('report_duration')}</th>\n"
        html += f"<th>{t('report_cost')}</th>\n"
        html += "</tr>\n"

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

            html += "<tr>\n"
            html += f"<td>{date_str}</td>\n"
            html += f"<td>{time_str}</td>\n"
            html += f"<td>{task_name}</td>\n"
            html += f"<td>{duration_str}</td>\n"
            html += f"<td>{cost_str}</td>\n"
            html += "</tr>\n"

            total_duration += duration

        html += "</table>\n"

    # Итоги
    total_hours = total_duration // 3600
    total_minutes = (total_duration % 3600) // 60
    total_seconds = total_duration % 60

    html += '<div class="total">\n'
    html += f"<div>{t('report_total')}</div>\n"
    html += f"<div>{t('report_total_time')} {total_hours}ч {total_minutes:02d}м {total_seconds:02d}с</div>\n"

    if total_cost > 0:
        html += f"<div>{t('report_total_cost')} ${total_cost:.2f}</div>\n"

    html += "</div>\n"
    html += "</body>\n</html>"

    return html
