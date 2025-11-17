#!/bin/bash

# Скрипт для додавання GitHub topics/tags
# Використання: ./add_github_topics.sh [GITHUB_TOKEN]

REPO_OWNER="maciborka"
REPO_NAME="MTimer"

# Topics для проєкту
TOPICS=(
    "macos"
    "macos-app"
    "time-tracker"
    "time-tracking"
    "pyobjc"
    "appkit"
    "cocoa"
    "python"
    "sqlite"
    "desktop-app"
    "native-app"
    "productivity"
    "menu-bar-app"
    "py2app"
    "python-macos"
    "time-management"
    "project-management"
    "dark-mode"
    "localization"
    "universal-binary"
)

# Перевірка наявності GitHub token
if [ -z "$1" ]; then
    echo "❌ Потрібен GitHub Personal Access Token"
    echo ""
    echo "Використання:"
    echo "  ./add_github_topics.sh YOUR_GITHUB_TOKEN"
    echo ""
    echo "Як отримати токен:"
    echo "1. Перейдіть на https://github.com/settings/tokens"
    echo "2. Generate new token (classic)"
    echo "3. Виберіть scope: 'repo'"
    echo "4. Скопіюйте згенерований токен"
    echo ""
    echo "Або встановіть його як змінну середовища:"
    echo "  export GITHUB_TOKEN=your_token_here"
    echo "  ./add_github_topics.sh \$GITHUB_TOKEN"
    exit 1
fi

GITHUB_TOKEN="$1"

# Конвертуємо масив в JSON
TOPICS_JSON=$(printf '%s\n' "${TOPICS[@]}" | jq -R . | jq -s .)

echo "📝 Додаємо topics до репозиторію ${REPO_OWNER}/${REPO_NAME}..."
echo ""
echo "Topics:"
printf '%s\n' "${TOPICS[@]}" | sed 's/^/  - /'
echo ""

# Виконуємо API запит
RESPONSE=$(curl -s -X PUT \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  -H "Authorization: token ${GITHUB_TOKEN}" \
  -d "{\"names\": ${TOPICS_JSON}}" \
  "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/topics")

# Перевіряємо результат
if echo "$RESPONSE" | jq -e '.names' > /dev/null 2>&1; then
    echo "✅ Topics успішно додані!"
    echo ""
    echo "Встановлені topics:"
    echo "$RESPONSE" | jq -r '.names[]' | sed 's/^/  ✓ /'
    echo ""
    echo "🔗 Перегляньте на: https://github.com/${REPO_OWNER}/${REPO_NAME}"
else
    echo "❌ Помилка при додаванні topics:"
    echo "$RESPONSE" | jq .
    exit 1
fi
