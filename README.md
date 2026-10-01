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

## 🚀 Как установить нужный плагин

Перейдите в папку нужного плагина и следуйте его инструкции:

1. **Для кнопки «Избранные модели»:**
   Откройте [plugins/favorites-models/README.md](plugins/favorites-models/README.md)
   ```bash
   python install.py --install-deps
   ```

2. **Для авторизации «Antigravity Google OAuth»:**
   Откройте [plugins/antigravity-oauth/README.md](plugins/antigravity-oauth/README.md)
   ```bash
   # Запустите install.bat в папке plugins/antigravity-oauth или:
   hermes auth add antigravity-direct
   ```

---

## 🛡 Безопасность

- Репозиторий **не содержит** персональных токенов, ключей доступа или настроек пользователей.
- Все учетные данные шифруются локально на машине пользователя.

