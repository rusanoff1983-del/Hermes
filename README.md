# Hermes Plugins & UI Extensions Catalog

Каталог плагинов и интерфейсных расширений для [Hermes Desktop](https://github.com/NousResearch/hermes-agent).

Каждый модуль изолирован в своей папке внутри `plugins/<имя-плагина>` со своей собственной инструкцией, файлами и скриптами установки.

---

## 🌟 Доступные плагины в каталоге

| Плагин | Описание | Инструкция и файлы |
| :--- | :--- | :--- |
| ☆ **`favorites-models`** | Компактная кнопка быстрого выбора избранных моделей в шапке чата | [👉 Перейти к плагину](plugins/favorites-models/README.md) |
| ☆ **`antigravity-oauth`** | Прямой Google Cloud Code / Antigravity OAuth провайдер (Gemini) без сторонних утилит | [👉 Перейти к плагину](plugins/antigravity-oauth/README.md) |

*(Каталог пополняется новыми плагинами)*

---

## 📁 Структура каталога

```text
Hermes/
├── plugins/
│   ├── favorites-models/       # ☆ Плагин «Избранные модели»
│   │   ├── plugin.js
│   │   └── README.md
│   │
│   └── antigravity-oauth/      # ☆ Плагин «Google Antigravity OAuth»
│       ├── plugin.yaml
│       ├── __init__.py
│       ├── direct.py
│       ├── wire.mjs
│       ├── package.json
│       ├── install.bat
│       ├── install.sh
│       └── README.md
│
├── interface/                  # Патчи и мосты для Desktop интерфейса
├── docs/                       # Скриншоты и общая документация
├── install.py                  # Установщик Desktop-мостов
└── README.md
```

---

## 🚀 Как установить плагин из каталога

1. Выберите нужный плагин в таблице выше и откройте его папку:
   - **[☆ Кнопка «Избранные модели»](plugins/favorites-models/README.md)** — быстрое переключение любимых моделей в шапке чата.
   - **[☆ Вход Google Antigravity OAuth](plugins/antigravity-oauth/README.md)** — прямое подключение моделей Gemini без сторонних CLI.

2. Внутри папки каждого плагина лежит **своя собственная инструкция** и отдельный скрипт установки `install.bat` в 1 клик.

---

## 🛡 Безопасность

- Репозиторий **не содержит** персональных токенов, ключей доступа или настроек пользователей.
- Все учетные данные шифруются локально на машине пользователя.

