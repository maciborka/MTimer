# GitHub Actions & Releases — Інструкція з налаштування

## 🚀 Автоматична збірка

### Що вже налаштовано

GitHub Actions workflow (`.github/workflows/build.yml`) автоматично:
- ✅ Збирає додаток при кожному push в `main`
- ✅ Створює DMG installer
- ✅ Публікує реліз при створенні тега `v*`
- ✅ Зберігає артефакти на 30 днів

### Як створити перший реліз

1. **Перевірте версію в `setup.py`:**
   ```python
   version='1.0.0',
   ```

2. **Закоммітьте всі зміни:**
   ```bash
   git add .
   git commit -m "Підготовка до релізу v1.0.0"
   git push
   ```

3. **Створіть та запуште тег:**
   ```bash
   git tag -a v1.0.0 -m "Перший публічний реліз

   Основний функціонал:
   - Нативний macOS додаток
   - Відстеження часу з проєктами
   - Багатомовна підтримка (UK/EN/RU)
   - Menu bar інтеграція
   - Dark mode support
   "
   
   git push origin v1.0.0
   ```

4. **Перевірте GitHub Actions:**
   - Перейдіть на https://github.com/maciborka/MTimer/actions
   - Дочекайтесь завершення збірки (~5-10 хв)
   - Перевірте створений реліз: https://github.com/maciborka/MTimer/releases

## 🏷️ GitHub Topics (Tags)

### Автоматичне додавання

```bash
# 1. Створіть GitHub Personal Access Token:
#    https://github.com/settings/tokens
#    Scope: repo

# 2. Запустіть скрипт:
./scripts/add_github_topics.sh YOUR_GITHUB_TOKEN
```

### Ручне додавання

1. Відкрийте https://github.com/maciborka/MTimer
2. Натисніть ⚙️ (біля "About")
3. Додайте topics через кому:
   ```
   macos, time-tracker, pyobjc, appkit, python, sqlite, desktop-app, 
   native-app, productivity, menu-bar-app, py2app, time-management
   ```

### Рекомендовані topics

**Основні:**
- `macos`, `macos-app`
- `time-tracker`, `time-tracking`, `time-management`
- `pyobjc`, `appkit`, `cocoa`
- `python`, `sqlite`

**Функціонал:**
- `desktop-app`, `native-app`
- `menu-bar-app`, `productivity`
- `project-management`
- `dark-mode`, `localization`

**Технічні:**
- `py2app`, `python-macos`
- `universal-binary`

## 📦 Структура релізу

Кожен реліз включає:
- **MTimer.dmg** — готовий інсталятор для користувачів
- **Артефакти збірки** — .app bundle для розробників
- **Release notes** — автоматично згенеровані з описом

## 🔄 Workflow оновлень

### Для patch версій (1.0.x)

```bash
# Виправлення помилок
git commit -m "Fix: опис виправлення"
git tag v1.0.1 -m "Patch: виправлення критичних помилок"
git push && git push --tags
```

### Для minor версій (1.x.0)

```bash
# Нові функції
git commit -m "Feature: опис нової функції"
git tag v1.1.0 -m "Minor: додано нові функції"
git push && git push --tags
```

### Для major версій (x.0.0)

```bash
# Breaking changes
git commit -m "Breaking: опис змін"
git tag v2.0.0 -m "Major: великі зміни в архітектурі"
git push && git push --tags
```

## 📊 Моніторинг

- **Actions:** https://github.com/maciborka/MTimer/actions
- **Releases:** https://github.com/maciborka/MTimer/releases
- **Insights:** https://github.com/maciborka/MTimer/pulse

## ⚠️ Важливо

1. **Перший реліз** може зайняти 10-15 хвилин (GitHub Actions встановлює macOS runner)
2. **DMG створення** вимагає `create-dmg` (встановлюється автоматично)
3. **Ad-hoc підпис** — користувачі побачать попередження при першому запуску
4. **Для production** — отримайте Apple Developer ID та налаштуйте notarization

## 🛠 Налаштування секретів (опціонально)

Для підпису Apple Developer ID:

1. Settings → Secrets and variables → Actions
2. Додайте секрети:
   - `APPLE_CERTIFICATE_BASE64` — сертифікат у base64
   - `APPLE_CERTIFICATE_PASSWORD` — пароль сертифіката
   - `APPLE_ID` — ваш Apple ID
   - `APPLE_ID_PASSWORD` — app-specific password
   - `APPLE_TEAM_ID` — Team ID

3. Оновіть workflow для підпису та нотаризації

---

**Готово!** Тепер при кожному тезі `v*` автоматично створюватиметься реліз з готовим DMG файлом.
