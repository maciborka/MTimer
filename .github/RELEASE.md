# Релізи MTimer

## Як створити новий реліз

### Автоматичний процес (рекомендується)

1. **Оновіть версію в `setup.py`:**
   ```python
   version='1.0.0',  # Змініть на нову версію
   ```

2. **Закоммітьте зміни:**
   ```bash
   git add setup.py
   git commit -m "Bump version to 1.0.0"
   git push
   ```

3. **Створіть та запуште тег:**
   ```bash
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

4. **GitHub Actions автоматично:**
   - Зібере додаток
   - Створить DMG файл
   - Опублікує реліз з готовим бандлом

### Локальна збірка (для тестування)

```bash
# Встановити залежності
pip install -r requirements.txt

# Зібрати додаток
python setup.py py2app

# Створити DMG (опціонально)
hdiutil create -volname MTimer -srcfolder dist/MTimer.app -ov -format UDZO MTimer.dmg
```

## Структура версій

Використовуємо [Semantic Versioning](https://semver.org/):

- **MAJOR.MINOR.PATCH** (наприклад, 1.2.3)
- **MAJOR** — несумісні зміни API
- **MINOR** — нові функції (зворотна сумісність)
- **PATCH** — виправлення помилок

## Checklist перед релізом

- [ ] Оновлено версію в `setup.py`
- [ ] Протестовано на Intel та Apple Silicon (якщо можливо)
- [ ] Перевірено всі основні функції
- [ ] Оновлено CHANGELOG.md (якщо є)
- [ ] Створено git tag з описом змін
- [ ] Перевірено, що GitHub Actions відпрацював успішно

## Відмінності між релізами

### DMG vs .app

- **MTimer.dmg** — встановлювач для кінцевих користувачів (рекомендується)
- **MTimer.app** — сирий бандл для розробників

### Артефакти GitHub Actions

Кожна збірка зберігає артефакти на 30 днів для тестування.
